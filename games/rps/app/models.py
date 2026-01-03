from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from enum import Enum

class Choice(str, Enum):
    ROCK = "rock"
    PAPER = "paper"
    SCISSORS = "scissors"

class GameState(BaseModel):
    game_id: int
    player1_id: int
    player2_id: Optional[int] = None
    player1_choice: Optional[Choice] = None
    player2_choice: Optional[Choice] = None
    player1_score: int = 0
    player2_score: int = 0
    round_number: int = 0
    status: str  # "waiting", "playing", "finished"
    winner: Optional[int] = None
    last_round_winner: Optional[int] = None

class GameAction(BaseModel):
    user_id: int
    game_id: int
    choice: Choice

class GameActionResponse(BaseModel):
    success: bool
    message: str
    new_state: Optional[GameState] = None
    round_result: Optional[str] = None

class FinishGameRequest(BaseModel):
    user_id: int
    game_id: int

class CreateGameRequest(BaseModel):
    player1_id: int

class JoinGameRequest(BaseModel):
    player2_id: int
    game_id: int

