import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings

async def main():
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        for table in ["job_matches", "job_embeddings"]:
            print(f"\n\\d {table}")
            print(f"{'Column':<30} | {'Type':<20} | {'Nullable'}")
            print("-" * 65)
            
            result = await session.execute(text(
                f"SELECT column_name, data_type, is_nullable "
                f"FROM information_schema.columns "
                f"WHERE table_name = '{table}';"
            ))
            for row in result.fetchall():
                print(f"{row[0]:<30} | {row[1]:<20} | {row[2]}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
