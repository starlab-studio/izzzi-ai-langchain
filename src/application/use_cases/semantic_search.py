from typing import List, Dict, Any
from uuid import UUID

from src.domain.repositories.embedding_repository import IEmbeddingRepository
from src.infrastructure.frameworks.embedding_service import EmbeddingService
from src.core.logger import app_logger

class SemanticSearchUseCase:
    """Use case pour recherche sémantique dans les réponses"""
    
    def __init__(
        self,
        embedding_repo: IEmbeddingRepository,
        embedding_service: EmbeddingService,
    ):
        self.embedding_repo = embedding_repo
        self.embedding_service = embedding_service
    
    async def execute(
        self,
        query: str,
        subject_id: UUID,
        limit: int = 20,
        similarity_threshold: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """
        Recherche sémantique dans les réponses
        
        Args:
            query: Question ou texte de recherche
            subject_id: Limiter à une matière
            limit: Nombre max de résultats
            similarity_threshold: Seuil de similarité (0-1)
        
        Returns:
            Liste de {text, similarity, metadata}
        """
        app_logger.info(f"Semantic search: '{query[:50]}...' in subject {subject_id}")
        
        query_embedding = await self.embedding_service.embed_text(query)
        
        results = await self.embedding_repo.find_similar(
            query_embedding=query_embedding,
            subject_id=subject_id,
            limit=limit,
            similarity_threshold=similarity_threshold,
        )
        
        formatted_results = [
            {
                "text": embedding.text_content,
                "similarity": similarity,
                "response_id": str(embedding.response_id),
                "answer_id": str(embedding.answer_id) if embedding.answer_id else None,
                "metadata": embedding.metadata,
                "created_at": embedding.created_at.isoformat(),
            }
            for embedding, similarity in results
        ]
        
        app_logger.info(f"Found {len(formatted_results)} similar responses")
        
        return formatted_results