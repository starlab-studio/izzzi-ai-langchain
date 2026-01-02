from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.insight import Insight, InsightPriority, InsightType
from src.domain.repositories.insight_repository import IInsightRepository
from src.infrastructure.models import InsightModel
from src.core.logger import app_logger

class PostgresInsightRepository(IInsightRepository):
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save(self, insight: Insight) -> Insight:
        """Sauvegarde un insight"""
        model = InsightModel(
            id=insight.id,
            subject_id=insight.subject_id,
            organization_id=insight.organization_id,
            insight_type=insight.type.value,
            title=insight.title,
            content=insight.content,
            embedding=insight.embedding,
            evidence={"texts": insight.evidence_texts, "count": insight.evidence_count},
            confidence=insight.confidence,
            priority=insight.priority.value,
            insight_metadata=insight.metadata,
        )
        
        self.session.add(model)
        await self.session.flush()
        
        app_logger.info(f"Saved insight {insight.id} for subject {insight.subject_id}")
        return insight
    
    async def find_by_subject(
        self,
        subject_id: UUID,
        limit: Optional[int] = None,
    ) -> List[Insight]:
        query = select(InsightModel).where(
            InsightModel.subject_id == subject_id
        ).order_by(InsightModel.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        result = await self.session.execute(query)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def find_by_organization(
        self,
        organization_id: UUID,
        limit: Optional[int] = None,
    ) -> List[Insight]:
        query = select(InsightModel).where(
            InsightModel.organization_id == organization_id
        ).order_by(InsightModel.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        result = await self.session.execute(query)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def find_actionable(
        self,
        subject_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None,
    ) -> List[Insight]:
        query = select(InsightModel).where(
            InsightModel.priority.in_([InsightPriority.HIGH.value, InsightPriority.URGENT.value])
        )
        
        if subject_id:
            query = query.where(InsightModel.subject_id == subject_id)
        
        if organization_id:
            query = query.where(InsightModel.organization_id == organization_id)
        
        query = query.order_by(InsightModel.created_at.desc())
        
        result = await self.session.execute(query)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def find_by_type(
        self,
        insight_type: InsightType,
        subject_id: Optional[UUID] = None,
        limit: Optional[int] = None,
    ) -> List[Insight]:
        query = select(InsightModel).where(
            InsightModel.insight_type == insight_type.value
        )
        
        if subject_id:
            query = query.where(InsightModel.subject_id == subject_id)
        
        query = query.order_by(InsightModel.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        result = await self.session.execute(query)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def delete(self, insight_id: UUID) -> bool:
        query = select(InsightModel).where(InsightModel.id == insight_id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        
        if model:
            await self.session.delete(model)
            await self.session.flush()
            return True
        
        return False
    
    def _model_to_entity(self, model: InsightModel) -> Insight:
        evidence_data = model.evidence or {}
        
        return Insight(
            id=model.id,
            subject_id=model.subject_id,
            organization_id=model.organization_id,
            type=InsightType(model.insight_type),
            priority=InsightPriority(model.priority) if model.priority else InsightPriority.MEDIUM,
            title=model.title,
            content=model.content,
            evidence_texts=evidence_data.get("texts", []),
            evidence_count=evidence_data.get("count", 0),
            confidence=model.confidence or 0.0,
            embedding=list(model.embedding) if model.embedding else None,
            metadata=model.insight_metadata or {},
            created_at=model.created_at,
        )

