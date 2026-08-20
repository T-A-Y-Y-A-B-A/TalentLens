from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, SparseVectorParams, PayloadSchemaType
from app.core.config import settings

qdrant_client = AsyncQdrantClient(
    url=settings.QDRANT_URL, 
    api_key=settings.QDRANT_API_KEY,
    timeout=60.0
)

async def init_qdrant():
    client = qdrant_client
    
    try:
        await client.create_collection(
            collection_name="candidates",
            vectors_config={"dense": VectorParams(size=384, distance=Distance.COSINE)},
        )
        await client.create_payload_index(
            collection_name="candidates",
            field_name="org_ids",
            field_schema=PayloadSchemaType.KEYWORD
        )
    except Exception as e:
        if "already exists" not in str(e):
            raise
        
    try:
        await client.create_collection(
            collection_name="jobs",
            vectors_config={"dense": VectorParams(size=384, distance=Distance.COSINE)},
        )
        await client.create_payload_index(
            collection_name="jobs",
            field_name="org_id",
            field_schema=PayloadSchemaType.KEYWORD
        )
    except Exception as e:
        if "already exists" not in str(e):
            raise
