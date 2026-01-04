from aiogram import Router, Bot, F
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import httpx
import asyncio
import csv
import io
from datetime import datetime
from functools import wraps

from config import ADMIN_USER_ID
from utils.keyboard import admin_keyboard, start_keyboard
from utils.buttons import admin_status_button, admin_logs_button, admin_back_button
from utils.urls import logging_service_url
from utils.utils import is_admin

router = Router()

def escape_markdown(text):
    """Escape special Markdown characters"""
    if text is None:
        return "N/A"
    if not isinstance(text, str):
        text = str(text)
    # Escape Markdown special characters
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

def format_timestamp(timestamp):
    """Format timestamp for display"""
    if not timestamp or timestamp == "N/A":
        return "N/A"
    try:
        if isinstance(timestamp, str):
            # Try to parse and format
            if "T" in timestamp:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            return timestamp.split(".")[0].replace("T", " ")
        return str(timestamp)
    except:
        return str(timestamp)

def format_logs_as_table(logs):
    """Format logs as a markdown table"""
    if not logs:
        return "📋 Логи игр пусты."
    
    # Create table header
    table = f"📋 *Логи игр \\(всего: {len(logs)}\\)*\n\n"
    table += "```\n"
    table += f"{'Тип':<12} {'ID игры':<10} {'Тип игры':<15} {'Пользователь':<12} {'Действие':<20} {'Время':<20}\n"
    table += "-" * 100 + "\n"
    
    # Add rows (limit to 50 for readability)
    for log in logs[:50]:
        log_type = str(log.get("log_type", "unknown"))[:10]
        game_id = str(log.get("game_id", "N/A"))[:8]
        game_type = str(log.get("game_type", "N/A") or "N/A")[:13]
        user_id = str(log.get("user_id", "N/A"))[:10]
        action_type = str(log.get("action_type") or "-")[:18]
        timestamp = format_timestamp(log.get("timestamp", "N/A"))[:18]
        
        table += f"{log_type:<12} {game_id:<10} {game_type:<15} {user_id:<12} {action_type:<20} {timestamp:<20}\n"
    
    if len(logs) > 50:
        table += f"\n... и еще {len(logs) - 50} записей\n"
    
    table += "```"
    return table

def generate_csv_file(logs):
    """Generate CSV file from logs"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "Тип", "ID игры", "Тип игры", "ID пользователя", 
        "Тип действия", "Время", "Дополнительные данные"
    ])
    
    # Write data rows
    for log in logs:
        log_type = log.get("log_type", "unknown")
        game_id = log.get("game_id", "N/A")
        game_type = log.get("game_type", "N/A") or "N/A"
        user_id = log.get("user_id", "N/A")
        action_type = log.get("action_type") or ""
        timestamp = format_timestamp(log.get("timestamp", "N/A"))
        
        # Format extra_data as JSON string
        extra_data = log.get("extra_data", {})
        if isinstance(extra_data, dict):
            import json
            extra_data_str = json.dumps(extra_data, ensure_ascii=False)
        else:
            extra_data_str = str(extra_data) if extra_data else ""
        
        writer.writerow([
            log_type, game_id, game_type, user_id,
            action_type, timestamp, extra_data_str
        ])
    
    csv_content = output.getvalue()
    output.close()
    return csv_content.encode('utf-8-sig')  # UTF-8 with BOM for Excel compatibility

# Microservice URLs for health checks
MICROSERVICES = {
    "API Gateway": "http://apigateway:8000/health",
    "User Service": "http://userservice:8000/health",
    "Game Engine": "http://gameengine:8000/health",
    "Monopoly Service": "http://monopoly:8000/health",
    "RPS Service": "http://rps:8000/health",
    "Dice and Ladders Service": "http://diceladders:8000/health",
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
    """Show all game logs as a table and CSV file"""
    try:
        await message.reply("📋 Загрузка логов...", reply_markup=admin_keyboard(message.from_user.id))
        
        # Use longer timeout and follow redirects
        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
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
                
                # Format logs as table
                table_text = format_logs_as_table(logs)
                
                # Send table
                await message.reply(
                    table_text,
                    parse_mode="Markdown",
                    reply_markup=admin_keyboard(message.from_user.id)
                )
                
                # Generate and send CSV file
                csv_content = generate_csv_file(logs)
                csv_file = BufferedInputFile(
                    csv_content,
                    filename=f"game_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                )
                
                await bot.send_document(
                    message.chat.id,
                    csv_file,
                    caption=f"📊 CSV файл с логами игр ({len(logs)} записей)"
                )
                
            else:
                await message.reply(
                    f"❌ Ошибка при получении логов: {response.status_code}",
                    reply_markup=admin_keyboard(message.from_user.id)
                )
    except httpx.TimeoutException:
        await message.reply(
            "❌ Ошибка: время ожидания истекло. Попробуйте позже.",
            reply_markup=admin_keyboard(message.from_user.id)
        )
    except httpx.ConnectError:
        await message.reply(
            "❌ Ошибка: не удалось подключиться к серверу логов.",
            reply_markup=admin_keyboard(message.from_user.id)
        )
    except httpx.RequestError as e:
        await message.reply(
            f"❌ Ошибка соединения: {str(e)}",
            reply_markup=admin_keyboard(message.from_user.id)
        )
    except Exception as e:
        error_msg = str(e)
        # Log the full error for debugging
        import logging
        logging.error(f"Error fetching logs: {e}", exc_info=True)
        await message.reply(
            f"❌ Ошибка при получении логов: {error_msg}",
            reply_markup=admin_keyboard(message.from_user.id)
        )