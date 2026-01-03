from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from src.configs import get_settings

settings = get_settings()

# Engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
)

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()

async def get_db_session() -> AsyncSession:
    """Dependency pour obtenir une session DB"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

def create_celery_session_maker():
    """
    Crée un nouveau engine et session maker pour les tâches Celery.
    Chaque appel asyncio.run() dans Celery a besoin de son propre engine
    pour éviter les conflits d'event loop.
    """
    celery_engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
    )
    
    session_maker = async_sessionmaker(
        celery_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    return celery_engine, session_maker