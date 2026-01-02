from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID

from src.interface.dto.analysis_dto import (
    AnalyzeSentimentRequest,
    SentimentAnalysisResponse,
)
from src.interface.dependencies import get_analysis_facade
from src.application.facades.analysis_facade import AnalysisFacade
from src.application.use_cases.generate_feedback_summary import GenerateFeedbackSummaryUseCase
from src.application.use_cases.generate_feedback_alerts import GenerateFeedbackAlertsUseCase
from src.infrastructure.frameworks.langchain_service import LangChainService
from src.infrastructure.repositories.postgres_analysis_cache_repository import (
    PostgresAnalysisCacheRepository
)
from src.infrastructure.database.connection import get_db_session
from src.infrastructure.auth.jwt_validator import get_current_user, CurrentUser
from src.core.logger import app_logger
from src.core.exceptions import InsufficientDataException

router = APIRouter(prefix="/feedback", tags=["Feedback"])

# Dependencies supplémentaires
from src.interface.dependencies import get_langchain_service

async def get_cache_repository(
    session = Depends(get_db_session)
) -> PostgresAnalysisCacheRepository:
    return PostgresAnalysisCacheRepository(session)

# Dependency pour GenerateFeedbackSummaryUseCase
async def get_feedback_summary_use_case(
    analysis_facade: AnalysisFacade = Depends(get_analysis_facade),
    langchain_service: LangChainService = Depends(get_langchain_service),
    cache_repo: PostgresAnalysisCacheRepository = Depends(get_cache_repository),
) -> GenerateFeedbackSummaryUseCase:
    return GenerateFeedbackSummaryUseCase(
        analysis_facade=analysis_facade,
        langchain_service=langchain_service,
        cache_repo=cache_repo,
    )

# Dependency pour GenerateFeedbackAlertsUseCase
async def get_feedback_alerts_use_case(
    analysis_facade: AnalysisFacade = Depends(get_analysis_facade),
) -> GenerateFeedbackAlertsUseCase:
    return GenerateFeedbackAlertsUseCase(analysis_facade=analysis_facade)

@router.get("/subjects/{subject_id}/summary")
async def get_feedback_summary(
    subject_id: UUID,
    period_days: int = 30,
    current_user: CurrentUser = Depends(get_current_user),
    use_case: GenerateFeedbackSummaryUseCase = Depends(get_feedback_summary_use_case),
):
    """
    Récupère le résumé IA des feedbacks pour une matière
    
    Returns:
        {
            "summary": str,  # Résumé court
            "full_summary": str,  # Résumé détaillé
            "generated_at": str,
        }
    """
    try:
        app_logger.info(f"User {current_user.id} requesting summary for subject {subject_id}")
        
        result = await use_case.execute(
            subject_id=subject_id,
            period_days=period_days,
            user_id=UUID(current_user.id),
        )
        
        return result
        
    except InsufficientDataException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": e.message,
                "min_required": e.details.get("min_required"),
                "actual": e.details.get("actual"),
            }
        )
    except Exception as e:
        app_logger.error(f"Error generating feedback summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating the summary"
        )

@router.get("/subjects/{subject_id}/alerts")
async def get_feedback_alerts(
    subject_id: UUID,
    period_days: int = 30,
    current_user: CurrentUser = Depends(get_current_user),
    use_case: GenerateFeedbackAlertsUseCase = Depends(get_feedback_alerts_use_case),
):
    """
    Récupère les alertes IA pour une matière
    
    Returns:
        {
            "alerts": [
                {
                    "id": str,
                    "type": "negative" | "alert",
                    "number": str,
                    "content": str,
                    "title": str,
                    "priority": str,
                    "timestamp": str,
                }
            ]
        }
    """
    try:
        app_logger.info(f"User {current_user.id} requesting alerts for subject {subject_id}")
        
        alerts = await use_case.execute(
            subject_id=subject_id,
            period_days=period_days,
        )
        
        return {"alerts": alerts}
        
    except Exception as e:
        app_logger.error(f"Error generating feedback alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating alerts"
        )

@router.post("/subjects/{subject_id}/analyze")
async def trigger_analysis(
    subject_id: UUID,
    period_days: int = 30,
    current_user: CurrentUser = Depends(get_current_user),
    facade: AnalysisFacade = Depends(get_analysis_facade),
):
    """
    Déclenche une analyse complète pour une matière (force refresh)
    
    Utile pour forcer la régénération des insights et invalider le cache
    """
    try:
        app_logger.info(f"User {current_user.id} triggering analysis for subject {subject_id}")
        
        # Générer les insights complets (force refresh)
        result = await facade.generate_comprehensive_insights(
            subject_id=subject_id,
            period_days=period_days,
            user_id=UUID(current_user.id),
        )
        
        return {
            "status": "completed",
            "subject_id": str(subject_id),
            "insights_generated": len(result.get("insights", [])),
            "generated_at": result.get("generated_at"),
        }
        
    except Exception as e:
        app_logger.error(f"Error triggering analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while triggering analysis"
        )

