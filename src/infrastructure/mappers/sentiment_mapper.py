from uuid import UUID
from datetime import datetime

from src.domain.entities.sentiment import SentimentAnalysis, SentimentEvidence
from src.infrastructure.models import SubjectAnalysisModel

class SentimentMapper:
    """Mapper entre SubjectAnalysisModel et SentimentAnalysis entity"""
    
    @staticmethod
    def model_to_entity(model: SubjectAnalysisModel) -> SentimentAnalysis:
        """Convertit un modèle en entité"""
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
    
    @staticmethod
    def entity_to_model_data(sentiment: SentimentAnalysis) -> dict:
        """Convertit une entité en données pour créer un modèle"""
        return {
            "id": sentiment.id,
            "subject_id": sentiment.subject_id,
            "organization_id": sentiment.organization_id,
            "analysis_type": "sentiment",
            "period_start": sentiment.period_start,
            "period_end": sentiment.period_end,
            "result": {
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
            "metadata": {},
        }

