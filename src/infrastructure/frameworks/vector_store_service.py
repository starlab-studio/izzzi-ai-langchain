from typing import List, Optional, Tuple
from uuid import UUID
from langchain_postgres import PGVector
from langchain_core.documents import Document

from src.configs import get_settings
from src.infrastructure.frameworks.embedding_service import EmbeddingService

settings = get_settings()

class VectorStoreService:
    """Service pour interagir avec pgvector via LangChain"""
    
    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service
        
        # LangChain PGVector store
        self.vector_store = PGVector(
            connection_string=settings.DATABASE_URL.replace('+asyncpg', ''),
            embedding_function=embedding_service.embeddings,
            collection_name="response_embeddings",
            use_jsonb=True,
        )
    
    async def add_documents(
        self,
        texts: List[str],
        metadatas: List[dict],
    ) -> List[str]:
        """Ajoute des documents au vector store"""
        documents = [
            Document(page_content=text, metadata=metadata)
            for text, metadata in zip(texts, metadatas)
        ]
        
        ids = await self.vector_store.aadd_documents(documents)
        return ids
    
    async def similarity_search(
        self,
        query: str,
        k: int = 10,
        filter: Optional[dict] = None,
    ) -> List[Tuple[Document, float]]:
        """Recherche de similarité"""
        results = await self.vector_store.asimilarity_search_with_score(
            query,
            k=k,
            filter=filter,
        )
        return results
    
    async def max_marginal_relevance_search(
        self,
        query: str,
        k: int = 10,
        fetch_k: int = 50,
        lambda_mult: float = 0.5,
    ) -> List[Document]:
        """
        MMR search pour diversité des résultats
        Évite les documents trop similaires entre eux
        """
        results = await self.vector_store.amax_marginal_relevance_search(
            query,
            k=k,
            fetch_k=fetch_k,
            lambda_mult=lambda_mult,
        )
        return results