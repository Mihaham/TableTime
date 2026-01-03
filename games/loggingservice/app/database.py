import asyncpg
from app.config import POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_HOST, POSTGRES_PORT
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

class Database:
    _pool: Optional[asyncpg.Pool] = None

    @classmethod
    async def get_pool(cls):
        if cls._pool is None:
            cls._pool = await asyncpg.create_pool(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                database=POSTGRES_DB
            )
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
            await conn.execute(
                """
                INSERT INTO game_event_logs (game_id, game_type, user_id, event_type, event_message, event_data)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                game_id, game_type, user_id, event_type, event_message, json.dumps(event_data) if event_data else None
            )

    @classmethod
    async def get_all_logs(cls, limit: int = 1000, offset: int = 0, game_type: Optional[str] = None):
        """Get all logs from all tables, ordered by time"""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            # Build the query with UNION ALL to combine all log types
            queries = []
            params = []
            param_count = 0
            
            # Creation logs
            creation_query = """
                SELECT 'creation' as log_type, id, game_id, game_type, creator_user_id as user_id, 
                       created_at as timestamp, NULL::text as action_type,
                       jsonb_build_object('invite_code', invite_code) as extra_data
                FROM game_creation_logs
                WHERE 1=1
            """
            if game_type:
                param_count += 1
                creation_query += f" AND game_type = ${param_count}"
                params.append(game_type)
            queries.append(creation_query)
            
            # Join logs
            join_query = """
                SELECT 'join' as log_type, id, game_id, game_type, user_id, 
                       joined_at as timestamp, NULL::text as action_type,
                       NULL::jsonb as extra_data
                FROM game_join_logs
                WHERE 1=1
            """
            if game_type:
                param_count += 1
                join_query += f" AND game_type = ${param_count}"
                params.append(game_type)
            queries.append(join_query)
            
            # Action logs - need to include action_type and action_data
            action_query = """
                SELECT 'action' as log_type, id, game_id, game_type, user_id, 
                       created_at as timestamp, action_type,
                       action_data as extra_data
                FROM game_action_logs
                WHERE 1=1
            """
            if game_type:
                param_count += 1
                action_query += f" AND game_type = ${param_count}"
                params.append(game_type)
            queries.append(action_query)
            
            # Finish logs
            finish_query = """
                SELECT 'finish' as log_type, id, game_id, game_type, finished_by_user_id as user_id, 
                       finished_at as timestamp, NULL::text as action_type,
                       jsonb_build_object('winner_user_id', winner_user_id, 'final_state', final_state) as extra_data
                FROM game_finish_logs
                WHERE 1=1
            """
            if game_type:
                param_count += 1
                finish_query += f" AND game_type = ${param_count}"
                params.append(game_type)
            queries.append(finish_query)
            
            # Combine all queries with UNION ALL
            combined_query = " UNION ALL ".join(queries)
            combined_query += " ORDER BY timestamp DESC"
            
            if limit > 0:
                param_count += 1
                combined_query += f" LIMIT ${param_count}"
                params.append(limit)
            
            if offset > 0:
                param_count += 1
                combined_query += f" OFFSET ${param_count}"
                params.append(offset)
            
            rows = await conn.fetch(combined_query, *params)
            logs = []
            for row in rows:
                log_dict = dict(row)
                # Parse JSONB fields
                if log_dict.get('extra_data'):
                    if isinstance(log_dict['extra_data'], str):
                        try:
                            log_dict['extra_data'] = json.loads(log_dict['extra_data'])
                        except:
                            pass
                logs.append(log_dict)
            
            return logs
