from fastapi import APIRouter, Depends, HTTPException
from app.models import GameCreate, GameResponse, JoinCreate, InputItem, UserItem
from app.dependencies import get_game_id
from app.GamesEngine.Games import GamesEngine
from app.error.error import AccessError, GameAmountError, IsNotConnectedError, NotHostError

router = APIRouter()

games = GamesEngine()

@router.post("/create/", response_model=GameResponse, status_code=201)
async def create_game(item: GameCreate):
    invite_code = games.create_game(user_id = item.user_id, name=item.game)
    return {"invite_code": invite_code}

@router.post("/join/", response_model=list[int])
async def join_game(item: JoinCreate):
    try:
        games.add_user(item.user_id, item.invite_code)
        ids = games.get_user_ids(user_id = item.user_id)
        ids.remove(item.user_id)
        return ids
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except GameAmountError as e:
        raise HTTPException(status_code=406, detail=str(e))

@router.post("/start/", response_model=list[int])
async def start_game(item: InputItem):
    try:
        return games.start_game(item.user_id)
    except IsNotConnectedError:
        raise HTTPException(status_code=404, detail="Not connected")
    except NotHostError:
        raise HTTPException(status_code=406, detail="Not host")