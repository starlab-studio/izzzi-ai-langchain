from fastapi import APIRouter, Depends, HTTPException, status

from src.interface.dto.analysis_dto import ChatbotQueryRequest, ChatbotResponse
from src.interface.dependencies import get_analysis_facade
from src.application.facades.analysis_facade import AnalysisFacade
from src.infrastructure.auth.jwt_validator import get_current_user, CurrentUser
from src.core.logger import app_logger
from uuid import UUID

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

@router.post("/query", response_model=ChatbotResponse)
async def chatbot_query(
    request: ChatbotQueryRequest,
    current_user: CurrentUser = Depends(get_current_user),
    facade: AnalysisFacade = Depends(get_analysis_facade),
):
    """
    Pose une question au chatbot intelligent
    
    Le chatbot utilise un agent LangChain qui :
    1. Comprend la question
    2. Décide quels outils utiliser (sentiment analysis, search, clustering)
    3. Combine les résultats
    4. Génère une réponse actionnable
    
    Exemples de questions :
    - "Pourquoi mes élèves sont moins satisfaits ce mois-ci ?"
    - "Quels sont les principaux problèmes mentionnés ?"
    - "Comment améliorer le rythme de mon cours ?"
    """
    try:
        app_logger.info(f"Chatbot query from user {current_user.id}: {request.query[:100]}...")
        
        result = await facade.chatbot_conversation(
            query=request.query,
            subject_id=request.subject_id,
            user_id=UUID(current_user.id),
            context=request.context,
        )
        
        return result
        
    except Exception as e:
        app_logger.error(f"Error in chatbot query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your question"
        )