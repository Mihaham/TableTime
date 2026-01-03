from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class GameCreationLog(BaseModel):
    game_id: int
    game_type: str
    creator_user_id: int
    invite_code: int
    created_at: Optional[datetime] = None

class GameJoinLog(BaseModel):
    game_id: int
    game_type: str
    user_id: int
    joined_at: Optional[datetime] = None

class GameActionLog(BaseModel):
    game_id: int
    game_type: str
    user_id: int
    action_type: str
    action_data: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

class GameFinishLog(BaseModel):
    game_id: int
    game_type: str
    finished_by_user_id: int
    winner_user_id: Optional[int] = None
    final_state: Optional[Dict[str, Any]] = None
    finished_at: Optional[datetime] = None

class GameEventLog(BaseModel):
    game_id: Optional[int] = None
    game_type: Optional[str] = None
    user_id: Optional[int] = None
    event_type: str
    event_message: Optional[str] = None
    event_data: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

# Request models
class LogCreationRequest(BaseModel):
    game_id: int
    game_type: str
    creator_user_id: int
    invite_code: int

class LogJoinRequest(BaseModel):
    game_id: int
    game_type: str
    user_id: int

class LogActionRequest(BaseModel):
    game_id: int
    game_type: str
    user_id: int
    action_type: str
    action_data: Optional[Dict[str, Any]] = None

class LogFinishRequest(BaseModel):
    game_id: int
    game_type: str
    finished_by_user_id: int
    winner_user_id: Optional[int] = None
    final_state: Optional[Dict[str, Any]] = None

class LogEventRequest(BaseModel):
    game_id: Optional[int] = None
    game_type: Optional[str] = None
    user_id: Optional[int] = None
    event_type: str
    event_message: Optional[str] = None
    event_data: Optional[Dict[str, Any]] = None

# Response models
class LogResponse(BaseModel):
    success: bool
    message: str
    log_id: Optional[int] = None

