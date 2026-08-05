"""Minimal diagnostic script to verify aiosqlite + SQLAlchemy works."""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    e = create_async_engine("sqlite+aiosqlite:///test_diag.db", echo=True)
    async with e.begin() as conn:
        result = await conn.execute(text("SELECT 1"))
        print("Result:", result.scalar())
    print("OK - aiosqlite works")
    await e.dispose()

asyncio.run(main())
