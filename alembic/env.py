from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import asyncio
from sqlalchemy.ext.asyncio import AsyncEngine

from src.configs import get_settings
from src.infrastructure.database.connection import Base

# Import all models so they are registered in Base.metadata
from src.infrastructure.models import (
    AnalysisCacheModel,
    ChatbotConversationModel,
    InsightModel,
    ResponseEmbeddingModel,
    SubjectAnalysisModel,
)

config = context.config
settings = get_settings()

# Override sqlalchemy.url with our settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Tables gérées par le projet langchain (ne pas exclure)
LANGCHAIN_TABLES = {
    'chatbot_conversations',
    'insights',
    'subject_analyses',
    'response_embeddings',
    'analysis_cache',
}

def include_object(object, name, type_, reflected, compare_to):
    """
    Exclut toutes les tables qui ne sont pas gérées par le projet langchain.
    Cela évite qu'Alembic ne génère des drop_table pour les tables du backend NestJS.
    """
    if type_ == "table":
        # Inclure uniquement les tables du projet langchain
        return name in LANGCHAIN_TABLES
    # Inclure tous les autres objets (indexes, constraints, etc.) pour les tables langchain
    return True

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = AsyncEngine(
        engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            future=True,
        )
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())