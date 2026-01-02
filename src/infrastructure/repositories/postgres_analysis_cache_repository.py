from typing import Optional, Any
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.repositories.analysis_cache_repository import IAnalysisCacheRepository
from src.infrastructure.models import AnalysisCacheModel
from src.core.logger import app_logger

class PostgresAnalysisCacheRepository(IAnalysisCacheRepository):
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get(self, cache_key: str) -> Optional[Any]:
        query = select(AnalysisCacheModel).where(
            and_(
                AnalysisCacheModel.cache_key == cache_key,
                AnalysisCacheModel.expires_at > datetime.now()
            )
        )
        
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        
        if model:
            app_logger.debug(f"Cache hit for key: {cache_key}")
            return model.cache_value
        
        app_logger.debug(f"Cache miss for key: {cache_key}")
        return None
    
    async def set(
        self,
        cache_key: str,
        cache_value: Any,
        expires_at: datetime,
    ) -> bool:
        query = select(AnalysisCacheModel).where(
            AnalysisCacheModel.cache_key == cache_key
        )
        result = await self.session.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            existing.cache_value = cache_value
            existing.expires_at = expires_at
        else:
            model = AnalysisCacheModel(
                cache_key=cache_key,
                cache_value=cache_value,
                expires_at=expires_at,
            )
            self.session.add(model)
        
        await self.session.flush()
        app_logger.debug(f"Cached value for key: {cache_key}")
        return True
    
    async def delete(self, cache_key: str) -> bool:
        query = select(AnalysisCacheModel).where(
            AnalysisCacheModel.cache_key == cache_key
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        
        if model:
            await self.session.delete(model)
            await self.session.flush()
            app_logger.debug(f"Deleted cache key: {cache_key}")
            return True
        
        return False
    
    async def clear_expired(self) -> int:
        query = select(AnalysisCacheModel).where(
            AnalysisCacheModel.expires_at <= datetime.now()
        )
        result = await self.session.execute(query)
        models = result.scalars().all()
        
        count = len(models)
        for model in models:
            await self.session.delete(model)
        
        await self.session.flush()
        
        if count > 0:
            app_logger.info(f"Cleared {count} expired cache entries")
        
        return count
    
    async def exists(self, cache_key: str) -> bool:
        query = select(AnalysisCacheModel).where(
            and_(
                AnalysisCacheModel.cache_key == cache_key,
                AnalysisCacheModel.expires_at > datetime.now()
            )
        )
        
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        
        return model is not None

