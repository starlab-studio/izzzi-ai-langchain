from loguru import logger
import sys
from src.configs import get_settings

settings = get_settings()

def setup_logger():
    """Configure loguru"""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=settings.LOG_LEVEL,
        colorize=True,
    )
    
    # Logging file in production
    if settings.ENVIRONMENT == "production":
        logger.add(
            "logs/ai_service_{time}.log",
            rotation="500 MB",
            retention="10 days",
            level="INFO",
        )
    
    return logger

app_logger = setup_logger()