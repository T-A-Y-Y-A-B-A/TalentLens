import asyncio
from app.core.database import AsyncSessionLocal
from app.models.candidate import Candidate, Resume, ResumeParsedData
from app.models.ai import AIMatchResult
from sqlalchemy import select
from sqlalchemy.orm import joinedload
import json

async def check_db():
    async with AsyncSessionLocal() as db:
        print("=== CANDIDATES & RESUMES ===")
        # Get candidates with resumes
        result = await db.execute(select(Candidate).order_by(Candidate.created_at.desc()).limit(5))
        candidates = result.scalars().all()
        
        if not candidates:
            print("No candidates found in the database.")
            
        for c in candidates:
            print(f"\nCandidate: {c.name} ({c.email})")
            
            resumes = await db.execute(select(Resume).where(Resume.candidate_id == c.id))
            for r in resumes.scalars().all():
                print(f"  -> Resume ID: {r.id}")
                print(f"     Status: {r.parse_status}")
                print(f"     Uploaded: {r.created_at}")
                
                parsed = await db.execute(select(ResumeParsedData).where(ResumeParsedData.resume_id == r.id))
                parsed_data = parsed.scalars().first()
                if parsed_data:
                    print(f"     [Parsed Data exists for this resume]")
                    print(f"     Skills Extracted: {', '.join(parsed_data.skills[:5])}...")
                else:
                    print("     [No parsed data yet]")
                    
            matches = await db.execute(select(AIMatchResult).where(AIMatchResult.candidate_id == c.id))
            for m in matches.scalars().all():
                print(f"  -> AI Match for Job {m.job_id}:")
                print(f"     Match: {m.match_pct}% (ATS: {m.ats_score}%)")
                print(f"     Strengths: {m.strengths[:2]}")
                print(f"     Missing: {m.missing_skills[:2]}")

if __name__ == "__main__":
    asyncio.run(check_db())
