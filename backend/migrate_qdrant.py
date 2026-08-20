import asyncio
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import VectorParams, Distance, SparseVectorParams
from app.core.config import settings

async def main():
    client = AsyncQdrantClient(
        url=settings.QDRANT_URL, 
        api_key=settings.QDRANT_API_KEY,
        timeout=60.0
    )
    
    await client.delete_collection("jobs")
    await client.create_collection(
        collection_name="jobs",
        vectors_config={
            "dense": VectorParams(size=384, distance=Distance.COSINE),
            "responsibilities_vec": VectorParams(size=384, distance=Distance.COSINE),
            "requirements_vec": VectorParams(size=384, distance=Distance.COSINE),
            "expectations_vec": VectorParams(size=384, distance=Distance.COSINE),
        },
        sparse_vectors_config={"sparse": SparseVectorParams()}
    )
    print("Recreated jobs collection.")
    
    await client.delete_collection("candidates")
    await client.create_collection(
        collection_name="candidates",
        vectors_config={
            "dense": VectorParams(size=384, distance=Distance.COSINE),
            "experience_vec": VectorParams(size=384, distance=Distance.COSINE),
            "titles_vec": VectorParams(size=384, distance=Distance.COSINE),
        },
        sparse_vectors_config={"sparse": SparseVectorParams()}
    )
    print("Recreated candidates collection.")
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
