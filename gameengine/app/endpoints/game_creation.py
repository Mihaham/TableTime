from fastapi import APIRouter, Depends, HTTPException
from app.models import GameCreate, GameResponse, JoinCreate
from app.dependencies import get_game_id
from app.GamesEngine.Games import GamesEngine
from app.error.error import AccessError, GameAmountError

router = APIRouter()

games = GamesEngine()

@router.post("/create/", response_model=GameResponse, status_code=201)
async def create_item(item: GameCreate):
    invite_code = games.create_game(user_id = item.user_id, name=item.game)
    return {"invite_code": invite_code}

@router.post("/join/", response_model=None)
async def read_all_items(item: JoinCreate):
    try:
        games.add_user(item.user_id, item.invite_code)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except GameAmountError as e:
        raise HTTPException(status_code=406, detail=str(e))