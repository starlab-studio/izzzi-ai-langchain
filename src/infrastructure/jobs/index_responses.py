import asyncio
from typing import List, Dict, Any
from sqlalchemy import text
from celery import Task

from src.infrastructure.jobs.celery_app import celery_app
from src.infrastructure.database.connection import async_session_maker
from src.infrastructure.frameworks.embedding_service import EmbeddingService
from src.infrastructure.repositories.postgres_embedding_repository import (
    PostgresEmbeddingRepository
)
from src.domain.entities.embedding import ResponseEmbedding
from src.core.logger import app_logger
from uuid import uuid4

class IndexResponsesTask(Task):
    """Task avec state pour réutiliser les services"""
    _embedding_service = None
    
    @property
    def embedding_service(self):
        if self._embedding_service is None:
            self._embedding_service = EmbeddingService()
        return self._embedding_service

@celery_app.task(
    bind=True,
    base=IndexResponsesTask,
    name="src.infrastructure.jobs.index_responses.index_new_responses_task",
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
)
def index_new_responses_task(self, batch_size: int = 100):
    """
    Job Celery qui indexe les nouvelles réponses textuelles
    
    Workflow :
    1. Récupère les réponses non indexées (LIMIT batch_size)
    2. Génère les embeddings en batch
    3. Sauvegarde dans response_embeddings
    4. Log les résultats
    
    S'exécute toutes les heures via Celery Beat
    """
    try:
        app_logger.info(f"Starting indexing job (batch_size={batch_size})")
        
        # Exécuter la logique async
        result = asyncio.run(index_responses_async(batch_size))
        
        app_logger.info(f"Indexing job completed: {result}")
        return result
        
    except Exception as e:
        app_logger.error(f"Error in indexing job: {e}")
        raise self.retry(exc=e)

async def index_responses_async(batch_size: int) -> Dict[str, Any]:
    """Logique async d'indexation"""
    
    async with async_session_maker() as session:
        embedding_repo = PostgresEmbeddingRepository(session)
        embedding_service = EmbeddingService()
        
        # 1. Récupérer les réponses non indexées
        unindexed = await embedding_repo.get_unindexed_responses(limit=batch_size)
        
        if not unindexed:
            app_logger.info("No new responses to index")
            return {"indexed": 0, "skipped": 0, "errors": 0}
        
        app_logger.info(f"Found {len(unindexed)} responses to index")
        
        # 2. Préparer les textes pour batch embedding
        texts = [item['text_content'] for item in unindexed]
        
        # 3. Générer les embeddings en batch (plus efficace)
        try:
            embeddings = await embedding_service.embed_batch(texts)
        except Exception as e:
            app_logger.error(f"Error generating embeddings: {e}")
            return {"indexed": 0, "skipped": len(unindexed), "errors": len(unindexed)}
        
        # 4. Créer les entités et sauvegarder
        embedding_entities = []
        for item, embedding_vector in zip(unindexed, embeddings):
            entity = ResponseEmbedding(
                id=uuid4(),
                response_id=item['response_id'],
                answer_id=item['answer_id'],
                text_content=item['text_content'],
                embedding=embedding_vector,
                metadata={
                    'quiz_id': str(item['quiz_id']),
                    'subject_id': str(item['subject_id']),
                    'indexed_at': 'auto',
                }
            )
            embedding_entities.append(entity)
        
        # 5. Sauvegarder en batch
        indexed_count = await embedding_repo.save_batch(embedding_entities)
        
        # 6. Commit
        await session.commit()
        
        return {
            "indexed": indexed_count,
            "skipped": 0,
            "errors": 0,
            "batch_size": batch_size,
        }

@celery_app.task(
    name="src.infrastructure.jobs.index_responses.reindex_subject_task",
    max_retries=1,
)
def reindex_subject_task(subject_id: str):
    """
    Ré-indexe toutes les réponses d'une matière
    Utile après un changement de modèle d'embedding
    """
    try:
        app_logger.info(f"Reindexing subject {subject_id}")
        
        result = asyncio.run(reindex_subject_async(subject_id))
        
        app_logger.info(f"Reindexing completed: {result}")
        return result
        
    except Exception as e:
        app_logger.error(f"Error reindexing subject: {e}")
        raise

async def reindex_subject_async(subject_id: str) -> Dict[str, Any]:
    """Ré-indexation complète d'une matière"""
    
    async with async_session_maker() as session:
        # 1. Supprimer les anciens embeddings
        delete_query = text("""
            DELETE FROM response_embeddings re
            USING responses r, quizzes q
            WHERE re.response_id = r.id
              AND r.quiz_id = q.id
              AND q.subject_id = :subject_id
        """)
        
        await session.execute(delete_query, {"subject_id": subject_id})
        await session.commit()
        
        app_logger.info(f"Deleted old embeddings for subject {subject_id}")
        
        # 2. Ré-indexer
        # Les réponses sont maintenant "non indexées", le job normal les reprendra
        
        return {"subject_id": subject_id, "status": "queued_for_reindex"}