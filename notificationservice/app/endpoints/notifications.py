from fastapi import APIRouter, Depends, HTTPException
from app.models import NotificationCreate, NotificationResponse, NotificationRead
from typing import List
from datetime import datetime

router = APIRouter()

# In-memory storage for demo (should be replaced with database)
notifications_db = {}
notification_counter = 0

@router.post("/", response_model=NotificationResponse, status_code=201)
async def create_notification(notification: NotificationCreate):
    """Create a new notification"""
    global notification_counter
    notification_counter += 1
    
    new_notification = {
        "id": notification_counter,
        "user_id": notification.user_id,
        "notification_type": notification.notification_type,
        "title": notification.title,
        "message": notification.message,
        "data": notification.data,
        "created_at": datetime.now(),
        "read": False
    }
    notifications_db[notification_counter] = new_notification
    return new_notification

@router.get("/user/{user_id}", response_model=List[NotificationResponse])
async def get_user_notifications(user_id: int, unread_only: bool = False):
    """Get notifications for a user"""
    user_notifications = [
        n for n in notifications_db.values() 
        if n["user_id"] == user_id and (not unread_only or not n["read"])
    ]
    return sorted(user_notifications, key=lambda x: x["created_at"], reverse=True)

@router.post("/read", status_code=200)
async def mark_as_read(notification_read: NotificationRead):
    """Mark notification as read"""
    if notification_read.notification_id not in notifications_db:
        raise HTTPException(status_code=404, detail="Notification not found")
    notifications_db[notification_read.notification_id]["read"] = True
    return {"status": "success"}

@router.delete("/{notification_id}", status_code=204)
async def delete_notification(notification_id: int):
    """Delete a notification"""
    if notification_id not in notifications_db:
        raise HTTPException(status_code=404, detail="Notification not found")
    del notifications_db[notification_id]
    return None

