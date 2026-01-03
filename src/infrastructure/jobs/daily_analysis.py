import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy import text
import httpx
from collections import defaultdict

from src.infrastructure.jobs.celery_app import celery_app
from src.infrastructure.database.connection import async_session_maker
from src.infrastructure.repositories.postgres_response_repository import (
    PostgresResponseRepository
)
from src.application.facades.analysis_facade import AnalysisFacade
from src.application.use_cases.generate_feedback_alerts import GenerateFeedbackAlertsUseCase
from src.core.logger import app_logger
from src.configs import get_settings
from uuid import UUID

@celery_app.task(
    name="src.infrastructure.jobs.daily_analysis.daily_analysis_task",
    max_retries=2,
)
def daily_analysis_task():
    """
    Daily automatic analysis
    
    Workflow:
    1. Identify all active subjects
    2. For each subject with new responses (last 24h)
    3. Run sentiment analysis
    4. Detect alerts (negative sentiment, decline)
    5. Notify if necessary
    
    Runs daily at 6 AM
    """
    try:
        app_logger.info("Starting daily analysis job")
        
        result = asyncio.run(daily_analysis_async())
        
        app_logger.info(f"Daily analysis completed: {result}")
        return result
        
    except Exception as e:
        app_logger.error(f"Error in daily analysis: {e}")
        raise

async def daily_analysis_async() -> Dict[str, Any]:
    """Async logic for daily analysis"""
    
    async with async_session_maker() as session:
        # Query to get subjects with recent responses, including organization name
        query = text("""
            SELECT DISTINCT 
                s.id as subject_id,
                s.name as subject_name,
                s.organization_id,
                o.name as organization_name,
                COUNT(DISTINCT r.id) as response_count
            FROM subjects s
            JOIN organizations o ON o.id = s.organization_id
            JOIN quizzes q ON q.subject_id = s.id
            JOIN responses r ON r.quiz_id = q.id
            WHERE r.submitted_at >= NOW() - INTERVAL '24 hours'
              AND s.is_active = true
            GROUP BY s.id, s.name, s.organization_id, o.name
            HAVING COUNT(DISTINCT r.id) >= 3
            ORDER BY response_count DESC
        """)
        
        result = await session.execute(query)
        subjects = result.fetchall()
        
        if not subjects:
            app_logger.info("No active subjects with recent responses")
            return {"subjects_analyzed": 0, "alerts": 0}
        
        app_logger.info(f"Found {len(subjects)} subjects to analyze")
        
        analyzed_count = 0
        total_alerts_sent = 0
        
        # Group subjects by organization for batch processing
        subjects_by_org = defaultdict(list)
        for subject in subjects:
            subjects_by_org[str(subject.organization_id)].append(subject)
        
        for organization_id, org_subjects in subjects_by_org.items():
            try:
                # Create facade and use case for this organization
                facade = await create_facade_for_analysis(session)
                alerts_use_case = GenerateFeedbackAlertsUseCase(analysis_facade=facade)
                
                # Process each subject in this organization
                alerts_by_subject: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
                
                for subject in org_subjects:
                    try:
                        subject_id = UUID(str(subject.subject_id))
                        
                        # Generate alerts using the use case
                        alerts = await alerts_use_case.execute(
                            subject_id=subject_id,
                            period_days=7,  # Last week
                        )
                        
                        if alerts:
                            alerts_by_subject[str(subject.subject_id)] = {
                                'alerts': alerts,
                                'subject_name': subject.subject_name,
                                'organization_name': subject.organization_name,
                            }
                            analyzed_count += 1
                            
                    except Exception as e:
                        app_logger.error(f"Error generating alerts for subject {subject.subject_id}: {e}")
                        continue
                
                # Send alerts grouped by subject to backend
                if alerts_by_subject:
                    for subject_id, alert_data in alerts_by_subject.items():
                        try:
                            await send_alert_to_backend(
                                organization_id=organization_id,
                                organization_name=alert_data['organization_name'],
                                subject_id=subject_id,
                                subject_name=alert_data['subject_name'],
                                alerts=alert_data['alerts'],
                            )
                            total_alerts_sent += len(alert_data['alerts'])
                        except Exception as e:
                            app_logger.error(f"Error sending alerts to backend for subject {subject_id}: {e}")
                            continue
                
            except Exception as e:
                app_logger.error(f"Error processing organization {organization_id}: {e}")
                continue
        
        await session.commit()
        
        return {
            "subjects_analyzed": analyzed_count,
            "alerts_sent": total_alerts_sent,
            "timestamp": datetime.now().isoformat(),
        }

async def create_facade_for_analysis(session) -> AnalysisFacade:
    """Helper to create facade with dependencies"""
    from src.infrastructure.repositories.postgres_embedding_repository import (
        PostgresEmbeddingRepository
    )
    from src.infrastructure.frameworks.embedding_service import EmbeddingService
    from src.infrastructure.frameworks.langchain_service import LangChainService
    from src.application.use_cases.analyze_subject_sentiment import (
        AnalyzeSubjectSentimentUseCase
    )
    from src.application.use_cases.semantic_search import SemanticSearchUseCase
    from src.application.use_cases.cluster_responses import ClusterResponsesUseCase
    from src.application.use_cases.chatbot_query import ChatbotQueryUseCase
    from src.infrastructure.frameworks.agent_service import TeacherAssistantAgent
    from src.infrastructure.frameworks.tools import (
        SentimentAnalysisTool,
        SemanticSearchTool,
        ClusterAnalysisTool,
    )
    
    # Create repositories
    response_repo = PostgresResponseRepository(session)
    embedding_repo = PostgresEmbeddingRepository(session)
    
    # Create services (singletons)
    embedding_service = EmbeddingService()
    langchain_service = LangChainService()
    
    # Create use cases first (they don't need tools)
    analyze_sentiment_uc = AnalyzeSubjectSentimentUseCase(
        response_repo=response_repo,
        embedding_repo=embedding_repo,
        langchain_service=langchain_service,
    )
    
    semantic_search_uc = SemanticSearchUseCase(
        embedding_repo=embedding_repo,
        embedding_service=embedding_service,
    )
    
    cluster_responses_uc = ClusterResponsesUseCase(
        embedding_repo=embedding_repo,
        langchain_service=langchain_service,
    )
    
    # Create tools with use cases
    sentiment_tool = SentimentAnalysisTool(use_case=analyze_sentiment_uc)
    semantic_search_tool = SemanticSearchTool(use_case=semantic_search_uc)
    cluster_tool = ClusterAnalysisTool(use_case=cluster_responses_uc)
    
    # Create agent
    agent = TeacherAssistantAgent(
        sentiment_tool=sentiment_tool,
        search_tool=semantic_search_tool,
        cluster_tool=cluster_tool,
    )
    
    chatbot_query_uc = ChatbotQueryUseCase(agent=agent)
    
    # Create facade
    facade = AnalysisFacade(
        analyze_sentiment_uc=analyze_sentiment_uc,
        semantic_search_uc=semantic_search_uc,
        cluster_responses_uc=cluster_responses_uc,
        chatbot_query_uc=chatbot_query_uc,
        response_repo=response_repo,
    )
    
    return facade

async def save_analysis_to_cache(session, analysis: Dict[str, Any]):
    """Save analysis to analysis_cache table"""
    from src.infrastructure.database.models import AnalysisCacheModel
    from datetime import datetime, timedelta
    import json
    
    cache_key = f"daily_analysis:{analysis['subject_id']}:{datetime.now().date()}"
    
    cache_entry = AnalysisCacheModel(
        cache_key=cache_key,
        cache_value=analysis,
        expires_at=datetime.now() + timedelta(days=7),
    )
    
    session.add(cache_entry)

async def send_alert_to_backend(
    organization_id: str,
    organization_name: str,
    subject_id: str,
    subject_name: str,
    alerts: List[Dict[str, Any]],
):
    """
    Send alerts to backend via POST /v1/alerts
    
    The backend will handle email and push notifications via AlertGeneratedEvent
    """
    settings = get_settings()
    backend_url = settings.BACKEND_URL
    
    app_logger.info(f"Sending {len(alerts)} alert(s) to backend for subject {subject_id}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{backend_url}/v1/feedback/alerts",
                json={
                    "organizationId": organization_id,
                    "organizationName": organization_name,
                    "subjectId": subject_id,
                    "subjectName": subject_name,
                    "alerts": alerts,
                },
                headers={
                    "Content-Type": "application/json",
                },
            )
            
            if response.status_code == 200:
                app_logger.info(
                    f"Alerts successfully sent to backend for subject {subject_id}"
                )
            else:
                app_logger.error(
                    f"Failed to send alerts to backend: {response.status_code} - {response.text}"
                )
                raise Exception(f"Backend API returned status {response.status_code}")
                
    except httpx.TimeoutException:
        app_logger.error(f"Timeout when calling backend API for subject {subject_id}")
        raise
    except Exception as e:
        app_logger.error(f"Error calling backend API: {e}")
        raise