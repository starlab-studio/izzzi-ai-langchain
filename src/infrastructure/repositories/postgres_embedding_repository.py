from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import json

from src.domain.entities.embedding import ResponseEmbedding
from src.domain.repositories.embedding_repository import IEmbeddingRepository
from src.infrastructure.models import ResponseEmbeddingModel
from src.core.logger import app_logger

class PostgresEmbeddingRepository(IEmbeddingRepository):
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save(self, embedding: ResponseEmbedding) -> ResponseEmbedding:
        model = ResponseEmbeddingModel(
            id=embedding.id,
            response_id=embedding.response_id,
            answer_id=embedding.answer_id,
            text_content=embedding.text_content,
            embedding=embedding.embedding,
            embedding_metadata=embedding.metadata,
        )
        
        self.session.add(model)
        await self.session.flush()
        
        app_logger.info(f"Saved embedding {embedding.id} for response {embedding.response_id}")
        return embedding
    
    async def save_batch(self, embeddings: List[ResponseEmbedding]) -> int:
        models = [
            ResponseEmbeddingModel(
                id=emb.id,
                response_id=emb.response_id,
                answer_id=emb.answer_id,
                text_content=emb.text_content,
                embedding=emb.embedding,
                embedding_metadata=emb.metadata,
            )
            for emb in embeddings
        ]
        
        self.session.add_all(models)
        await self.session.flush()
        
        app_logger.info(f"Saved batch of {len(embeddings)} embeddings")
        return len(embeddings)
    
    async def find_similar(
        self,
        query_embedding: List[float],
        subject_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None,
        limit: int = 20,
        similarity_threshold: float = 0.7,
    ) -> List[Tuple[ResponseEmbedding, float]]:
        """
        Recherche vectorielle avec pgvector
        Retourne (embedding, similarity_score)
        """
        filters = []
        params = {
            "limit": limit,
            "threshold": similarity_threshold,
        }
        
        joins = """
            FROM response_embeddings re
            JOIN responses r ON r.id = re.response_id
            JOIN quizzes q ON q.id = r.quiz_id
            JOIN subjects s ON s.id = q.subject_id
        """
        
        if subject_id:
            filters.append("s.id = :subject_id")
            params["subject_id"] = str(subject_id)
        
        if organization_id:
            filters.append("s.organization_id = :organization_id")
            params["organization_id"] = str(organization_id)
        
        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
        
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
        
        query_sql = f"""
            SELECT 
                re.id,
                re.response_id,
                re.answer_id,
                re.text_content,
                re.embedding,
                re.metadata as metadata,
                re.created_at,
                re.updated_at,
                1 - (re.embedding <=> '{embedding_str}'::vector) as similarity
            {joins}
            {where_clause}
            {"AND" if filters else "WHERE"} 1 - (re.embedding <=> '{embedding_str}'::vector) > :threshold
            ORDER BY re.embedding <=> '{embedding_str}'::vector
            LIMIT :limit
        """
        
        query = text(query_sql)
        
        app_logger.debug(f"Executing similarity search with {len(filters)} filters")
        
        result = await self.session.execute(query, params)
        rows = result.fetchall()
        
        app_logger.info(f"Found {len(rows)} similar embeddings")
        
        results = []
        for row in rows:
            # Parse embedding from PostgreSQL vector type
            # asyncpg returns vectors as strings like "[0.1, 0.2, 0.3, ...]"
            if isinstance(row.embedding, str):
                # Parse the string representation
                embedding_list = json.loads(row.embedding)
            elif isinstance(row.embedding, (list, tuple)):
                embedding_list = list(row.embedding)
            else:
                # Fallback: try to convert to list
                try:
                    embedding_list = list(row.embedding)
                except (TypeError, ValueError) as e:
                    app_logger.error(
                        f"Failed to parse embedding for row {row.id}: {type(row.embedding)} - {e}"
                    )
                    # Use zero vector as fallback
                    embedding_list = [0.0] * 1536
            
            results.append((
                ResponseEmbedding(
                    id=row.id,
                    response_id=row.response_id,
                    answer_id=row.answer_id,
                    text_content=row.text_content,
                    embedding=embedding_list,
                    metadata=row.metadata or {},
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                ),
                float(row.similarity)
            ))
        
        return results
    
    async def get_unindexed_responses(
        self,
        limit: int = 1000
    ) -> List[dict]:
        query = text("""
            SELECT 
                a.id as answer_id,
                a.response_id,
                a.value_text as text_content,
                r.quiz_id,
                q.subject_id
            FROM answers a
            JOIN responses r ON r.id = a.response_id
            JOIN quizzes q ON q.id = r.quiz_id
            LEFT JOIN response_embeddings re ON re.answer_id = a.id
            WHERE a.value_text IS NOT NULL 
              AND a.value_text != ''
              AND CHAR_LENGTH(a.value_text) > 10
              AND re.id IS NULL
            ORDER BY a.created_at DESC
            LIMIT :limit
        """)
        
        result = await self.session.execute(query, {"limit": limit})
        rows = result.fetchall()
        
        return [
            {
                "answer_id": row.answer_id,
                "response_id": row.response_id,
                "text_content": row.text_content,
                "quiz_id": row.quiz_id,
                "subject_id": row.subject_id,
            }
            for row in rows
        ]
    
    async def count_by_subject(self, subject_id: UUID) -> int:
        query = text("""
            SELECT COUNT(*)
            FROM response_embeddings re
            JOIN responses r ON r.id = re.response_id
            JOIN quizzes q ON q.id = r.quiz_id
            WHERE q.subject_id = :subject_id
        """)
        
        result = await self.session.execute(query, {"subject_id": str(subject_id)})
        return result.scalar()