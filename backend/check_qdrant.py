import asyncio
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qdrant_models
import sys

async def check():
    client = AsyncQdrantClient(host="qdrant", port=6333)
    candidate_id = "002b4736-fec2-4ea8-8060-75f36077fe31"
    
    # We filter by candidate_id in the payload
    filter = qdrant_models.Filter(
        must=[
            qdrant_models.FieldCondition(
                key="candidate_id",
                match=qdrant_models.MatchValue(value=candidate_id)
            )
        ]
    )
    
    records = await client.scroll(
        collection_name="candidates",
        scroll_filter=filter,
        with_payload=True,
        with_vectors=False,
        limit=5
    )
    
    points, _ = records
    
    if len(points) == 0:
        print(f"Candidate {candidate_id} NOT FOUND in Qdrant.")
    else:
        print(f"Candidate {candidate_id} FOUND in Qdrant!")
        for p in points:
            print(f"Point ID: {p.id}")
            print(f"Payload: {p.payload}")
            
if __name__ == "__main__":
    asyncio.run(check())
