import asyncio
import json
from qdrant_client import AsyncQdrantClient
from app.core.config import settings

async def main():
    client = AsyncQdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
    p = await client.scroll(collection_name='candidates', limit=1)
    if p[0]:
        print(json.dumps(p[0][0].payload, indent=2))
    else:
        print('empty')

asyncio.run(main())
