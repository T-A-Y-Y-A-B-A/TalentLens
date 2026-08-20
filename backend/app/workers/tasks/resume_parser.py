import asyncio
import os
import structlog
import uuid
from datetime import datetime, timezone

from app.workers.celery_app import celery_app
import asyncio
from app.core.database import AsyncSessionLocal, engine
from app.core.config import settings
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
    
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy.pool import NullPool
    engine_local = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, poolclass=NullPool)
    async_session = async_sessionmaker(engine_local, expire_on_commit=False)
    
    try:
        async with async_session() as db:
            from sqlalchemy import select
            result = await db.execute(select(Resume).where(Resume.id == resume_id))
        resume = result.scalars().first()
        
        if not resume:
            logger.error("resume_not_found", resume_id=resume_id)
            return
            
        resume.parse_status = ParseStatus.PROCESSING
        await db.commit()
        
        try:
            # Download from MinIO to memory buffer
            import io
            file_buffer = io.BytesIO()
            
            if resume.file_url.startswith("s3://"):
                from app.core.storage import get_s3_client
                bucket, key = resume.file_url.replace("s3://", "").split("/", 1)
                s3 = get_s3_client()
                obj = s3.get_object(Bucket=bucket, Key=key)
                file_buffer = io.BytesIO(obj['Body'].read())
            else:
                # Local fallback (for old testing data)
                with open(resume.file_url, "rb") as f:
                    file_buffer = io.BytesIO(f.read())
            
            extracted_text = ""
            try:
                from docling.document_converter import DocumentConverter
                converter = DocumentConverter()
                # Depending on docling version, this might not support BytesIO natively,
                # but we try it. If it fails, we fall back to pypdf.
                doc = converter.convert(file_buffer)
                extracted_text = doc.document.export_to_markdown()
            except Exception as e:
                logger.warning("docling_failed_falling_back_to_pypdf", error=str(e))
                import pypdf
                file_buffer.seek(0)
                pdf = pypdf.PdfReader(file_buffer)
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
                model=settings.GROQ_MODEL_EXTRACT
            )
            
            # 3. Save structured data to Postgres
            parsed_data = ResumeParsedData(
                resume_id=resume.id,
                skills=structured_data.skills,
                experience=[e.model_dump() for e in structured_data.experience],
                education=[e.model_dump() for e in structured_data.education],
                certifications=structured_data.certifications,
                projects=[p.model_dump() for p in structured_data.projects]
            )
            db.add(parsed_data)
            
            # 4. Generate Embeddings & Upsert to Qdrant
            from app.models.candidate import Candidate
            cand_result = await db.execute(select(Candidate).where(Candidate.id == resume.candidate_id))
            candidate = cand_result.scalars().first()
            
            from app.services.matching import compute_candidate_embeddings
            await compute_candidate_embeddings(db, candidate, parsed_data)
            
            # 5. Mark as DONE
            resume.parse_status = ParseStatus.DONE
            await db.commit()
            logger.info("parse_resume_success", resume_id=resume_id)
            
            from app.services.candidate_visibility import sync_candidate_qdrant_orgs
            await sync_candidate_qdrant_orgs(db, resume.candidate_id)

            from app.workers.tasks.keyword_matching import match_candidate_to_all_jobs
            match_candidate_to_all_jobs.delay(str(resume.candidate_id))
            
        except Exception as e:
            logger.error("parse_resume_failed", resume_id=resume_id, error=str(e))
            resume.parse_status = ParseStatus.FAILED
            await db.commit()
            raise
    finally:
        await engine_local.dispose()

@celery_app.task(name="tasks.parse_resume")
def parse_resume(resume_id: str):
    """
    Celery task entrypoint. Runs the async parse workflow in a new event loop.
    """
    async def wrapper():
        await async_parse_resume(resume_id)
            
    asyncio.run(wrapper())
