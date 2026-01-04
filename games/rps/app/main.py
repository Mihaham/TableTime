from fastapi import FastAPI
from app.endpoints import game
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

app = FastAPI(
    title="Rock Paper Scissors Game Service",
    version="0.1.0",
    description="Microservice for Rock Paper Scissors game logic"
)

app.include_router(
    game.router,
    prefix="/api/v1/rps",
    tags=["rps"]
)

@app.get("/health")
async def health_check():
    logger.info("Health check requested")
    return {"status": "ok", "service": "rps"}
