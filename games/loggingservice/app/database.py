import asyncpg
from app.config import DATABASE_URL
from typing import Optional, List, Dict, Any
from datetime import datetime

class Database:
    _pool: Optional[asyncpg.Pool] = None

    @classmethod
    async def get_pool(cls):
        if cls._pool is None:
            cls._pool = await asyncpg.create_pool(DATABASE_URL)
        return cls._pool

    @classmethod
    async def close_pool(cls):
        if cls._pool:
            await cls._pool.close()
            cls._pool = None

    @classmethod
    async def log_game_creation(cls, game_id: int, game_type: str, creator_user_id: int, invite_code: int):
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO game_creation_logs (game_id, game_type, creator_user_id, invite_code)
                VALUES ($1, $2, $3, $4)
                """,
                game_id, game_type, creator_user_id, invite_code
            )

    @classmethod
    async def log_game_join(cls, game_id: int, game_type: str, user_id: int):
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO game_join_logs (game_id, game_type, user_id)
                VALUES ($1, $2, $3)
                """,
                game_id, game_type, user_id
            )

    @classmethod
    async def log_game_action(cls, game_id: int, game_type: str, user_id: int, action_type: str, action_data: Optional[Dict[str, Any]] = None):
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            import json
            await conn.execute(
                """
                INSERT INTO game_action_logs (game_id, game_type, user_id, action_type, action_data)
                VALUES ($1, $2, $3, $4, $5)
                """,
                game_id, game_type, user_id, action_type, json.dumps(action_data) if action_data else None
            )

    @classmethod
    async def log_game_finish(cls, game_id: int, game_type: str, finished_by_user_id: int, 
                              winner_user_id: Optional[int] = None, final_state: Optional[Dict[str, Any]] = None):
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            import json
            await conn.execute(
                """
                INSERT INTO game_finish_logs (game_id, game_type, finished_by_user_id, winner_user_id, final_state)
                VALUES ($1, $2, $3, $4, $5)
                """,
                game_id, game_type, finished_by_user_id, winner_user_id, json.dumps(final_state) if final_state else None
            )

    @classmethod
    async def log_game_event(cls, game_id: Optional[int], game_type: Optional[str], user_id: Optional[int],
                             event_type: str, event_message: Optional[str] = None, event_data: Optional[Dict[str, Any]] = None):
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            import json
            await conn.execute(
                """
                INSERT INTO game_event_logs (game_id, game_type, user_id, event_type, event_message, event_data)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                game_id, game_type, user_id, event_type, event_message, json.dumps(event_data) if event_data else None
            )

    @classmethod
    async def get_all_logs(cls, limit: int = 100, offset: int = 0, game_type: Optional[str] = None):
        """Get all logs from all tables, ordered by time"""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            logs = []
            
            # Get creation logs
            query = """
                SELECT 'creation' as log_type, id, game_id, game_type, creator_user_id as user_id, 
                       created_at as timestamp, NULL as action_type, NULL as event_type
                FROM game_creation_logs
            """
            if game_type:
                query += f" WHERE game_type = '{game_type}'"
            query += " ORDER BY created_at DESC LIMIT $1 OFFSET $2"
            
            creation_logs = await conn.fetch(query, limit, offset)
            logs.extend([dict(row) for row in creation_logs])
            
            # Get join logs
            query = """
                SELECT 'join' as log_type, id, game_id, game_type, user_id, 
                       joined_at as timestamp, NULL as action_type, NULL as event_type
                FROM game_join_logs
            """
            if game_type:
                query += f" WHERE game_type = '{game_type}'"
            query += " ORDER BY joined_at DESC LIMIT $1 OFFSET $2"
            
            join_logs = await conn.fetch(query, limit, offset)
            logs.extend([dict(row) for row in join_logs])
            
            # Get action logs
            query = """
                SELECT 'action' as log_type, id, game_id, game_type, user_id, 
                       created_at as timestamp, action_type, NULL as event_type
                FROM game_action_logs
            """
            if game_type:
                query += f" WHERE game_type = '{game_type}'"
            query += " ORDER BY created_at DESC LIMIT $1 OFFSET $2"
            
            action_logs = await conn.fetch(query, limit, offset)
            logs.extend([dict(row) for row in action_logs])
            
            # Get finish logs
            query = """
                SELECT 'finish' as log_type, id, game_id, game_type, finished_by_user_id as user_id, 
                       finished_at as timestamp, NULL as action_type, NULL as event_type
                FROM game_finish_logs
            """
            if game_type:
                query += f" WHERE game_type = '{game_type}'"
            query += " ORDER BY finished_at DESC LIMIT $1 OFFSET $2"
            
            finish_logs = await conn.fetch(query, limit, offset)
            logs.extend([dict(row) for row in finish_logs])
            
            # Sort all logs by timestamp
            logs.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return logs[:limit]

