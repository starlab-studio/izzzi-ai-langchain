from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from src.interface.dto.analysis_dto import (
    SemanticSearchRequest,
    SemanticSearchResultResponse,
)
from src.interface.dependencies import get_analysis_facade
from src.application.facades.analysis_facade import AnalysisFacade
from src.infrastructure.auth.jwt_validator import get_current_user, CurrentUser
from src.core.logger import app_logger

router = APIRouter(prefix="/search", tags=["Search"])

@router.post("/semantic", response_model=List[SemanticSearchResultResponse])
async def semantic_search(
    request: SemanticSearchRequest,
    current_user: CurrentUser = Depends(get_current_user),
    facade: AnalysisFacade = Depends(get_analysis_facade),
):
    """
    Recherche sémantique dans les réponses des élèves
    
    Exemples :
    - "Trouve toutes les mentions du rythme du cours"
    - "Cherche les commentaires sur les supports"
    - "Élèves qui parlent de difficulté à suivre"
    
    La recherche est basée sur la similarité sémantique, pas sur des mots-clés exacts.
    """
    try:
        results = await facade.semantic_search(
            query=request.query,
            subject_id=request.subject_id,
            limit=request.limit,
        )
        
        return results
        
    except Exception as e:
        app_logger.error(f"Error in semantic search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during search"
        )