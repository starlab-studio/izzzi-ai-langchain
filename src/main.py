from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from src.configs import get_settings
from src.core.logger import setup_logger
from src.interface.controllers.v1 import analysis, chatbot, search, feedback
from src.interface.middlewares.error_handler import add_exception_handlers, LoggingMiddleware

settings = get_settings()
logger = setup_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management"""
    # Startup
    logger.info(f"Starting {settings.SERVICE_NAME}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # TODO: Initialize database connection pool
    # TODO: Warm up ML models if needed
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI service")
    # TODO: Close database connections
    # TODO: Cleanup resources

# Create FastAPI app
app = FastAPI(
    title="Izzzi AI Analysis Service",
    description="Microservice d'analyse IA des retours élèves avec LangChain",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Logging middleware (pour déboguer les headers)
app.add_middleware(LoggingMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Exception handlers
add_exception_handlers(app)

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
    }

# Include routers
app.include_router(analysis.router, prefix=settings.API_V1_PREFIX)
app.include_router(chatbot.router, prefix=settings.API_V1_PREFIX)
app.include_router(search.router, prefix=settings.API_V1_PREFIX)
app.include_router(feedback.router, prefix=settings.API_V1_PREFIX)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )