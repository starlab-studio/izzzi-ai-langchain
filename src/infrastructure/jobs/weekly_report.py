import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy import text
import httpx

from src.infrastructure.jobs.celery_app import celery_app
from src.infrastructure.database.connection import async_session_maker
from src.infrastructure.frameworks.agent_service import ReportGeneratorAgent
from src.core.logger import app_logger
from src.configs import get_settings

@celery_app.task(
    name="src.infrastructure.jobs.weekly_report.weekly_report_task",
    max_retries=1,
)
def weekly_report_task():
    """
    Génère un rapport hebdomadaire pour chaque organisation
    
    Workflow :
    1. Grouper les matières par organisation
    2. Pour chaque organisation, utiliser le ReportGeneratorAgent
    3. L'agent analyse toutes les matières et génère un rapport structuré
    4. Envoyer le rapport au backend via POST /v1/reports
    5. Le backend se charge d'envoyer les emails et notifications push
    
    S'exécute tous les lundis à 8h
    """
    try:
        app_logger.info("Starting weekly report generation")
        
        result = asyncio.run(weekly_report_async())
        
        app_logger.info(f"Weekly report completed: {result}")
        return result
        
    except Exception as e:
        app_logger.error(f"Error in weekly report: {e}")
        raise

async def weekly_report_async() -> Dict[str, Any]:
    """Génération des rapports hebdomadaires"""
    
    async with async_session_maker() as session:
        # 1. Récupérer les organisations avec activité
        query = text("""
            SELECT 
                o.id as organization_id,
                o.name as organization_name,
                ARRAY_AGG(DISTINCT s.id) as subject_ids,
                COUNT(DISTINCT r.id) as total_responses
            FROM organizations o
            JOIN subjects s ON s.organization_id = o.id
            JOIN quizzes q ON q.subject_id = s.id
            JOIN responses r ON r.quiz_id = q.id
            WHERE r.submitted_at >= NOW() - INTERVAL '7 days'
              AND s.is_active = true
            GROUP BY o.id, o.name
            HAVING COUNT(DISTINCT r.id) >= 10
        """)
        
        result = await session.execute(query)
        organizations = result.fetchall()
        
        if not organizations:
            app_logger.info("No organizations with sufficient activity")
            return {"reports_generated": 0}
        
        app_logger.info(f"Generating reports for {len(organizations)} organizations")
        
        # 2. Créer l'agent générateur de rapports
        agent = await create_report_agent()
        
        reports_generated = 0
        
        for org in organizations:
            try:
                # Générer le rapport via l'agent
                report = await agent.generate_weekly_report(
                    subject_ids=[str(sid) for sid in org.subject_ids],
                    organization_name=org.organization_name,
                )
                
                # Sauvegarder le rapport et déclencher les notifications
                await save_report(
                    organization_id=str(org.organization_id),
                    organization_name=org.organization_name,
                    report_content=report,
                    subject_ids=[str(sid) for sid in org.subject_ids],
                )
                
                reports_generated += 1
                
            except Exception as e:
                app_logger.error(f"Error generating report for org {org.organization_id}: {e}")
                continue
        
        await session.commit()
        
        return {
            "reports_generated": reports_generated,
            "organizations_processed": len(organizations),
            "timestamp": datetime.now().isoformat(),
        }

async def create_report_agent() -> ReportGeneratorAgent:
    """Créer l'agent de génération de rapports"""
    # TODO: Implémenter avec DI
    from src.infrastructure.frameworks.tools import (
        SentimentAnalysisTool,
        SemanticSearchTool,
        ClusterAnalysisTool,
    )
    
    # Placeholder
    raise NotImplementedError("Implement DI for agent in jobs")

async def save_report(
    organization_id: str,
    organization_name: str,
    report_content: str,
    subject_ids: List[str],
):
    """
    Sauvegarde le rapport généré en appelant l'API backend
    
    Le backend se charge ensuite d'envoyer les emails et notifications push
    via l'événement report.generated
    """
    settings = get_settings()
    backend_url = settings.BACKEND_URL
    
    app_logger.info(f"Saving report for organization {organization_id}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{backend_url}/v1/reports",
                json={
                    "organizationId": organization_id,
                    "organizationName": organization_name,
                    "reportContent": report_content,
                    "subjectIds": subject_ids,
                },
                headers={
                    "Content-Type": "application/json",
                },
            )
            
            if response.status_code == 200:
                app_logger.info(
                    f"Report successfully sent to backend for organization {organization_id}"
                )
            else:
                app_logger.error(
                    f"Failed to send report to backend: {response.status_code} - {response.text}"
                )
                raise Exception(f"Backend API returned status {response.status_code}")
                
    except httpx.TimeoutException:
        app_logger.error(f"Timeout when calling backend API for organization {organization_id}")
        raise
    except Exception as e:
        app_logger.error(f"Error calling backend API: {e}")
        raise