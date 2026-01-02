from fastapi import FastAPI
from app.endpoints import game

app = FastAPI(
    title="Monopoly Game Service",
    version="0.1.0",
    description="Microservice for Monopoly game logic"
)

app.include_router(
    game.router,
    prefix="/api/v1/monopoly",
    tags=["monopoly"]
)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "monopoly"}

