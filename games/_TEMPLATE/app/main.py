from fastapi import FastAPI
from app.endpoints import game

# TODO: Replace "your_game_name" with your actual game name (lowercase, no spaces)
GAME_NAME = "your_game_name"
GAME_TITLE = "Your Game Name Service"

app = FastAPI(
    title=GAME_TITLE,
    version="0.1.0",
    description=f"Microservice for {GAME_TITLE} game logic"
)

app.include_router(
    game.router,
    prefix=f"/api/v1/{GAME_NAME}",
    tags=[GAME_NAME]
)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": GAME_NAME}

