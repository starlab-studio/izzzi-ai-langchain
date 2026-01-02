from typing import List
from langchain_openai import OpenAIEmbeddings
from tenacity import retry, stop_after_attempt, wait_exponential

from src.configs import get_settings
from src.core.logger import app_logger

settings = get_settings()

class EmbeddingService:
    """Service pour générer des embeddings via LangChain"""
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def embed_text(self, text: str) -> List[float]:
        """Génère un embedding pour un texte"""
        try:
            embedding = await self.embeddings.aembed_query(text)
            app_logger.debug(f"Generated embedding for text (length: {len(text)})")
            return embedding
        except Exception as e:
            app_logger.error(f"Error generating embedding: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Génère des embeddings en batch (plus efficace et moins cher)"""
        try:
            embeddings = await self.embeddings.aembed_documents(texts)
            app_logger.info(f"Generated {len(embeddings)} embeddings in batch")
            return embeddings
        except Exception as e:
            app_logger.error(f"Error generating batch embeddings: {e}")
            raise