import asyncio
import os
import sys

# Add the parent directory to sys.path to allow imports from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.qdrant import qdrant_client

async def check():
    print("Fetching points from Qdrant...")
    result, next_page_offset = await qdrant_client.scroll(
        collection_name="candidates",
        limit=1,
        with_payload=True,
        with_vectors=False
    )
    
    if result:
        print("Successfully fetched point. Payload:")
        import json
        print(json.dumps(result[0].payload, indent=2))
    else:
        print("No points found in Qdrant candidates collection.")

if __name__ == "__main__":
    asyncio.run(check())
