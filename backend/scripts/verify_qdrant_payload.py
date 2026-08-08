import asyncio
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.qdrant import qdrant_client

async def verify():
    print("Fetching one candidate from Qdrant candidates collection...")
    result = await qdrant_client.scroll(
        collection_name="candidates",
        limit=1,
        with_payload=True
    )
    points = result[0]
    if not points:
        print("No points found in Qdrant candidates collection.")
        return
        
    point = points[0]
    print("\n=== Qdrant Payload Verification ===")
    print(f"Point ID: {point.id}")
    print(f"Payload: {json.dumps(point.payload, indent=2)}")
    print("===================================\n")

if __name__ == "__main__":
    asyncio.run(verify())
