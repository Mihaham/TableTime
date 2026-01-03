from aiogram import Router, Bot, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import httpx
import asyncio
from functools import wraps

from config import ADMIN_USER_ID
from utils.keyboard import admin_keyboard, start_keyboard
from utils.buttons import admin_status_button, admin_logs_button, admin_back_button
from utils.urls import logging_service_url
from utils.utils import is_admin

router = Router()

# Microservice URLs for health checks
MICROSERVICES = {
    "API Gateway": "http://apigateway:8000/health",
    "User Service": "http://userservice:8000/health",
    "Game Engine": "http://gameengine:8000/health",
    "Monopoly Service": "http://monopoly:8000/health",
    "RPS Service": "http://rps:8000/health",
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
@router.message(F.text == admin_status_button)
@admin_only
async def check_status(message: Message, bot: Bot):
    """Check status of all microservices"""
    await message.reply("🔍 Проверка статуса всех микросервисов...")
    
    status_report = "📊 **Отчет о статусе микросервисов**\n\n"
    
    # Check all services concurrently
    tasks = [
        check_service_health(name, url)
        for name, url in MICROSERVICES.items()
    ]
    results = await asyncio.gather(*tasks)
    
    # Format results
    online_count = 0
    total_count = len(MICROSERVICES)
    
    for (service_name, _), result in zip(MICROSERVICES.items(), results):
        status_report += f"**{service_name}**\n"
        status_report += f"Статус: {result['status']}\n"
        
        if "✅ Online" in result['status']:
            online_count += 1
            
        if result.get('details'):
            if isinstance(result['details'], dict):
                # Format JSON response nicely
                details_str = ", ".join([f"{k}: {v}" for k, v in result['details'].items()])
                status_report += f"Детали: {details_str}\n"
            else:
                status_report += f"Детали: {result['details']}\n"
        status_report += "\n"
    
    status_report += f"\n**Итого**: {online_count}/{total_count} сервисов онлайн"
    
    await message.reply(status_report, parse_mode="Markdown", reply_markup=admin_keyboard(message.from_user.id))


@router.message(F.text == admin_back_button)
async def admin_back(message: Message, bot: Bot, state: FSMContext):
    """Return to main menu from admin panel"""
    if not is_admin(message.from_user.id):
        return
    
    await message.reply(
        "Главное меню",
        reply_markup=start_keyboard(message.from_user.id)
    )


@router.message(Command("admin"))
@admin_only
async def admin_help(message: Message, bot: Bot):
    """Show available admin commands"""
    help_text = "🔐 **Админ-панель**\n\n"
    help_text += "**Кнопки:**\n"
    help_text += f"• {admin_status_button} - Проверить статус всех сервисов\n"
    help_text += f"• {admin_logs_button} - Просмотреть логи игр\n\n"
    help_text += "**Команды:**\n"
    help_text += "• `/status` - Проверить статус всех сервисов\n"
    help_text += "• `/logs` - Просмотреть логи игр\n"
    help_text += "• `/admin` - Показать это сообщение\n"
    
    await message.reply(
        help_text,
        parse_mode="Markdown",
        reply_markup=admin_keyboard(message.from_user.id)
    )

@router.message(F.text == admin_logs_button)
@router.message(Command("logs"))
@admin_only
async def show_game_logs(message: Message, bot: Bot):
    """Show all game logs with detailed information"""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Get all logs (no limit or high limit)
            response = await client.get(f"{logging_service_url}/all", params={"limit": 1000})
            if response.status_code == 200:
                data = response.json()
                logs = data.get("logs", [])
                
                if not logs:
                    await message.reply(
                        "📋 Логи игр пусты. Пока нет записанных событий.",
                        reply_markup=admin_keyboard(message.from_user.id)
                    )
                    return
                
                # Format logs with detailed information
                log_text = f"📋 **Все логи игр (всего: {len(logs)})**\n\n"
                
                # Telegram message limit is 4096 characters, so we'll send multiple messages if needed
                current_message = log_text
                
                for i, log in enumerate(logs, 1):
                    log_type = log.get("log_type", "unknown")
                    game_id = log.get("game_id", "N/A")
                    game_type = log.get("game_type", "N/A")
                    user_id = log.get("user_id", "N/A")
                    timestamp = log.get("timestamp", "N/A")
                    action_type = log.get("action_type")
                    
                    # Format timestamp
                    if timestamp and timestamp != "N/A":
                        try:
                            if isinstance(timestamp, str):
                                timestamp = timestamp.split(".")[0].replace("T", " ")  # Remove microseconds and format
                        except:
                            pass
                    
                    # Format log type emoji
                    type_emoji = {
                        "creation": "🆕",
                        "join": "➕",
                        "action": "🎮",
                        "finish": "🏁"
                    }.get(log_type, "📝")
                    
                    log_entry = f"{type_emoji} **{log_type.upper()}**\n"
                    log_entry += f"   🎮 Игра: {game_id} ({game_type})\n"
                    log_entry += f"   👤 Пользователь: {user_id}\n"
                    
                    # Get extra_data (contains detailed information)
                    extra_data = log.get("extra_data", {})
                    
                    # Add detailed info based on log type
                    if log_type == "creation":
                        invite_code = extra_data.get("invite_code") if isinstance(extra_data, dict) else None
                        if invite_code:
                            log_entry += f"   🔑 Код приглашения: {invite_code}\n"
                    
                    if log_type == "action" and action_type:
                        log_entry += f"   📌 Действие: {action_type}\n"
                        
                        # Add detailed action information
                        if isinstance(extra_data, dict):
                            if action_type == "round_complete":
                                player1_choice = extra_data.get("player1_choice")
                                player2_choice = extra_data.get("player2_choice")
                                winner = extra_data.get("winner")
                                round_num = extra_data.get("round_number")
                                player1_score = extra_data.get("player1_score")
                                player2_score = extra_data.get("player2_score")
                                player1_id = extra_data.get("player1_id")
                                player2_id = extra_data.get("player2_id")
                                
                                if round_num is not None:
                                    log_entry += f"   🎲 Раунд: {round_num}\n"
                                if player1_choice:
                                    log_entry += f"   ✊ Игрок 1: {player1_choice}\n"
                                if player2_choice:
                                    log_entry += f"   ✋ Игрок 2: {player2_choice}\n"
                                if winner:
                                    if winner == "player1" or winner == 1:
                                        log_entry += f"   🏆 Победитель раунда: Игрок 1\n"
                                    elif winner == "player2" or winner == 2:
                                        log_entry += f"   🏆 Победитель раунда: Игрок 2\n"
                                    else:
                                        log_entry += f"   🤝 Ничья в раунде\n"
                                if player1_score is not None and player2_score is not None:
                                    log_entry += f"   📊 Счёт: {player1_score} - {player2_score}\n"
                            
                            elif action_type in ["player1_move", "player2_move"]:
                                choice = extra_data.get("choice")
                                if choice:
                                    player_num = "1" if action_type == "player1_move" else "2"
                                    log_entry += f"   ✋ Игрок {player_num} выбрал: {choice}\n"
                    
                    if log_type == "finish":
                        if isinstance(extra_data, dict):
                            winner_id = extra_data.get("winner_user_id")
                            final_state = extra_data.get("final_state")
                            
                            if winner_id:
                                log_entry += f"   🏆 Победитель игры: {winner_id}\n"
                            else:
                                log_entry += f"   🤝 Ничья в игре\n"
                            
                            if isinstance(final_state, dict):
                                player1_score = final_state.get("player1_score")
                                player2_score = final_state.get("player2_score")
                                if player1_score is not None and player2_score is not None:
                                    log_entry += f"   📊 Финальный счёт: {player1_score} - {player2_score}\n"
                    
                    log_entry += f"   ⏰ {timestamp}\n\n"
                    
                    # Check if adding this log would exceed Telegram's limit
                    if len(current_message + log_entry) > 4000:
                        # Send current message
                        await message.reply(
                            current_message,
                            parse_mode="Markdown",
                            reply_markup=admin_keyboard(message.from_user.id) if i == len(logs) else None
                        )
                        # Start new message
                        current_message = f"📋 **Логи игр (продолжение)**\n\n{log_entry}"
                    else:
                        current_message += log_entry
                
                # Send remaining logs
                if current_message.strip() != log_text.strip():
                    await message.reply(
                        current_message,
                        parse_mode="Markdown",
                        reply_markup=admin_keyboard(message.from_user.id)
                    )
                else:
                    # All logs fit in one message
                    await message.reply(
                        current_message,
                        parse_mode="Markdown",
                        reply_markup=admin_keyboard(message.from_user.id)
                    )
            else:
                await message.reply(
                    f"❌ Ошибка при получении логов: {response.status_code}",
                    reply_markup=admin_keyboard(message.from_user.id)
                )
    except Exception as e:
        await message.reply(
            f"❌ Ошибка при получении логов: {str(e)}",
            reply_markup=admin_keyboard(message.from_user.id)
        )