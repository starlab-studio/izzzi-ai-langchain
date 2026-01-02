from uuid import UUID
from datetime import datetime

from src.infrastructure.models import SubjectAnalysisModel

class SubjectAnalysisMapper:
    """Mapper pour SubjectAnalysisModel"""
    
    @staticmethod
    def model_to_dict(model: SubjectAnalysisModel) -> dict:
        """Convertit un modèle en dictionnaire"""
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
    
    @staticmethod
    def dict_to_model_data(data: dict) -> dict:
        """Convertit un dictionnaire en données pour créer un modèle"""
        return {
            "subject_id": UUID(data["subject_id"]) if isinstance(data["subject_id"], str) else data["subject_id"],
            "organization_id": UUID(data["organization_id"]) if isinstance(data["organization_id"], str) else data["organization_id"],
            "analysis_type": data["analysis_type"],
            "period_start": datetime.fromisoformat(data["period_start"]) if isinstance(data["period_start"], str) else data["period_start"],
            "period_end": datetime.fromisoformat(data["period_end"]) if isinstance(data["period_end"], str) else data["period_end"],
            "result": data["result"],
            "metadata": data.get("metadata", {}),
            "created_by_user_id": UUID(data["created_by_user_id"]) if data.get("created_by_user_id") else None,
        }

