import asyncio
import json
from qdrant_client import AsyncQdrantClient

async def main():
    client = AsyncQdrantClient(host='localhost', port=6333)
    p = await client.scroll(collection_name='candidates', limit=1)
    if p[0]:
        print(json.dumps(p[0][0].payload, indent=2))
    else:
        print('empty')

asyncio.run(main())
