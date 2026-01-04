from fastapi import APIRouter, HTTPException
from app.models import (
    LogCreationRequest, LogJoinRequest, LogActionRequest, 
    LogFinishRequest, LogEventRequest, LogResponse
)
from app.database import Database
from typing import Optional
from loguru import logger
import asyncpg

router = APIRouter()

@router.post("/creation", response_model=LogResponse)
async def log_creation(request: LogCreationRequest):
    """Log a game creation event"""
    try:
        await Database.log_game_creation(
            request.game_id, request.game_type, 
            request.creator_user_id, request.invite_code
        )
        return LogResponse(success=True, message="Game creation logged successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log game creation: {str(e)}")

@router.post("/join", response_model=LogResponse)
async def log_join(request: LogJoinRequest):
    """Log a game join event"""
    try:
        await Database.log_game_join(
            request.game_id, request.game_type, request.user_id
        )
        return LogResponse(success=True, message="Game join logged successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log game join: {str(e)}")

@router.post("/action", response_model=LogResponse)
async def log_action(request: LogActionRequest):
    """Log a game action event"""
    try:
        await Database.log_game_action(
            request.game_id, request.game_type, request.user_id,
            request.action_type, request.action_data
        )
        return LogResponse(success=True, message="Game action logged successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log game action: {str(e)}")

@router.post("/finish", response_model=LogResponse)
async def log_finish(request: LogFinishRequest):
    """Log a game finish event"""
    try:
        await Database.log_game_finish(
            request.game_id, request.game_type, request.finished_by_user_id,
            request.winner_user_id, request.final_state
        )
        return LogResponse(success=True, message="Game finish logged successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log game finish: {str(e)}")

@router.post("/event", response_model=LogResponse)
async def log_event(request: LogEventRequest):
    """Log a general game event"""
    try:
        await Database.log_game_event(
            request.game_id, request.game_type, request.user_id,
            request.event_type, request.event_message, request.event_data
        )
        return LogResponse(success=True, message="Game event logged successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log game event: {str(e)}")

@router.get("/all")
async def get_all_logs(limit: int = 1000, offset: int = 0, game_type: Optional[str] = None):
    """Get all game logs (admin only). Default limit is 1000 to show all logs."""
    logger.info(f"Getting all logs: limit={limit}, offset={offset}, game_type={game_type}")
    try:
        logs = await Database.get_all_logs(limit=limit, offset=offset, game_type=game_type)
        logger.success(f"Retrieved {len(logs)} logs successfully")
        return {"logs": logs, "count": len(logs)}
    except Exception as e:
        logger.error(f"Failed to get logs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get logs: {str(e)}")

@router.get("/creation")
async def get_creation_logs(limit: int = 100, offset: int = 0, game_type: Optional[str] = None):
    """Get game creation logs"""
    try:
        pool = await Database.get_pool()
        async with pool.acquire() as conn:
            query = "SELECT * FROM game_creation_logs"
            params = []
            if game_type:
                query += " WHERE game_type = $1"
                params.append(game_type)
                query += " ORDER BY created_at DESC LIMIT $2 OFFSET $3"
                params.extend([limit, offset])
            else:
                query += " ORDER BY created_at DESC LIMIT $1 OFFSET $2"
                params.extend([limit, offset])
            
            rows = await conn.fetch(query, *params)
            return {"logs": [dict(row) for row in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get creation logs: {str(e)}")

@router.get("/join")
async def get_join_logs(limit: int = 100, offset: int = 0, game_type: Optional[str] = None):
    """Get game join logs"""
    try:
        pool = await Database.get_pool()
        async with pool.acquire() as conn:
            query = "SELECT * FROM game_join_logs"
            params = []
            if game_type:
                query += " WHERE game_type = $1"
                params.append(game_type)
                query += " ORDER BY joined_at DESC LIMIT $2 OFFSET $3"
                params.extend([limit, offset])
            else:
                query += " ORDER BY joined_at DESC LIMIT $1 OFFSET $2"
                params.extend([limit, offset])
            
            rows = await conn.fetch(query, *params)
            return {"logs": [dict(row) for row in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get join logs: {str(e)}")

@router.get("/action")
async def get_action_logs(limit: int = 100, offset: int = 0, game_type: Optional[str] = None):
    """Get game action logs"""
    try:
        pool = await Database.get_pool()
        async with pool.acquire() as conn:
            query = "SELECT * FROM game_action_logs"
            params = []
            if game_type:
                query += " WHERE game_type = $1"
                params.append(game_type)
                query += " ORDER BY created_at DESC LIMIT $2 OFFSET $3"
                params.extend([limit, offset])
            else:
                query += " ORDER BY created_at DESC LIMIT $1 OFFSET $2"
                params.extend([limit, offset])
            
            rows = await conn.fetch(query, *params)
            return {"logs": [dict(row) for row in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get action logs: {str(e)}")

@router.get("/finish")
async def get_finish_logs(limit: int = 100, offset: int = 0, game_type: Optional[str] = None):
    """Get game finish logs"""
    try:
        pool = await Database.get_pool()
        async with pool.acquire() as conn:
            query = "SELECT * FROM game_finish_logs"
            params = []
            if game_type:
                query += " WHERE game_type = $1"
                params.append(game_type)
                query += " ORDER BY finished_at DESC LIMIT $2 OFFSET $3"
                params.extend([limit, offset])
            else:
                query += " ORDER BY finished_at DESC LIMIT $1 OFFSET $2"
                params.extend([limit, offset])
            
            rows = await conn.fetch(query, *params)
            return {"logs": [dict(row) for row in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get finish logs: {str(e)}")
