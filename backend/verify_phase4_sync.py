import asyncio
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings
from app.models.candidate import Candidate, Resume, ResumeParsedData
from app.models.recruitment import Job, JobStatus
from app.services.matching import compute_msgc_score

async def test_msgc():
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        # Get first open job
        job_res = await session.execute(select(Job).where(Job.status == JobStatus.OPEN).limit(1))
        job = job_res.scalars().first()
        if not job:
            print("No open jobs found")
            return
            
        # Get first candidate
        cand_res = await session.execute(
            select(Candidate, ResumeParsedData)
            .join(Resume, Resume.candidate_id == Candidate.id)
            .join(ResumeParsedData, ResumeParsedData.resume_id == Resume.id)
            .limit(1)
        )
        row = cand_res.first()
        if not row:
            print("No candidates found")
            return
            
        candidate, resume_data = row
        
        # --- NEGATIVE TEST CASE ---
        print("\n=== NEGATIVE TEST CASE (Mismatch) ===")
        job.title = "Senior Java Engineer"
        job.requirements = {'required_skills': ['Java', 'Spring Boot', 'AWS', 'Microservices', 'Docker']}
        job.key_responsibilities = ["Develop Java Spring Boot microservices", "Deploy containerized apps to AWS"]
        resume_data.skills = ['Python', 'React', 'Node.js', 'PyTorch', 'TensorFlow', 'MongoDB']
        resume_data.experience = [
            {"title": "Machine Learning Engineer", "description": ["Built Python ML models using PyTorch", "Developed React frontends"]}
        ]
        
        result = await compute_msgc_score(session, job, candidate, resume_data)
        
        print("\n--- MSGC Result ---")
        for k, v in result.items():
            print(f"{k}: {v}")
            
        # --- POSITIVE TEST CASE ---
        print("\n=== POSITIVE TEST CASE (Match) ===")
        job.title = "Senior Java Engineer"
        job.requirements = {'required_skills': ['Java', 'Spring Boot', 'AWS', 'Microservices', 'Docker']}
        job.key_responsibilities = ["Develop Java Spring Boot microservices", "Deploy containerized apps to AWS"]
        resume_data.skills = ['Java', 'Spring Boot', 'Amazon Web Services (AWS)', 'Docker', 'Kubernetes', 'Microservices architecture']
        resume_data.experience = [
            {"title": "Java Backend Developer", "description": ["Designed and implemented scalable microservices using Java and Spring Boot.", "Managed container orchestration with Docker on AWS ECS."]}
        ]
        
        result_pos = await compute_msgc_score(session, job, candidate, resume_data)
        
        print("\n--- MSGC Result ---")
        for k, v in result_pos.items():
            print(f"{k}: {v}")
            
        # --- INCOMPLETE JD TEST CASE (Mismatch) ---
        print("\n=== INCOMPLETE JD TEST CASE (Mismatch Candidate) ===")
        job.key_responsibilities = None
        job.expectations = None
        
        resume_data.skills = ['Python', 'React', 'Node.js', 'PyTorch', 'TensorFlow', 'MongoDB']
        resume_data.experience = [
            {"title": "Machine Learning Engineer", "description": ["Built Python ML models using PyTorch", "Developed React frontends"]}
        ]
        
        result_inc_neg = await compute_msgc_score(session, job, candidate, resume_data)
        
        print("\n--- MSGC Result ---")
        for k, v in result_inc_neg.items():
            print(f"{k}: {v}")
            
        # --- INCOMPLETE JD TEST CASE (Match) ---
        print("\n=== INCOMPLETE JD TEST CASE (Match Candidate) ===")
        resume_data.skills = ['Java', 'Spring Boot', 'Amazon Web Services (AWS)', 'Docker', 'Kubernetes', 'Microservices architecture']
        resume_data.experience = [
            {"title": "Java Backend Developer", "description": ["Designed and implemented scalable microservices using Java and Spring Boot.", "Managed container orchestration with Docker on AWS ECS."]}
        ]
        
        result_inc_pos = await compute_msgc_score(session, job, candidate, resume_data)
        
        print("\n--- MSGC Result ---")
        for k, v in result_inc_pos.items():
            print(f"{k}: {v}")
            
        # --- REAL INCOMPLETE JD TEST CASE (DB Data) ---
        stmt = select(Job).filter(Job.key_responsibilities.is_(None)).limit(1)
        res = await session.execute(stmt)
        real_inc_job = res.scalar_one_or_none()
        
        if real_inc_job:
            print(f"\n=== REAL INCOMPLETE JD TEST CASE (Job: {real_inc_job.title}) ===")
            print(f"Has key_responsibilities: {real_inc_job.key_responsibilities is not None}")
            
            # Mismatch Candidate
            print("\n--- Mismatch Candidate ---")
            resume_data.skills = ['Python', 'Django', 'Machine Learning']
            resume_data.experience = [{"title": "Data Scientist", "description": ["Analyzed data"]}]
            
            res_real_neg = await compute_msgc_score(session, real_inc_job, candidate, resume_data)
            print("\n--- MSGC Result ---")
            for k, v in res_real_neg.items():
                print(f"{k}: {v}")
                
            # Match Candidate
            print("\n--- Match Candidate ---")
            req_skills = real_inc_job.requirements.get('required_skills', []) if isinstance(real_inc_job.requirements, dict) else getattr(real_inc_job.requirements, 'required_skills', [])
            resume_data.skills = req_skills
            resume_data.experience = [{"title": real_inc_job.title, "description": ["Did exactly what was asked"]}]
            
            res_real_pos = await compute_msgc_score(session, real_inc_job, candidate, resume_data)
            print("\n--- MSGC Result ---")
            for k, v in res_real_pos.items():
                print(f"{k}: {v}")
        else:
            print("\nNo incomplete job found in DB to test.")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_msgc())
