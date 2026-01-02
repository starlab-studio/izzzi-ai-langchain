from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from src.core.logger import app_logger

class PostgresResponseRepository:
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_text_responses_by_subject(
        self,
        subject_id: UUID,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> List[dict]:
        filters = ["q.subject_id = :subject_id", "a.value_text IS NOT NULL"]
        params = {"subject_id": str(subject_id)}
        
        if period_start:
            filters.append("r.submitted_at >= :period_start")
            params["period_start"] = period_start
        
        if period_end:
            filters.append("r.submitted_at <= :period_end")
            params["period_end"] = period_end
        
        where_clause = " AND ".join(filters)
        
        query = text(f"""
            SELECT 
                a.id as answer_id,
                a.response_id,
                a.question_id,
                a.value_text,
                a.value_stars,
                r.submitted_at,
                q.id as quiz_id,
                q.type as quiz_type,
                qt.text as question_text,
                qt.category as question_category
            FROM answers a
            JOIN responses r ON r.id = a.response_id
            JOIN quizzes q ON q.id = r.quiz_id
            JOIN quiz_template_questions qt ON qt.id = a.question_id
            WHERE {where_clause}
            ORDER BY r.submitted_at DESC
        """)
        
        result = await self.session.execute(query, params)
        rows = result.fetchall()
        
        return [dict(row._mapping) for row in rows]
    
    async def get_star_ratings_by_subject(
        self,
        subject_id: UUID,
        question_category: Optional[str] = None,
    ) -> List[dict]:
        filters = ["q.subject_id = :subject_id", "a.value_stars IS NOT NULL"]
        params = {"subject_id": str(subject_id)}
        
        if question_category:
            filters.append("qt.category = :category")
            params["category"] = question_category
        
        where_clause = " AND ".join(filters)
        
        query = text(f"""
            SELECT 
                a.value_stars,
                qt.text as question_text,
                qt.category,
                COUNT(*) as count,
                AVG(a.value_stars) as average
            FROM answers a
            JOIN responses r ON r.id = a.response_id
            JOIN quizzes q ON q.id = r.quiz_id
            JOIN quiz_template_questions qt ON qt.id = a.question_id
            WHERE {where_clause}
            GROUP BY a.value_stars, qt.text, qt.category
            ORDER BY qt.category, a.value_stars
        """)
        
        result = await self.session.execute(query, params)
        return [dict(row._mapping) for row in result.fetchall()]
    
    async def get_response_count_by_subject(
        self,
        subject_id: UUID,
        period_days: int = 30
    ) -> int:
        query = text("""
            SELECT COUNT(DISTINCT r.id)
            FROM responses r
            JOIN quizzes q ON q.id = r.quiz_id
            WHERE q.subject_id = :subject_id
              AND r.submitted_at >= NOW() - INTERVAL ':days days'
        """)
        
        result = await self.session.execute(
            query, 
            {"subject_id": str(subject_id), "days": period_days}
        )
        return result.scalar() or 0