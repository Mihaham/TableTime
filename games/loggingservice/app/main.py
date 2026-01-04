from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.endpoints import logs
from app.database import Database
from loguru import logger
import sys

# Configure loguru
logger.remove()  # Remove default handler
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
    colorize=True
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Logging Service starting up...")
    yield
    # Shutdown
    logger.info("Logging Service shutting down...")
    await Database.close_pool()

app = FastAPI(
    title="Logging Service",
    version="0.1.0",
    description="Microservice for game logging",
    lifespan=lifespan
)

app.include_router(
    logs.router,
    prefix="/api/v1/logs",
    tags=["logs"]
)

@app.get("/health")
async def health_check():
    logger.info("Health check requested")
    try:
        # Test database connection
        pool = await Database.get_pool()
        return {"status": "ok", "service": "loggingservice", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "error", "service": "loggingservice", "error": str(e)}
