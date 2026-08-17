import asyncio
from sqlalchemy import select, update
from app.core.database import AsyncSessionLocal
from app.models.recruitment import Job

async def seed_jobs():
    async with AsyncSessionLocal() as session:
        jobs = (await session.execute(select(Job))).scalars().all()
        
        for job in jobs:
            skills = ["Python", "FastAPI", "SQL"] # fallback
            
            if "Software Engineer" in job.title:
                if "ABC" in job.title:
                    skills = ["Java", "Spring Boot", "AWS", "Microservices", "Docker"]
                elif "XYZ" in job.title:
                    skills = ["C#", ".NET Core", "Azure", "SQL Server", "TypeScript"]
                else:
                    skills = ["Python", "Django", "PostgreSQL", "React", "GraphQL"]
            elif "Test" in job.title:
                skills = ["Selenium", "PyTest", "Cypress", "QA", "CI/CD"]
            elif "Org 1" in job.title:
                skills = ["JavaScript", "Node.js", "Express", "MongoDB", "AWS"]
            elif "Org 2" in job.title:
                skills = ["Go", "Kubernetes", "gRPC", "PostgreSQL", "Kafka"]
                
            reqs = dict(job.requirements) if job.requirements else {}
            reqs["required_skills"] = skills
            
            await session.execute(
                update(Job)
                .where(Job.id == job.id)
                .values(requirements=reqs)
            )
            
        await session.commit()
        print(f"Seeded {len(jobs)} jobs with realistic requirements.")

if __name__ == "__main__":
    asyncio.run(seed_jobs())
