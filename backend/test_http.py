import sys
import os
sys.path.insert(0, os.getcwd())

import asyncio
import httpx
from app.core.security import create_access_token

async def main():
    cand_id = "cbdfe29c-4ef0-429c-82fc-3a7490edc09b"
    token = create_access_token(str(cand_id), additional_claims={"role": "candidate"})
    
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000", timeout=30.0) as client:
        try:
            resp = await client.get(
                "/api/v1/candidate-portal/jobs",
                headers={"Authorization": f"Bearer {token}"}
            )
            print(f"Status Code: {resp.status_code}")
            print(f"Response: {resp.text[:500]}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
