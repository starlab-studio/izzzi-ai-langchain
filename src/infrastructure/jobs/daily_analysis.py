import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy import text

from src.infrastructure.jobs.celery_app import celery_app
from src.infrastructure.database.connection import async_session_maker
from src.infrastructure.repositories.postgres_response_repository import (
    PostgresResponseRepository
)
from src.application.facades.analysis_facade import AnalysisFacade
from src.core.logger import app_logger
from uuid import UUID

@celery_app.task(
    name="src.infrastructure.jobs.daily_analysis.daily_analysis_task",
    max_retries=2,
)
def daily_analysis_task():
    """
    Analyse quotidienne automatique
    
    Workflow :
    1. Identifier toutes les matières actives
    2. Pour chaque matière avec des nouvelles réponses (dernières 24h)
    3. Lancer l'analyse de sentiment
    4. Détecter les alertes (sentiment négatif, baisse)
    5. Notifier si nécessaire
    
    S'exécute tous les jours à 6h du matin
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
    """Logique async de l'analyse quotidienne"""
    
    async with async_session_maker() as session:
        query = text("""
            SELECT DISTINCT 
                s.id as subject_id,
                s.name as subject_name,
                s.organization_id,
                COUNT(DISTINCT r.id) as response_count
            FROM subjects s
            JOIN quizzes q ON q.subject_id = s.id
            JOIN responses r ON r.quiz_id = q.id
            WHERE r.submitted_at >= NOW() - INTERVAL '24 hours'
              AND s.is_active = true
            GROUP BY s.id, s.name, s.organization_id
            HAVING COUNT(DISTINCT r.id) >= 3
            ORDER BY response_count DESC
        """)
        
        result = await session.execute(query)
        subjects = result.fetchall()
        
        if not subjects:
            app_logger.info("No active subjects with recent responses")
            return {"subjects_analyzed": 0, "alerts": 0}
        
        app_logger.info(f"Found {len(subjects)} subjects to analyze")
        
        # 2. Pour chaque matière, lancer l'analyse
        # (Simplifié : en production, utiliser get_analysis_facade avec DI)
        analyzed_count = 0
        alerts_count = 0
        alerts = []
        
        for subject in subjects:
            try:
                # Créer le facade (simplifié)
                # En prod: injecter les dépendances correctement
                facade = await create_facade_for_analysis(session)
                
                # Analyser
                analysis = await facade.analyze_subject_sentiment(
                    subject_id=UUID(str(subject.subject_id)),
                    period_days=7,  # Dernière semaine
                )
                
                analyzed_count += 1
                
                # Détecter les alertes
                if analysis['overall_score'] < -0.3:
                    alerts_count += 1
                    alerts.append({
                        'subject_id': str(subject.subject_id),
                        'subject_name': subject.subject_name,
                        'organization_id': str(subject.organization_id),
                        'alert_type': 'negative_sentiment',
                        'score': analysis['overall_score'],
                        'message': f"Sentiment négatif détecté pour {subject.subject_name}",
                    })
                
                if analysis.get('trend_percentage') and analysis['trend_percentage'] < -15:
                    alerts_count += 1
                    alerts.append({
                        'subject_id': str(subject.subject_id),
                        'subject_name': subject.subject_name,
                        'organization_id': str(subject.organization_id),
                        'alert_type': 'negative_trend',
                        'trend': analysis['trend_percentage'],
                        'message': f"Baisse de {abs(analysis['trend_percentage']):.0f}% pour {subject.subject_name}",
                    })
                
                # Sauvegarder l'analyse en cache
                await save_analysis_to_cache(session, analysis)
                
            except Exception as e:
                app_logger.error(f"Error analyzing subject {subject.subject_id}: {e}")
                continue
        
        # 3. Envoyer les notifications si alertes
        if alerts:
            await send_alert_notifications(alerts)
        
        await session.commit()
        
        return {
            "subjects_analyzed": analyzed_count,
            "alerts": alerts_count,
            "alert_details": alerts,
            "timestamp": datetime.now().isoformat(),
        }

async def create_facade_for_analysis(session) -> AnalysisFacade:
    """Helper pour créer le facade (simplifié)"""
    # TODO: Implémenter avec injection de dépendances correcte
    from src.infrastructure.database.repositories.postgres_embedding_repository import (
        PostgresEmbeddingRepository
    )
    from src.infrastructure.ml.embedding_service import EmbeddingService
    from src.infrastructure.llm.langchain_service import LangChainService
    from src.application.use_cases.analyze_subject_sentiment import (
        AnalyzeSubjectSentimentUseCase
    )
    # ... (créer tous les use cases)
    
    # Placeholder
    raise NotImplementedError("Implement DI for facade in jobs")

async def save_analysis_to_cache(session, analysis: Dict[str, Any]):
    """Sauvegarde l'analyse dans la table analysis_cache"""
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

async def send_alert_notifications(alerts: List[Dict[str, Any]]):
    """Envoie des notifications pour les alertes"""
    # TODO: Intégrer avec le module Notification de NestJS
    # Via API call ou message queue
    app_logger.info(f"Sending {len(alerts)} alert notifications")
    
    # Placeholder
    for alert in alerts:
        app_logger.warning(f"ALERT: {alert['message']}")