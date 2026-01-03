from aiogram import Router, Bot
from aiogram.types import Message
from aiogram.filters import Command
import httpx
import asyncio
from functools import wraps

from config import ADMIN_USER_ID

router = Router()

# Microservice URLs for health checks
MICROSERVICES = {
    "API Gateway": "http://apigateway:8000/health",
    "Database Interface": "http://databaseinterface:8000/health",
    "User Service": "http://userservice:8000/health",
    "Game Engine": "http://gameengine:8000/health",
    "Monopoly Service": "http://monopoly:8000/health",
    "Notification Service": "http://notificationservice:8000/health",
}


def admin_only(func):
    """Decorator to restrict access to admin only"""
    @wraps(func)
    async def wrapper(message: Message, *args, **kwargs):
        user_id = message.from_user.id
        
        if ADMIN_USER_ID is None:
            await message.reply("❌ Admin access is not configured. Please set ADMIN_USER_ID in .env file.")
            return
        
        if user_id != ADMIN_USER_ID:
            await message.reply("❌ Access denied. This command is only available for administrators.")
            return
        
        return await func(message, *args, **kwargs)
    return wrapper


async def check_service_health(service_name: str, url: str) -> dict:
    """Check health status of a single microservice"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "✅ Online",
                    "details": data,
                    "status_code": response.status_code
                }
            else:
                return {
                    "status": "⚠️ Error",
                    "details": f"Status code: {response.status_code}",
                    "status_code": response.status_code
                }
    except httpx.TimeoutException:
        return {
            "status": "⏱️ Timeout",
            "details": "Service did not respond within 5 seconds",
            "status_code": None
        }
    except httpx.ConnectError:
        return {
            "status": "❌ Offline",
            "details": "Could not connect to service",
            "status_code": None
        }
    except Exception as e:
        return {
            "status": "❌ Error",
            "details": str(e),
            "status_code": None
        }


@router.message(Command("status"))
@admin_only
async def check_status(message: Message, bot: Bot):
    """Check status of all microservices"""
    await message.reply("🔍 Checking microservice statuses...")
    
    status_report = "📊 **Microservice Status Report**\n\n"
    
    # Check all services concurrently
    tasks = [
        check_service_health(name, url)
        for name, url in MICROSERVICES.items()
    ]
    results = await asyncio.gather(*tasks)
    
    # Format results
    for (service_name, _), result in zip(MICROSERVICES.items(), results):
        status_report += f"**{service_name}**\n"
        status_report += f"Status: {result['status']}\n"
        if result.get('details'):
            if isinstance(result['details'], dict):
                # Format JSON response nicely
                details_str = ", ".join([f"{k}: {v}" for k, v in result['details'].items()])
                status_report += f"Details: {details_str}\n"
            else:
                status_report += f"Details: {result['details']}\n"
        status_report += "\n"
    
    await message.reply(status_report, parse_mode="Markdown")


@router.message(Command("admin"))
@admin_only
async def admin_help(message: Message, bot: Bot):
    """Show available admin commands"""
    help_text = "🔐 **Admin Commands**\n\n"
    help_text += "/status - Check status of all microservices\n"
    help_text += "/admin - Show this help message\n"
    
    await message.reply(help_text, parse_mode="Markdown")