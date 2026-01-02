from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    telegram_id: Optional[int] = None
    email: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    telegram_id: Optional[int] = None
    email: Optional[str] = None
    created_at: datetime
    is_active: bool

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None

