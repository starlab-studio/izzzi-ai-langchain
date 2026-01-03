from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
import hashlib

from src.application.facades.analysis_facade import AnalysisFacade
from src.domain.entities.insight import InsightType, InsightPriority
from src.core.logger import app_logger

class GenerateFeedbackAlertsUseCase:
    """Use case pour générer les alertes de feedback pour une matière"""
    
    def __init__(
        self,
        analysis_facade: AnalysisFacade,
    ):
        self.analysis_facade = analysis_facade
    
    async def execute(
        self,
        subject_id: UUID,
        period_days: int = 30,
        form_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Génère les alertes à partir des insights
        
        Args:
            subject_id: ID de la matière
            period_days: Période d'analyse
            form_type: Type de formulaire ("during_course" ou "after_course")
        
        Returns:
            Liste d'alertes formatées pour le frontend
        """
        log_msg = f"Generating feedback alerts for subject {subject_id}"
        if form_type:
            log_msg += f" (form_type: {form_type})"
        app_logger.info(log_msg)
        
        try:
            insights_data = await self.analysis_facade.generate_comprehensive_insights(
                subject_id=subject_id,
                period_days=period_days,
                form_type=form_type,
            )
        except Exception as e:
            app_logger.error(f"Error generating insights for alerts: {e}")
            return []
        
        all_insights = insights_data.get("insights", [])
        app_logger.info(
            f"Found {len(all_insights)} insights for subject {subject_id}, form_type: {form_type}"
        )
        
        alerts = []
        for idx, insight in enumerate(all_insights):
            priority = insight.get("priority", "")
            insight_type = insight.get("type", "")
            
            app_logger.info(
                f"Insight {idx}: type={insight_type}, priority={priority}, will generate alert: {priority in ['high', 'urgent'] and insight_type in ['alert', 'negative']}"
            )
            
            if priority in ["high", "urgent"] and insight_type in ["alert", "negative"]:
                evidence_list = insight.get("evidence", [])
                evidence_strings = []
                for ev in evidence_list:
                    if isinstance(ev, dict):
                        text = ev.get("text") or ev.get("example", "")
                        if text:
                            evidence_strings.append(text)
                    elif isinstance(ev, str):
                        evidence_strings.append(ev)
                
                title = insight.get("title", "")
                content = insight.get("content", "")
                content_hash = hashlib.md5(
                    f"{title}{content}{subject_id}".encode()
                ).hexdigest()[:8]
                timestamp_str = str(int(datetime.now().timestamp()))
                alert_id = f"alert_{subject_id}_{content_hash}_{timestamp_str}"
                
                alert_data = {
                    "id": alert_id,
                    "type": "negative" if insight_type == "negative" else "alert",
                    "number": f"Alerte {len(alerts) + 1}/{len([i for i in all_insights if i.get('priority') in ['high', 'urgent']])}",
                    "content": content,
                    "title": title,
                    "priority": priority,
                    "evidence": evidence_strings,
                    "timestamp": datetime.now().isoformat(),
                }
                
                if form_type:
                    alert_data["formType"] = form_type
                
                alerts.append(alert_data)
        
        app_logger.info(f"Generated {len(alerts)} alerts for subject {subject_id}")
        
        return alerts

