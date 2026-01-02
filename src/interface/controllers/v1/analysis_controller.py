from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID

from src.interface.dto.analysis_dto import (
    AnalyzeSentimentRequest,
    SentimentAnalysisResponse,
    GenerateInsightsRequest,
    ComprehensiveInsightsResponse,
    CompareSubjectsRequest,
    ComparisonResponse,
    PredictRisksRequest,
    RiskPredictionResponse,
)
from src.interface.dependencies import get_analysis_facade
from src.application.facades.analysis_facade import AnalysisFacade
from src.infrastructure.auth.jwt_validator import get_current_user, CurrentUser
from src.core.exceptions import InsufficientDataException, NotFoundException
from src.core.logger import app_logger

router = APIRouter(prefix="/analysis", tags=["Analysis"])

@router.post("/sentiment", response_model=SentimentAnalysisResponse)
async def analyze_sentiment(
    request: AnalyzeSentimentRequest,
    current_user: CurrentUser = Depends(get_current_user),
    facade: AnalysisFacade = Depends(get_analysis_facade),
):
    """
    Analyse le sentiment des élèves pour une matière
    
    Retourne :
    - Score global de sentiment (-1 à 1)
    - Distribution positive/neutre/négative
    - Points positifs et négatifs
    - Recommandations
    - Thèmes identifiés
    """
    try:
        app_logger.info(f"User {current_user.id} analyzing sentiment for subject {request.subject_id}")
        
        result = await facade.analyze_subject_sentiment(
            subject_id=request.subject_id,
            period_days=request.period_days,
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
        app_logger.error(f"Error analyzing sentiment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while analyzing sentiment"
        )

@router.post("/insights/generate", response_model=ComprehensiveInsightsResponse)
async def generate_insights(
    request: GenerateInsightsRequest,
    current_user: CurrentUser = Depends(get_current_user),
    facade: AnalysisFacade = Depends(get_analysis_facade),
):
    """
    Génère des insights complets pour une matière
    
    Combine :
    - Analyse de sentiment
    - Identification des thèmes
    - Insights actionnables
    - Recommandations prioritaires
    """
    try:
        result = await facade.generate_comprehensive_insights(
            subject_id=request.subject_id,
            period_days=request.period_days,
            user_id=UUID(current_user.id),
        )
        
        return result
        
    except InsufficientDataException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        app_logger.error(f"Error generating insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating insights"
        )

@router.post("/compare", response_model=ComparisonResponse)
async def compare_subjects(
    request: CompareSubjectsRequest,
    current_user: CurrentUser = Depends(get_current_user),
    facade: AnalysisFacade = Depends(get_analysis_facade),
):
    """
    Compare plusieurs matières
    
    Identifie :
    - Les différences de sentiment
    - Les forces et faiblesses de chaque matière
    - Le "gagnant" (meilleur sentiment)
    """
    try:
        result = await facade.compare_subjects(
            subject_ids=request.subject_ids,
            period_days=request.period_days,
        )
        
        return result
        
    except Exception as e:
        app_logger.error(f"Error comparing subjects: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/risks/predict", response_model=RiskPredictionResponse)
async def predict_risks(
    request: PredictRisksRequest,
    current_user: CurrentUser = Depends(get_current_user),
    facade: AnalysisFacade = Depends(get_analysis_facade),
):
    """
    Analyse prédictive : détecte les risques potentiels
    
    Identifie :
    - Tendances négatives
    - Signaux faibles
    - Score de risque
    - Recommandations préventives
    """
    try:
        result = await facade.predict_risks(
            subject_id=request.subject_id,
            lookback_days=request.lookback_days,
        )
        
        return result
        
    except InsufficientDataException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        app_logger.error(f"Error predicting risks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )