import asyncio
from app.core.database import engine
from app.models.base import Base
from app.models.candidate import Candidate, Resume, ResumeParsedData, CandidateEmbedding
from app.models.application import Application, ApplicationStageHistory

async def main():
    async with engine.begin() as conn:
        print("Dropping tables...")
        # Since sqlite handles CASCADE poorly without PRAGMA foreign_keys=OFF, we might need to drop all
        # To be safe and just do what the user asked, we'll drop all tables and recreate them.
        from sqlalchemy import text
        await conn.execute(text("DROP TABLE IF EXISTS candidate_embeddings CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS resume_parsed_data CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS resumes CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS application_stage_history CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS applications CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS candidates CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS parsestatus CASCADE"))
        print("Creating tables...")
        await conn.run_sync(Candidate.__table__.create)
        await conn.run_sync(Application.__table__.create)
        await conn.run_sync(ApplicationStageHistory.__table__.create)
        await conn.run_sync(Resume.__table__.create)
        await conn.run_sync(ResumeParsedData.__table__.create)
        await conn.run_sync(CandidateEmbedding.__table__.create)
        await conn.run_sync(Base.metadata.create_all)
        print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
