from fastapi import APIRouter, Depends, HTTPException
from app.models import GameCreate, GameResponse
from app.dependencies import get_game_id()

router = APIRouter()

Games = GamesEngine()

@router.post("/create/", response_model=GameResponse, status_code=201)
async def create_item(item: GameCreate):
    game_id = get_game_id()
    db_item = {
        "id": game_id,
        **item.dict()
    }
    Games.create(db_item)
    fake_db[current_id] = db_item
    current_id += 1
    return db_item

@router.get("/items/", response_model=list[ItemResponse])
async def read_all_items():
    return list(fake_db.values())