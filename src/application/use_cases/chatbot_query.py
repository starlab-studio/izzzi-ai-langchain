from typing import Dict, Any
from uuid import UUID

from src.infrastructure.frameworks.agent_service import TeacherAssistantAgent
from src.core.logger import app_logger

class ChatbotQueryUseCase:
    """Use case pour le chatbot avec agent LangChain"""
    
    def __init__(self, agent: TeacherAssistantAgent):
        self.agent = agent
    
    async def execute(
        self,
        query: str,
        subject_id: UUID,
        user_id: UUID,
        context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Répond à une question via l'agent intelligent
        
        Args:
            query: Question de l'enseignant
            subject_id: ID de la matière
            user_id: ID de l'utilisateur (traçabilité)
            context: Contexte additionnel
        
        Returns:
            {
                "answer": str,
                "tools_used": List[str],
                "sources": List[dict],
            }
        """
        app_logger.info(f"Chatbot query from user {user_id}: {query[:100]}...")
        
        # L'agent va automatiquement décider quels outils utiliser
        result = await self.agent.query(
            question=query,
            subject_id=str(subject_id),
            context=context,
        )
        
        # Sauvegarder la conversation (optionnel)
        # TODO: Persist to chatbot_conversations table
        
        app_logger.info(f"Chatbot response generated using tools: {result['tools_used']}")
        
        return {
            "query": query,
            "answer": result['answer'],
            "tools_used": result['tools_used'],
            "intermediate_steps": result.get('intermediate_steps', []),
        }