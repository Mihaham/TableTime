from fastapi import APIRouter, Depends, HTTPException
from app.models import UserCreate, UserResponse, UserUpdate
from typing import List

router = APIRouter()

# In-memory storage for demo (should be replaced with database)
users_db = {}
user_counter = 0

@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(user: UserCreate):
    """Create a new user"""
    global user_counter
    user_counter += 1
    from datetime import datetime
    
    new_user = {
        "id": user_counter,
        "username": user.username,
        "telegram_id": user.telegram_id,
        "email": user.email,
        "created_at": datetime.now(),
        "is_active": True
    }
    users_db[user_counter] = new_user
    return new_user

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    """Get user by ID"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return users_db[user_id]

@router.get("/", response_model=List[UserResponse])
async def list_users(skip: int = 0, limit: int = 100):
    """List all users"""
    return list(users_db.values())[skip:skip+limit]

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_update: UserUpdate):
    """Update user information"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = users_db[user_id]
    if user_update.username is not None:
        user["username"] = user_update.username
    if user_update.email is not None:
        user["email"] = user_update.email
    if user_update.is_active is not None:
        user["is_active"] = user_update.is_active
    
    return user

@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: int):
    """Delete a user"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    del users_db[user_id]
    return None

