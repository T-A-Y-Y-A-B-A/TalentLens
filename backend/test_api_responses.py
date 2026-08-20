import asyncio
import httpx
import json

async def test_api():
    print(f"\n--- Testing /api/v1/jobs/board ---")
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8001") as client:
        try:
            response = await client.get("/api/v1/jobs/board")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("jobs"):
                    first_job = data["jobs"][0]
                    print("First JobBoardCard Schema:")
                    print(json.dumps(first_job, indent=2))
                    
                    # Assertions
                    assert "composite_score" in first_job, "composite_score is missing!"
                    assert "flags" in first_job, "flags is missing!"
                    assert "match_pct" not in first_job, "match_pct should be removed!"
                    print("\nAll assertions passed!")
                else:
                    print("No jobs found on board.")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_api())

