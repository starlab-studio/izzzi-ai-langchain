from typing import List, Dict, Any
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from src.configs import get_settings
from src.infrastructure.frameworks.tools import (
    SentimentAnalysisTool,
    SemanticSearchTool,
    ClusterAnalysisTool,
)
from src.core.logger import app_logger

settings = get_settings()

class TeacherAssistantAgent:
    """
    Agent LangChain qui aide les enseignants à analyser leurs retours
    
    L'agent peut :
    1. Analyser le sentiment général
    2. Rechercher des réponses spécifiques
    3. Identifier les thèmes récurrents
    4. Combiner plusieurs analyses pour répondre à des questions complexes
    """
    
    def __init__(
        self,
        sentiment_tool: SentimentAnalysisTool,
        search_tool: SemanticSearchTool,
        cluster_tool: ClusterAnalysisTool,
    ):
        self.tools = [sentiment_tool, search_tool, cluster_tool]
        
        # LLM pour l'agent
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0,  # Agent doit être déterministe
            openai_api_key=settings.OPENAI_API_KEY,
        )
        
        # Prompt système pour l'agent
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Tu es un assistant pédagogique intelligent qui aide les enseignants 
            à comprendre les retours de leurs élèves.

            Tu as accès à plusieurs outils :
            - analyze_subject_sentiment : Pour analyser le sentiment général
            - search_similar_responses : Pour chercher des réponses spécifiques
            - identify_themes : Pour identifier les thèmes récurrents

            Utilise ces outils de manière intelligente pour répondre aux questions.

            Principes :
            - Sois concis et actionnable
            - Cite des exemples concrets des retours d'élèves
            - Propose des actions spécifiques
            - Reste empathique et constructif
            - Réponds en français

            Si on te donne un subject_id, utilise-le pour tous les outils."""),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Créer l'agent
        self.agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt,
        )
        
        # Executor pour exécuter l'agent
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=5,
            handle_parsing_errors=True,
        )
    
    async def query(
        self,
        question: str,
        subject_id: str,
        context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Pose une question à l'agent
        
        Args:
            question: Question de l'enseignant
            subject_id: UUID de la matière
            context: Contexte additionnel (optionnel)
        
        Returns:
            {
                "answer": str,
                "tools_used": List[str],
                "intermediate_steps": List[dict],
            }
        """
        try:
            enriched_input = f"""Question : {question}

            Context :
            - subject_id : {subject_id}
            """
            
            if context:
                enriched_input += f"- Informations additionnelles : {context}\n"
            
            app_logger.info(f"Agent processing query: {question[:100]}...")
            
            # Exécuter l'agent
            result = await self.agent_executor.ainvoke({"input": enriched_input})
            
            # Extraire les outils utilisés
            tools_used = []
            for step in result.get("intermediate_steps", []):
                if hasattr(step[0], "tool"):
                    tools_used.append(step[0].tool)
            
            app_logger.info(f"Agent completed. Tools used: {tools_used}")
            
            return {
                "answer": result["output"],
                "tools_used": tools_used,
                "intermediate_steps": [
                    {
                        "tool": step[0].tool if hasattr(step[0], "tool") else None,
                        "input": step[0].tool_input if hasattr(step[0], "tool_input") else None,
                        "output": str(step[1])[:200],  # Truncate
                    }
                    for step in result.get("intermediate_steps", [])
                ],
            }
            
        except Exception as e:
            app_logger.error(f"Error in agent query: {e}")
            raise

class ReportGeneratorAgent:
    """
        Agent spécialisé dans la génération de rapports hebdomadaires
        
        Workflow :
        1. Analyse le sentiment de toutes les matières
        2. Identifie les matières qui nécessitent attention
        3. Pour chaque matière critique, cherche les détails
        4. Génère un rapport structuré
    """
    
    def __init__(
        self,
        sentiment_tool: SentimentAnalysisTool,
        search_tool: SemanticSearchTool,
        cluster_tool: ClusterAnalysisTool,
    ):
        self.tools = [sentiment_tool, search_tool, cluster_tool]
        
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0,
            openai_api_key=settings.OPENAI_API_KEY,
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", 
            """
                Tu es un analyste éducatif qui génère des rapports hebdomadaires.

                Ton workflow :
                1. Analyser le sentiment de chaque matière listée
                2. Identifier les matières avec problèmes (sentiment < -0.2 ou baisse > 15%)
                3. Pour chaque matière à problème, identifier les thèmes
                4. Générer un rapport structuré avec :
                - Vue d'ensemble
                - Matières qui vont bien (top 3)
                - Matières qui nécessitent attention (avec détails)
                - Recommandations prioritaires

                Sois factuel, précis, et actionnable.
            """),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        self.agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt,
        )
        
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=15,
        )
    
    async def generate_weekly_report(
        self,
        subject_ids: List[str],
        organization_name: str,
    ) -> str:
        """Génère un rapport hebdomadaire automatique"""
        input_text = f"""Génère un rapport hebdomadaire pour {organization_name}.

            Matières à analyser : {', '.join(subject_ids)}

            Pour chaque matière, utilise l'outil analyze_subject_sentiment.
            Ensuite, pour les matières avec des problèmes, utilise identify_themes pour comprendre les causes.

            Structure ton rapport en :
            1. Vue d'ensemble
            2. Top 3 des matières qui vont bien
            3. Matières qui nécessitent attention (avec détails et thèmes)
            4. Recommandations prioritaires pour la semaine prochaine
        """
        
        result = await self.agent_executor.ainvoke({"input": input_text})
        return result["output"]