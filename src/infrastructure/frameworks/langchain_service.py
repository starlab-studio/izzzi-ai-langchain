from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough

from src.configs import get_settings
from src.infrastructure.frameworks.prompt_templates import (
    SENTIMENT_ANALYSIS_PROMPT,
    TOPIC_EXTRACTION_PROMPT,
    INSIGHTS_GENERATION_PROMPT,
    CHATBOT_RAG_PROMPT,
)
from src.core.logger import app_logger

settings = get_settings()

class LangChainService:
    """Service pour orchestration LLM via LangChain"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0.7,
            openai_api_key=settings.OPENAI_API_KEY,
        )
        
        self.json_parser = JsonOutputParser()
    
    async def analyze_sentiment(
        self,
        subject_name: str,
        responses: List[str],
    ) -> Dict[str, Any]:
        """Analyse de sentiment avec LLM"""
        chain = (
            SENTIMENT_ANALYSIS_PROMPT
            | self.llm
            | self.json_parser
        )
        
        try:
            result = await chain.ainvoke({
                "subject_name": subject_name,
                "responses": "\n\n".join([f"- {r}" for r in responses[:50]]),
            })
            
            app_logger.info(f"Sentiment analysis completed for {subject_name}")
            return result
        except Exception as e:
            app_logger.error(f"Error in sentiment analysis: {e}")
            raise
    
    async def extract_topics(
        self,
        responses: List[str],
    ) -> Dict[str, Any]:
        """Extraction de thèmes via LLM"""
        chain = (
            TOPIC_EXTRACTION_PROMPT
            | self.llm
            | self.json_parser
        )
        
        try:
            result = await chain.ainvoke({
                "responses": "\n\n".join([f"- {r}" for r in responses[:50]]),
            })
            
            app_logger.info(f"Topic extraction completed")
            return result
        except Exception as e:
            app_logger.error(f"Error in topic extraction: {e}")
            raise
    
    async def generate_insights(
        self,
        subject_name: str,
        instructor_name: str,
        period: str,
        response_count: int,
        sentiment_analysis: Dict[str, Any],
        topics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Génération d'insights actionnables"""
        chain = (
            INSIGHTS_GENERATION_PROMPT
            | self.llm
            | self.json_parser
        )
        
        try:
            result = await chain.ainvoke({
                "subject_name": subject_name,
                "instructor_name": instructor_name,
                "period": period,
                "response_count": response_count,
                "sentiment_analysis": str(sentiment_analysis),
                "topics": str(topics),
            })
            
            app_logger.info(f"Insights generated for {subject_name}")
            return result
        except Exception as e:
            app_logger.error(f"Error generating insights: {e}")
            raise
    
    async def chatbot_query(
        self,
        query: str,
        subject_name: str,
        instructor_name: str,
        context: List[str],
    ) -> str:
        """Répond à une question via RAG"""
        chain = (
            CHATBOT_RAG_PROMPT
            | self.llm
        )
        
        try:
            result = await chain.ainvoke({
                "query": query,
                "subject_name": subject_name,
                "instructor_name": instructor_name,
                "context": "\n\n".join([f"Élève: {c}" for c in context]),
            })
            
            app_logger.info(f"Chatbot query processed: {query[:50]}...")
            return result.content
        except Exception as e:
            app_logger.error(f"Error in chatbot query: {e}")
            raise