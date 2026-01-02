from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class NotificationType(str, Enum):
    GAME_INVITE = "game_invite"
    GAME_START = "game_start"
    TURN_NOTIFICATION = "turn_notification"
    GAME_END = "game_end"
    SYSTEM = "system"

class NotificationCreate(BaseModel):
    user_id: int
    notification_type: NotificationType
    title: str
    message: str
    data: Optional[dict] = None

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    notification_type: NotificationType
    title: str
    message: str
    data: Optional[dict] = None
    created_at: datetime
    read: bool

class NotificationRead(BaseModel):
    notification_id: int

