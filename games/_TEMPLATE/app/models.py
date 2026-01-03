from pydantic import BaseModel
from typing import Optional, Dict, Any

class GameState(BaseModel):
    """Current state of the game"""
    game_id: int  # This is the invite_code (6-digit number)
    player1_id: int
    player2_id: Optional[int] = None
    status: str  # "waiting", "playing", "finished"
    # Add your game-specific fields here
    
class GameAction(BaseModel):
    """Action a player takes in the game"""
    user_id: int
    game_id: int
    # Add action-specific fields here
    
class GameActionResponse(BaseModel):
    """Response from performing an action"""
    success: bool
    message: str
    new_state: Optional[GameState] = None
    # Add additional response fields as needed

class CreateGameRequest(BaseModel):
    """Request to create a new game"""
    player1_id: int

class JoinGameRequest(BaseModel):
    """Request to join a game"""
    player2_id: int
    game_id: int  # This is the invite_code (6-digit)

class FinishGameRequest(BaseModel):
    """Request to finish a game (optional)"""
    user_id: int
    game_id: int

