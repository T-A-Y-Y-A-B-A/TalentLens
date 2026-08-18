import asyncio
import uuid
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.workers.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.models.recruitment import Job, JobEmbedding
from app.ai.embeddings import embed_text, EMBEDDING_MODEL_NAME
from app.core.qdrant import qdrant_client
from qdrant_client.models import PointStruct

logger = structlog.get_logger()

async def async_embed_job(job_id: str):
    logger.info("start_embed_job", job_id=job_id)
    
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy.pool import NullPool
    from app.core.config import settings
    engine_local = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, poolclass=NullPool)
    async_session = async_sessionmaker(engine_local, expire_on_commit=False)
    
    try:
        async with async_session() as db:
            result = await db.execute(select(Job).where(Job.id == job_id))
            job = result.scalars().first()
        
        if not job:
            logger.error("job_not_found", job_id=job_id)
            return
            
        try:
            # 1. Prepare text to embed
            job_text = f"{job.title} {job.description} {job.requirements}"
            
            # 2. Generate Dense Vector
            loop = asyncio.get_event_loop()
            dense_vector = await loop.run_in_executor(None, embed_text, job_text)
            
            # 3. Generate Sparse Vector
            def embed_sparse():
                from app.services.matching import get_sparse_model
                model = get_sparse_model()
                return list(model.embed([job_text]))[0]
                
            sparse_dict = await loop.run_in_executor(None, embed_sparse)
            sparse_vector = {
                "indices": sparse_dict.indices.tolist(),
                "values": sparse_dict.values.tolist()
            }
            
            # 4. Save embedding metadata to Postgres
            point_id = str(uuid.uuid4())
            emb_record = JobEmbedding(
                job_id=job.id,
                qdrant_point_id=point_id,
                model_version=EMBEDDING_MODEL_NAME
            )
            # Use merge to handle upsert if job already has embedding
            await db.merge(emb_record)
            await db.commit()
            
            # 5. Upsert to Qdrant 'jobs' collection
            await qdrant_client.upsert(
                collection_name="jobs",
                points=[
                    PointStruct(
                        id=point_id,
                        vector={
                            "dense": dense_vector,
                            "sparse": sparse_vector
                        },
                        payload={
                            "job_id": str(job.id),
                            "org_id": str(job.org_id),
                            "title": job.title
                        }
                    )
                ]
            )
            
            logger.info("embed_job_success", job_id=job_id)
            
        except Exception as e:
            logger.error("embed_job_failed", job_id=job_id, error=str(e))
            await db.rollback()
    finally:
        await engine_local.dispose()

@celery_app.task(name="tasks.embed_job")
def embed_job(job_id: str):
    """
    Celery task entrypoint. Runs the async job embedding workflow in a new event loop.
    """
    async def wrapper():
        await async_embed_job(job_id)
            
    asyncio.run(wrapper())
