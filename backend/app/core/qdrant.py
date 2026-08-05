from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams
from app.core.config import settings

qdrant_client = AsyncQdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)

async def init_qdrant():
    collections = await qdrant_client.get_collections()
    collection_names = [c.name for c in collections.collections]
    
    if "candidates" not in collection_names:
        # Using BGE small dimension which is 384
        await qdrant_client.create_collection(
            collection_name="candidates",
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )
