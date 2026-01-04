from pydantic import BaseModel
from typing import Optional, Dict, List

class GameState(BaseModel):
    """Current state of the monopoly game"""
    game_id: int  # This is the invite_code (6-digit number)
    player1_id: int
    player2_id: Optional[int] = None
    player3_id: Optional[int] = None
    status: str  # "waiting", "playing", "finished"
    current_turn: Optional[int] = None  # Player number whose turn it is (1, 2, or 3)
    board_size: int = 20  # Simplified board with 20 spaces (0-19)
    
    # Player data
    player_positions: Dict[int, int] = {}  # player_id -> position (0-19)
    player_money: Dict[int, int] = {}  # player_id -> money amount
    player_properties: Dict[int, List[int]] = {}  # player_id -> list of property positions
    
    # Property ownership: position -> owner_id (None if unowned)
    property_owners: Dict[int, Optional[int]] = {}
    
    # Last dice roll
    last_dice_roll: Optional[int] = None
    
    # Game state
    winner_id: Optional[int] = None

class CreateGameRequest(BaseModel):
    """Request to create a new game"""
    player1_id: int

class JoinGameRequest(BaseModel):
    """Request to join a game"""
    player_id: int
    game_id: int  # This is the invite_code (6-digit)

class RollDiceRequest(BaseModel):
    """Request to roll dice"""
    user_id: int
    game_id: int

class BuyPropertyRequest(BaseModel):
    """Request to buy a property"""
    user_id: int
    game_id: int

class EndTurnRequest(BaseModel):
    """Request to end turn"""
    user_id: int
    game_id: int

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
    property_cost: Optional[int] = None
    rent_paid: Optional[int] = None
    can_buy: Optional[bool] = None
