import asyncio
from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.models.recruitment import Job, JobStatus
from sqlalchemy import select
import json

async def inject_data():
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, poolclass=NullPool)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    # Generic JD data
    generic_responsibilities = """- Design, develop, and maintain high-quality software solutions.
- Collaborate with cross-functional teams to define, design, and ship new features.
- Ensure the best possible performance, quality, and responsiveness of applications.
- Identify bottlenecks and bugs, and devise solutions to mitigate and address these issues.
- Help maintain code quality, organization, and automatization."""

    generic_expectations = """- Strong problem-solving skills and ability to work independently.
- Excellent communication and teamwork abilities.
- A passion for learning new technologies and keeping up with industry trends.
- Experience with Agile/Scrum development methodologies."""

    generic_company = """We are a fast-growing tech company dedicated to building innovative solutions that make a real impact. We value creativity, collaboration, and continuous improvement. Join us and be part of a team that is changing the industry!"""

    generic_benefits = """- Competitive salary and equity packages.
- Comprehensive health, dental, and vision insurance.
- Flexible working hours and remote work options.
- Generous PTO and paid holidays.
- Professional development and learning stipends."""

    async with async_session() as session:
        result = await session.execute(select(Job).where(Job.status == JobStatus.OPEN))
        jobs = result.scalars().all()
        
        count = 0
        for job in jobs:
            # Inject if null or empty
            if not job.key_responsibilities:
                job.key_responsibilities = generic_responsibilities
                count += 1
            if not job.expectations:
                job.expectations = generic_expectations
            if not job.company_description:
                job.company_description = generic_company
            if not job.benefits:
                job.benefits = generic_benefits
                
        if count > 0:
            await session.commit()
            print(f"Successfully injected JD data into {count} jobs.")
        else:
            print("No jobs required JD data injection.")

if __name__ == "__main__":
    asyncio.run(inject_data())
