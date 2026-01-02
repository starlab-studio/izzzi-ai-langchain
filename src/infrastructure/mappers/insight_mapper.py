from uuid import UUID

from src.domain.entities.insight import Insight, InsightType, InsightPriority
from src.infrastructure.models import InsightModel

class InsightMapper:
    """Mapper entre InsightModel et Insight entity"""
    
    @staticmethod
    def model_to_entity(model: InsightModel) -> Insight:
        """Convertit un modèle en entité"""
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
    
    @staticmethod
    def entity_to_model_data(insight: Insight) -> dict:
        """Convertit une entité en données pour créer un modèle"""
        return {
            "id": insight.id,
            "subject_id": insight.subject_id,
            "organization_id": insight.organization_id,
            "insight_type": insight.type.value,
            "title": insight.title,
            "content": insight.content,
            "embedding": insight.embedding,
            "evidence": {
                "texts": insight.evidence_texts,
                "count": insight.evidence_count,
            },
            "confidence": insight.confidence,
            "priority": insight.priority.value,
            "metadata": insight.metadata,
        }

