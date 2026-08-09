from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, SparseVectorParams
from app.core.config import settings

class _QdrantProxy:
    def __getattr__(self, name):
        client = AsyncQdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        return getattr(client, name)

qdrant_client = _QdrantProxy()

async def init_qdrant():
    client = AsyncQdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
    collections = await client.get_collections()
    collection_names = [c.name for c in collections.collections]
    
    if "candidates" not in collection_names:
        # Using BGE small dimension which is 384 for dense
        await client.create_collection(
            collection_name="candidates",
            vectors_config={"dense": VectorParams(size=384, distance=Distance.COSINE)},
            sparse_vectors_config={"sparse": SparseVectorParams()}
        )
        
    if "jobs" not in collection_names:
        await client.create_collection(
            collection_name="jobs",
            vectors_config={"dense": VectorParams(size=384, distance=Distance.COSINE)},
            sparse_vectors_config={"sparse": SparseVectorParams()}
        )

