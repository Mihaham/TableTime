from pydantic import BaseModel
from typing import Optional, Dict, List

class PlayerPosition(BaseModel):
    """Player position on the board"""
    player_id: int
    position: int  # Current position on the board (0-100 or similar)

class GameState(BaseModel):
    """Current state of the dice and ladders game"""
    game_id: int  # This is the invite_code (6-digit number)
    player1_id: int
    player2_id: Optional[int] = None
    player3_id: Optional[int] = None
    status: str  # "waiting", "playing", "finished"
    current_turn: Optional[int] = None  # Player number whose turn it is (1, 2, or 3)
    board_size: int = 100  # Board size (0 to 100)
    player_positions: Dict[int, int] = {}  # player_id -> position
    last_dice_roll: Optional[int] = None  # Last dice roll value
    winner_id: Optional[int] = None

class RollDiceRequest(BaseModel):
    """Request to roll dice"""
    user_id: int
    game_id: int

class MoveRequest(BaseModel):
    """Request to move after dice roll"""
    user_id: int
    game_id: int

class CreateGameRequest(BaseModel):
    """Request to create a new game"""
    player1_id: int

class JoinGameRequest(BaseModel):
    """Request to join a game"""
    player_id: int
    game_id: int  # This is the invite_code (6-digit)

class FinishGameRequest(BaseModel):
    """Request to finish a game"""
    user_id: int
    game_id: int

class GameActionResponse(BaseModel):
    """Response from performing an action"""
    success: bool
    message: str
    new_state: Optional[GameState] = None
    dice_roll: Optional[int] = None
    new_position: Optional[int] = None
    ladder_used: Optional[bool] = None
    ladder_delta: Optional[int] = None

