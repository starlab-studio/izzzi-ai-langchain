from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.repositories.subject_analysis_repository import ISubjectAnalysisRepository
from src.infrastructure.models import SubjectAnalysisModel
from src.core.logger import app_logger

class PostgresSubjectAnalysisRepository(ISubjectAnalysisRepository):
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save(
        self,
        subject_id: UUID,
        organization_id: UUID,
        analysis_type: str,
        period_start: datetime,
        period_end: datetime,
        result: dict,
        created_by_user_id: Optional[UUID] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        model = SubjectAnalysisModel(
            subject_id=subject_id,
            organization_id=organization_id,
            analysis_type=analysis_type,
            period_start=period_start,
            period_end=period_end,
            result=result,
            created_by_user_id=created_by_user_id,
            analysis_metadata=metadata or {},
        )
        
        self.session.add(model)
        await self.session.flush()
        
        app_logger.info(f"Saved {analysis_type} analysis for subject {subject_id}")
        
        return {
            "id": str(model.id),
            "subject_id": str(model.subject_id),
            "organization_id": str(model.organization_id),
            "analysis_type": model.analysis_type,
            "period_start": model.period_start.isoformat(),
            "period_end": model.period_end.isoformat(),
            "result": model.result,
            "metadata": model.analysis_metadata,
            "created_by_user_id": str(model.created_by_user_id) if model.created_by_user_id else None,
            "created_at": model.created_at.isoformat(),
        }
    
    async def find_by_subject(
        self,
        subject_id: UUID,
        analysis_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[dict]:
        query = select(SubjectAnalysisModel).where(
            SubjectAnalysisModel.subject_id == subject_id
        )
        
        if analysis_type:
            query = query.where(SubjectAnalysisModel.analysis_type == analysis_type)
        
        query = query.order_by(SubjectAnalysisModel.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        result = await self.session.execute(query)
        models = result.scalars().all()
        
        return [self._model_to_dict(model) for model in models]
    
    async def find_by_period(
        self,
        subject_id: UUID,
        period_start: datetime,
        period_end: datetime,
        analysis_type: Optional[str] = None,
    ) -> List[dict]:
        query = select(SubjectAnalysisModel).where(
            and_(
                SubjectAnalysisModel.subject_id == subject_id,
                SubjectAnalysisModel.period_start >= period_start,
                SubjectAnalysisModel.period_end <= period_end,
            )
        )
        
        if analysis_type:
            query = query.where(SubjectAnalysisModel.analysis_type == analysis_type)
        
        query = query.order_by(SubjectAnalysisModel.created_at.desc())
        
        result = await self.session.execute(query)
        models = result.scalars().all()
        
        return [self._model_to_dict(model) for model in models]
    
    async def find_latest(
        self,
        subject_id: UUID,
        analysis_type: Optional[str] = None,
    ) -> Optional[dict]:
        query = select(SubjectAnalysisModel).where(
            SubjectAnalysisModel.subject_id == subject_id
        )
        
        if analysis_type:
            query = query.where(SubjectAnalysisModel.analysis_type == analysis_type)
        
        query = query.order_by(SubjectAnalysisModel.created_at.desc()).limit(1)
        
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        
        if model:
            return self._model_to_dict(model)
        
        return None
    
    def _model_to_dict(self, model: SubjectAnalysisModel) -> dict:
        return {
            "id": str(model.id),
            "subject_id": str(model.subject_id),
            "organization_id": str(model.organization_id),
            "analysis_type": model.analysis_type,
            "period_start": model.period_start.isoformat(),
            "period_end": model.period_end.isoformat(),
            "result": model.result,
            "metadata": model.analysis_metadata or {},
            "created_by_user_id": str(model.created_by_user_id) if model.created_by_user_id else None,
            "created_at": model.created_at.isoformat(),
        }

