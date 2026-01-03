from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from functools import lru_cache
from typing import List, Union
import json

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        env_parse_none_str="",
        extra="ignore",
    )
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, v):
        """Parse DEBUG from string to boolean"""
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return bool(v)
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    # JWT (⭐ identique NestJS)
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    
    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: Union[str, List[str]] = Field(
        default=["http://localhost:3000"],
        description="List of allowed CORS origins. Can be set as JSON array or comma-separated in .env file."
    )
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if v is None or v == "":
            return ["http://localhost:3000"]
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            # Try to parse as JSON first
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
                return [parsed] if parsed else ["http://localhost:3000"]
            except (json.JSONDecodeError, ValueError):
                # If not JSON, try comma-separated values
                origins = [origin.strip() for origin in v.split(",") if origin.strip()]
                return origins if origins else ["http://localhost:3000"]
        return v
    
    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def ensure_list(cls, v):
        if isinstance(v, str):
            return [v]
        return v if isinstance(v, list) else ["http://localhost:3000"]
    
    # Service
    SERVICE_NAME: str = "izzzi-ai-service"
    SERVICE_PORT: int = 8000
    
    # Backend API (for report submission)
    BACKEND_URL: str = "http://localhost:3000"

@lru_cache()
def get_settings() -> Settings:
    return Settings()