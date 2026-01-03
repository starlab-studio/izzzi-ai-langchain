from celery import Celery
from celery.schedules import crontab
from datetime import timedelta
from src.configs import get_settings

settings = get_settings()

celery_app = Celery(
    "izzzi-ai-tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "src.infrastructure.jobs.index_responses",
        "src.infrastructure.jobs.daily_analysis",
        "src.infrastructure.jobs.weekly_report",
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Paris",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    task_soft_time_limit=3000,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)

celery_app.conf.beat_schedule = {
    # Indexer les nouvelles réponses toutes les minutes (modifier pour toutes les heures en prod)
    "index-new-responses": {
        "task": "src.infrastructure.jobs.index_responses.index_new_responses_task",
        "schedule": timedelta(minutes=1),  # Toutes les minutes
    },
    
    # Analyse quotidienne à 6h du matin
    "daily-analysis": {
        "task": "src.infrastructure.jobs.daily_analysis.daily_analysis_task",
        "schedule": timedelta(minutes=1),
    },
    
    # Rapport hebdomadaire le lundi à 8h
    "weekly-report": {
        "task": "src.infrastructure.jobs.weekly_report.weekly_report_task",
        "schedule": crontab(day_of_week=1, hour=8, minute=0),
    },
}