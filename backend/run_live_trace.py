import asyncio
import time
import uuid
import httpx
from datetime import timedelta
from app.core.database import AsyncSessionLocal
from app.models.identity import User
from app.core.security import create_access_token
from app.core.config import settings
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        # Find Org A user (DigitalSofts)
        res = await db.execute(select(User).where(User.email == 'hr@digitalsofts.com').limit(1))
        org_a_user = res.scalars().first()
        
        # Find Org B user (ABC-Software)
        res_b = await db.execute(select(User).where(User.email == 'hr@abc-software.com').limit(1))
        org_b_user = res_b.scalars().first()
        
        if not org_a_user or not org_b_user:
            print("Users not found")
            return

        token_a = create_access_token(subject=str(org_a_user.id), expires_delta=timedelta(minutes=15))
        token_b = create_access_token(subject=str(org_b_user.id), expires_delta=timedelta(minutes=15))
        
        job_id = "1e4630c2-09c6-4aea-a9f6-f8cb00f7b196"
        candidate_id = "7bdfe08b-55e1-4caf-8bee-c7d9757c4bf4"
        url = f"http://localhost:8000/api/v1/jobs/{job_id}/matches/{candidate_id}/reason"
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            print("=== TEST 1: First Call (Expected Latency) ===")
            start = time.time()
            r1 = await client.post(url, headers={"Authorization": f"Bearer {token_a}"})
            print(f"Status: {r1.status_code}")
            print(f"Latency: {time.time() - start:.2f} seconds")
            print("Response:", r1.json())
            
            print("\n=== TEST 2: Second Call (Expected Cache Hit) ===")
            start = time.time()
            r2 = await client.post(url, headers={"Authorization": f"Bearer {token_a}"})
            print(f"Status: {r2.status_code}")
            print(f"Latency: {time.time() - start:.2f} seconds")
            print("Response:", r2.json())
            
            print("\n=== TEST 3: Cross-Tenant Call (Org B user) ===")
            start = time.time()
            r3 = await client.post(url, headers={"Authorization": f"Bearer {token_b}"})
            print(f"Status: {r3.status_code}")
            print(f"Latency: {time.time() - start:.2f} seconds")
            print("Response:", r3.text)

if __name__ == "__main__":
    asyncio.run(main())
