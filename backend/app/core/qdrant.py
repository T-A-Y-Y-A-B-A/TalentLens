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
    collections = await client.get_collections()
    collection_names = [c.name for c in collections.collections]
    
    if "candidates" not in collection_names:
        # Using BGE small dimension which is 384 for dense
        await client.create_collection(
            collection_name="candidates",
            vectors_config={"dense": VectorParams(size=384, distance=Distance.COSINE)},
            sparse_vectors_config={"sparse": SparseVectorParams()}
        )
        await client.create_payload_index(
            collection_name="candidates",
            field_name="org_ids",
            field_schema=PayloadSchemaType.KEYWORD
        )
        
    if "jobs" not in collection_names:
        await client.create_collection(
            collection_name="jobs",
            vectors_config={"dense": VectorParams(size=384, distance=Distance.COSINE)},
            sparse_vectors_config={"sparse": SparseVectorParams()}
        )

