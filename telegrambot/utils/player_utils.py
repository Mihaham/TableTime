"""Utility functions for getting player usernames"""
from aiogram import Bot
from typing import Dict, Optional
from loguru import logger

async def get_username(bot: Bot, user_id: int) -> str:
    """Get username for a user_id, return user_id as string if not available"""
    try:
        chat = await bot.get_chat(user_id)
        return chat.username or chat.first_name or f"User_{user_id}"
    except Exception as e:
        logger.warning(f"Could not get username for user {user_id}: {e}")
        return f"User_{user_id}"

async def get_player_usernames(bot: Bot, player_ids: list) -> Dict[int, str]:
    """Get usernames for multiple players"""
    usernames = {}
    for player_id in player_ids:
        usernames[player_id] = await get_username(bot, player_id)
    return usernames

