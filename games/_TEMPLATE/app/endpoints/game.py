from fastapi import APIRouter, HTTPException
from app.models import (
    GameState,
    GameAction,
    GameActionResponse,
    CreateGameRequest,
    JoinGameRequest,
    FinishGameRequest  # Optional
)
from typing import Dict
import random

router = APIRouter()

# In-memory game storage (key is invite_code which is 6-digit number)
games: Dict[int, GameState] = {}

@router.post("/create", response_model=GameState)
async def create_game(request: CreateGameRequest):
    """Create a new game"""
    # Generate 6-digit invite code (same format as all games: 100000-999999)
    invite_code = random.randint(100000, 999999)
    
    # Ensure unique invite code
    while invite_code in games:
        invite_code = random.randint(100000, 999999)
    
    # Create game state
    game = GameState(
        game_id=invite_code,  # Use invite_code as game_id
        player1_id=request.player1_id,
        status="waiting"
        # Initialize your game-specific fields here
    )
    
    games[invite_code] = game
    return game

@router.post("/join", response_model=GameState)
async def join_game(request: JoinGameRequest):
    """Join an existing game"""
    if request.game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[request.game_id]
    
    # Validate game can be joined
    if game.player2_id is not None:
        raise HTTPException(status_code=400, detail="Game is already full")
    
    if game.player1_id == request.player2_id:
        raise HTTPException(status_code=400, detail="Player cannot join their own game")
    
    # Add player 2
    game.player2_id = request.player2_id
    game.status = "playing"
    
    return game

@router.post("/action", response_model=GameActionResponse)
async def perform_action(action: GameAction):
    """Perform a game action"""
    if action.game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[action.game_id]
    
    # Validate player is in the game
    if action.user_id not in [game.player1_id, game.player2_id]:
        raise HTTPException(status_code=403, detail="Player not in this game")
    
    # Validate game status
    if game.status != "playing":
        raise HTTPException(status_code=400, detail=f"Game is not in playing status. Current status: {game.status}")
    
    # TODO: Implement your game logic here
    
    return GameActionResponse(
        success=True,
        message="Action performed",
        new_state=game
    )

@router.get("/{game_id}/state", response_model=GameState)
async def get_game_state(game_id: int):
    """Get current game state"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    return games[game_id]

@router.get("/{game_id}/status")
async def get_game_status(game_id: int):
    """Get game status"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    game = games[game_id]
    return {
        "game_id": game_id,
        "status": game.status,
        "player1_id": game.player1_id,
        "player2_id": game.player2_id,
        # Add other status fields
    }

# Optional: Finish game endpoint
@router.post("/finish", response_model=GameState)
async def finish_game(request: FinishGameRequest):
    """Finish/end a game"""
    if request.game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[request.game_id]
    
    # Validate player is in the game
    if request.user_id not in [game.player1_id, game.player2_id]:
        raise HTTPException(status_code=403, detail="Player not in this game")
    
    # Set game status to finished
    game.status = "finished"
    
    return game

