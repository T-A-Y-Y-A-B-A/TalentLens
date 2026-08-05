from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, SparseVectorParams
from app.core.config import settings

qdrant_client = AsyncQdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)

async def init_qdrant():
    collections = await qdrant_client.get_collections()
    collection_names = [c.name for c in collections.collections]
    
    if "candidates" not in collection_names:
        # Using BGE small dimension which is 384 for dense
        await qdrant_client.create_collection(
            collection_name="candidates",
            vectors_config={"dense": VectorParams(size=384, distance=Distance.COSINE)},
            sparse_vectors_config={"sparse": SparseVectorParams()}
        )
    else:
        # Check if it has sparse vectors config, if not, we can't easily modify the unnamed default vector,
        # but in this scope we'll assume it was created correctly or we wipe it in testing.
        pass
