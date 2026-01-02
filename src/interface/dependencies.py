from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.connection import get_db_session
from src.infrastructure.repositories.postgres_embedding_repository import (
    PostgresEmbeddingRepository
)
from src.infrastructure.repositories.postgres_response_repository import (
    PostgresResponseRepository
)
from src.infrastructure.frameworks.embedding_service import EmbeddingService
from src.infrastructure.frameworks.langchain_service import LangChainService
from src.infrastructure.frameworks.agent_service import TeacherAssistantAgent
from src.infrastructure.frameworks.tools import (
    SentimentAnalysisTool,
    SemanticSearchTool,
    ClusterAnalysisTool,
)
from src.application.use_cases.analyze_subject_sentiment import AnalyzeSubjectSentimentUseCase
from src.application.use_cases.semantic_search import SemanticSearchUseCase
from src.application.use_cases.cluster_responses import ClusterResponsesUseCase
from src.application.use_cases.chatbot_query import ChatbotQueryUseCase
from src.application.facades.analysis_facade import AnalysisFacade
from src.infrastructure.auth.jwt_validator import get_current_user, CurrentUser

# === Singletons ===

_embedding_service = None
_langchain_service = None

def get_embedding_service() -> EmbeddingService:
    """Singleton pour EmbeddingService"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service

def get_langchain_service() -> LangChainService:
    """Singleton pour LangChainService"""
    global _langchain_service
    if _langchain_service is None:
        _langchain_service = LangChainService()
    return _langchain_service

# === Repositories ===

async def get_embedding_repository(
    session: AsyncSession = Depends(get_db_session)
) -> PostgresEmbeddingRepository:
    return PostgresEmbeddingRepository(session)

async def get_response_repository(
    session: AsyncSession = Depends(get_db_session)
) -> PostgresResponseRepository:
    return PostgresResponseRepository(session)

# === Use Cases ===

async def get_analyze_sentiment_use_case(
    response_repo: PostgresResponseRepository = Depends(get_response_repository),
    embedding_repo: PostgresEmbeddingRepository = Depends(get_embedding_repository),
    langchain_service: LangChainService = Depends(get_langchain_service),
) -> AnalyzeSubjectSentimentUseCase:
    return AnalyzeSubjectSentimentUseCase(
        response_repo=response_repo,
        embedding_repo=embedding_repo,
        langchain_service=langchain_service,
    )

async def get_semantic_search_use_case(
    embedding_repo: PostgresEmbeddingRepository = Depends(get_embedding_repository),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
) -> SemanticSearchUseCase:
    return SemanticSearchUseCase(
        embedding_repo=embedding_repo,
        embedding_service=embedding_service,
    )

async def get_cluster_responses_use_case(
    embedding_repo: PostgresEmbeddingRepository = Depends(get_embedding_repository),
    langchain_service: LangChainService = Depends(get_langchain_service),
) -> ClusterResponsesUseCase:
    return ClusterResponsesUseCase(
        embedding_repo=embedding_repo,
        langchain_service=langchain_service,
    )

async def get_teacher_assistant_agent(
    sentiment_uc: AnalyzeSubjectSentimentUseCase = Depends(get_analyze_sentiment_use_case),
    search_uc: SemanticSearchUseCase = Depends(get_semantic_search_use_case),
    cluster_uc: ClusterResponsesUseCase = Depends(get_cluster_responses_use_case),
) -> TeacherAssistantAgent:
    """Créer l'agent avec ses tools"""
    sentiment_tool = SentimentAnalysisTool(use_case=sentiment_uc)
    search_tool = SemanticSearchTool(use_case=search_uc)
    cluster_tool = ClusterAnalysisTool(use_case=cluster_uc)
    
    return TeacherAssistantAgent(
        sentiment_tool=sentiment_tool,
        search_tool=search_tool,
        cluster_tool=cluster_tool,
    )

async def get_chatbot_query_use_case(
    agent: TeacherAssistantAgent = Depends(get_teacher_assistant_agent),
) -> ChatbotQueryUseCase:
    return ChatbotQueryUseCase(agent=agent)

# === Facade ===

async def get_analysis_facade(
    analyze_sentiment_uc: AnalyzeSubjectSentimentUseCase = Depends(get_analyze_sentiment_use_case),
    semantic_search_uc: SemanticSearchUseCase = Depends(get_semantic_search_use_case),
    cluster_responses_uc: ClusterResponsesUseCase = Depends(get_cluster_responses_use_case),
    chatbot_query_uc: ChatbotQueryUseCase = Depends(get_chatbot_query_use_case),
    response_repo: PostgresResponseRepository = Depends(get_response_repository),
) -> AnalysisFacade:
    return AnalysisFacade(
        analyze_sentiment_uc=analyze_sentiment_uc,
        semantic_search_uc=semantic_search_uc,
        cluster_responses_uc=cluster_responses_uc,
        chatbot_query_uc=chatbot_query_uc,
        response_repo=response_repo,
    )