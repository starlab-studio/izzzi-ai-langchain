from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.sentiment import SentimentAnalysis, SentimentEvidence
from src.domain.repositories.sentiment_repository import ISentimentRepository
from src.infrastructure.models import SubjectAnalysisModel
from src.core.logger import app_logger

class PostgresSentimentRepository(ISentimentRepository):
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save(self, sentiment: SentimentAnalysis) -> SentimentAnalysis:
        """Sauvegarde une analyse de sentiment"""
        model = SubjectAnalysisModel(
            id=sentiment.id,
            subject_id=sentiment.subject_id,
            organization_id=sentiment.organization_id,
            analysis_type="sentiment",
            period_start=sentiment.period_start,
            period_end=sentiment.period_end,
            result={
                "overall_score": sentiment.overall_score,
                "confidence": sentiment.confidence,
                "positive_percentage": sentiment.positive_percentage,
                "neutral_percentage": sentiment.neutral_percentage,
                "negative_percentage": sentiment.negative_percentage,
                "trend_percentage": sentiment.trend_percentage,
                "previous_score": sentiment.previous_score,
                "total_responses": sentiment.total_responses,
                "positive_evidence": [
                    {
                        "text": ev.text,
                        "response_id": str(ev.response_id),
                        "created_at": ev.created_at.isoformat(),
                        "confidence": ev.confidence,
                    }
                    for ev in sentiment.positive_evidence
                ],
                "negative_evidence": [
                    {
                        "text": ev.text,
                        "response_id": str(ev.response_id),
                        "created_at": ev.created_at.isoformat(),
                        "confidence": ev.confidence,
                    }
                    for ev in sentiment.negative_evidence
                ],
            },
            metadata={},
        )
        
        self.session.add(model)
        await self.session.flush()
        
        app_logger.info(f"Saved sentiment analysis {sentiment.id} for subject {sentiment.subject_id}")
        return sentiment
    
    async def find_by_subject(
        self,
        subject_id: UUID,
    ) -> Optional[SentimentAnalysis]:
        query = select(SubjectAnalysisModel).where(
            SubjectAnalysisModel.subject_id == subject_id,
            SubjectAnalysisModel.analysis_type == "sentiment"
        ).order_by(SubjectAnalysisModel.created_at.desc()).limit(1)
        
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        
        if model:
            return self._model_to_entity(model)
        
        return None
    
    async def find_latest(
        self,
        subject_id: UUID,
        limit: int = 1,
    ) -> list[SentimentAnalysis]:
        query = select(SubjectAnalysisModel).where(
            SubjectAnalysisModel.subject_id == subject_id,
            SubjectAnalysisModel.analysis_type == "sentiment"
        ).order_by(SubjectAnalysisModel.created_at.desc()).limit(limit)
        
        result = await self.session.execute(query)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    def _model_to_entity(self, model: SubjectAnalysisModel) -> SentimentAnalysis:
        from datetime import datetime
        
        result = model.result or {}
        
        return SentimentAnalysis(
            id=model.id,
            subject_id=model.subject_id,
            organization_id=model.organization_id,
            overall_score=result.get("overall_score", 0.0),
            confidence=result.get("confidence", 0.0),
            positive_percentage=result.get("positive_percentage", 0.0),
            neutral_percentage=result.get("neutral_percentage", 0.0),
            negative_percentage=result.get("negative_percentage", 0.0),
            trend_percentage=result.get("trend_percentage"),
            previous_score=result.get("previous_score"),
            positive_evidence=[
                SentimentEvidence(
                    text=ev["text"],
                    response_id=UUID(ev["response_id"]),
                    created_at=datetime.fromisoformat(ev["created_at"]),
                    confidence=ev["confidence"],
                )
                for ev in result.get("positive_evidence", [])
            ],
            negative_evidence=[
                SentimentEvidence(
                    text=ev["text"],
                    response_id=UUID(ev["response_id"]),
                    created_at=datetime.fromisoformat(ev["created_at"]),
                    confidence=ev["confidence"],
                )
                for ev in result.get("negative_evidence", [])
            ],
            total_responses=result.get("total_responses", 0),
            period_start=model.period_start,
            period_end=model.period_end,
            created_at=model.created_at,
        )

