from fastapi import FastAPI, Depends
from app.endpoints import game_creation

app = FastAPI(
    title="GameEngine",
    version="0.1.0"
)

app.include_router(
    game_creation.router,
    prefix="/api/v1",
    tags=["game"]
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}