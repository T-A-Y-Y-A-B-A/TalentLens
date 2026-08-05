import asyncio
import os
import structlog
import uuid
from datetime import datetime, timezone

from app.workers.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.models.candidate import Resume, ParseStatus, ResumeParsedData, CandidateEmbedding
from app.ai.llm import call_llm
from app.ai.prompts.resume_extraction import RESUME_EXTRACTION_PROMPT
from app.schemas.candidate import ResumeExtraction
from app.ai.embeddings import embed_text, get_embedding_model, EMBEDDING_MODEL_NAME
from app.core.qdrant import qdrant_client
from qdrant_client.models import PointStruct

logger = structlog.get_logger()

async def async_parse_resume(resume_id: str):
    logger.info("start_parse_resume", resume_id=resume_id)
    
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        result = await db.execute(select(Resume).where(Resume.id == resume_id))
        resume = result.scalars().first()
        
        if not resume:
            logger.error("resume_not_found", resume_id=resume_id)
            return
            
        resume.parse_status = ParseStatus.PROCESSING
        await db.commit()
        
        try:
            # 1. Extract text from PDF
            file_path = resume.file_url
            if file_path.startswith("http"):
                # Real implementation would download from MinIO here
                pass
            
            # For local uploads, we just read the file
            # In production this will use Docling.
            extracted_text = ""
            try:
                from docling.document_converter import DocumentConverter
                converter = DocumentConverter()
                doc = converter.convert(file_path)
                extracted_text = doc.document.export_to_markdown()
            except ImportError:
                # Fallback / Mock for tests running without docling
                logger.warning("docling_not_available", fallback="pypdf")
                import pypdf
                with open(file_path, "rb") as f:
                    pdf = pypdf.PdfReader(f)
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            extracted_text += text + "\n"
                            
            if not extracted_text.strip():
                raise Exception("Empty PDF or failed to extract text")
                
            resume.raw_text = extracted_text
            
            # 2. Extract structured data via LLM
            prompt = RESUME_EXTRACTION_PROMPT.format(text=extracted_text)
            structured_data = await call_llm(
                prompt=prompt,
                response_model=ResumeExtraction,
                model="claude-3-5-sonnet-20240620"
            )
            
            # 3. Save structured data to Postgres
            parsed_data = ResumeParsedData(
                resume_id=resume.id,
                skills=structured_data.skills,
                experience=[e.model_dump() for e in structured_data.experience],
                education=[e.model_dump() for e in structured_data.education],
                certifications=structured_data.certifications,
                projects=structured_data.projects
            )
            db.add(parsed_data)
            
            # 4. Generate Embeddings & Upsert to Qdrant
            # We embed the whole extracted text or structured summary
            # For simplicity, embed a concatenated summary of the structured data
            text_to_embed = f"Skills: {', '.join(structured_data.skills)}\n"
            for exp in structured_data.experience:
                text_to_embed += f"Experience: {exp.title} at {exp.company}\n"
            
            # Embed the text
            vector = embed_text(text_to_embed)
            
            # Save embedding metadata
            point_id = str(uuid.uuid4())
            emb_record = CandidateEmbedding(
                candidate_id=resume.candidate_id,
                qdrant_point_id=point_id,
                model_version=EMBEDDING_MODEL_NAME
            )
            # Use merge to handle potential upserts if candidate already has embedding
            await db.merge(emb_record)
            
            # Upload to Qdrant
            # Get candidate's org_id
            from app.models.candidate import Candidate
            cand_result = await db.execute(select(Candidate).where(Candidate.id == resume.candidate_id))
            candidate = cand_result.scalars().first()
            
            await qdrant_client.upsert(
                collection_name="candidates",
                points=[
                    PointStruct(
                        id=point_id,
                        vector=vector,
                        payload={
                            "candidate_id": str(candidate.id),
                            "org_id": str(candidate.org_id),
                            "skills": structured_data.skills
                        }
                    )
                ]
            )
            
            # 5. Mark as DONE
            resume.parse_status = ParseStatus.DONE
            await db.commit()
            logger.info("parse_resume_success", resume_id=resume_id)
            
        except Exception as e:
            logger.error("parse_resume_failed", resume_id=resume_id, error=str(e))
            resume.parse_status = ParseStatus.FAILED
            await db.commit()

@celery_app.task(name="tasks.parse_resume")
def parse_resume(resume_id: str):
    """
    Celery task entrypoint. Runs the async parse workflow in a new event loop.
    """
    asyncio.run(async_parse_resume(resume_id))
