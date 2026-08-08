import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.qdrant import init_qdrant

if __name__ == "__main__":
    asyncio.run(init_qdrant())
