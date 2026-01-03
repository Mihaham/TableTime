from fastapi import FastAPI
from app.endpoints import game

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
    return {"status": "ok", "service": "rps"}

