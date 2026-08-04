import uuid
from typing import Generic, TypeVar, Type, Optional, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.sql.expression import false

ModelType = TypeVar("ModelType")

class BaseRepository(Generic[ModelType]):
    """
    Base Repository that enforces org_id isolation on every read/write.
    """
    def __init__(self, model: Type[ModelType], org_id: uuid.UUID, db: AsyncSession):
        self.model = model
        self.org_id = org_id
        self.db = db

    def _base_query(self):
        query = select(self.model)
        # Enforce org_id if the model has it
        if hasattr(self.model, "org_id"):
            query = query.where(self.model.org_id == self.org_id)
        # Ignore soft-deleted records by default
        if hasattr(self.model, "deleted_at"):
            query = query.where(self.model.deleted_at.is_(None))
        return query

    async def get_by_id(self, id: uuid.UUID) -> Optional[ModelType]:
        query = self._base_query().where(self.model.id == id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        query = self._base_query().offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, obj_in: dict) -> ModelType:
        if hasattr(self.model, "org_id"):
            obj_in["org_id"] = self.org_id
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        await self.db.flush()
        return db_obj

    async def update(self, id: uuid.UUID, obj_in: dict) -> Optional[ModelType]:
        # Perform query to ensure the object exists and belongs to the org
        query = self._base_query().where(self.model.id == id)
        result = await self.db.execute(query)
        db_obj = result.scalars().first()
        if not db_obj:
            return None
            
        update_stmt = (
            update(self.model)
            .where(self.model.id == id)
            .where(self.model.org_id == self.org_id)
            .values(**obj_in)
        )
        await self.db.execute(update_stmt)
        await self.db.flush()
        
        return await self.get_by_id(id)

    async def delete(self, id: uuid.UUID, hard: bool = False) -> bool:
        # Perform query to ensure the object exists and belongs to the org
        query = self._base_query().where(self.model.id == id)
        result = await self.db.execute(query)
        db_obj = result.scalars().first()
        if not db_obj:
            return False
            
        if hard:
            await self.db.delete(db_obj)
        else:
            if hasattr(self.model, "deleted_at"):
                from datetime import datetime
                db_obj.deleted_at = datetime.utcnow()
                self.db.add(db_obj)
        await self.db.flush()
        return True
