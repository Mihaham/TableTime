from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class GameState(BaseModel):
    game_id: int
    players: List[Dict[str, Any]]
    board_state: Dict[str, Any]
    current_player: int
    turn_number: int

class GameAction(BaseModel):
    user_id: int
    game_id: int
    action_type: str
    action_data: Dict[str, Any]

class GameActionResponse(BaseModel):
    success: bool
    new_state: Optional[GameState] = None
    message: str

