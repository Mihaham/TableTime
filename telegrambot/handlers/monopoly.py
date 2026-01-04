from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import Bot
from utils.buttons import monopoly_roll_button, monopoly_buy_button, monopoly_end_turn_button, monopoly_finish_button
from utils.utils import get_monopoly_game_state, send_seq_messages
from utils.urls import monopoly_service_url
from utils.texts import monopoly_game_started, monopoly_your_turn
from utils.player_utils import get_username, get_player_usernames
import requests
import tempfile
import os
from loguru import logger

router = Router()

class MonopolyStates(StatesGroup):
    Playing = State()

def monopoly_keyboard(show_buy: bool = False, show_finish: bool = False):
    """Create keyboard for monopoly game"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = [
        [InlineKeyboardButton(text=monopoly_roll_button, callback_data="monopoly_roll")]
    ]
    if show_buy:
        buttons.append([InlineKeyboardButton(text=monopoly_buy_button, callback_data="monopoly_buy")])
    buttons.append([InlineKeyboardButton(text=monopoly_end_turn_button, callback_data="monopoly_end_turn")])
    if show_finish:
        buttons.append([InlineKeyboardButton(text=monopoly_finish_button, callback_data="monopoly_finish")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_board_image_bytes(game_id: int) -> bytes:
    """Get board image from monopoly service"""
    try:
        url = f"{monopoly_service_url}/{game_id}/board"
        logger.info(f"Getting board image from: {url}")
        response = requests.get(url)
        logger.info(f"Board image response: {response.status_code}, content-type: {response.headers.get('content-type', 'unknown')}")
        
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            
            # Check if response is JSON-wrapped (legacy API gateway behavior)
            if content_type.startswith('application/json'):
                try:
                    json_data = response.json()
                    if 'data' in json_data:
                        import base64
                        try:
                            image_bytes = base64.b64decode(json_data['data'])
                            logger.info(f"Decoded base64 image, size: {len(image_bytes)} bytes")
                            return image_bytes
                        except:
                            logger.error(f"JSON response contains text data, cannot recover binary image")
                            return None
                except Exception as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    return None
            
            # Direct binary response (correct behavior)
            image_bytes = response.content
            logger.info(f"Got direct binary image, size: {len(image_bytes)} bytes")
            return image_bytes
        else:
            logger.error(f"Failed to get board image: {response.status_code}, {response.text[:200]}")
    except Exception as e:
        logger.error(f"Error getting board image: {e}", exc_info=True)
    return None

async def send_board_image(bot: Bot, user_id: int, game_id: int, caption: str = "", reply_markup=None):
    """Send board image to user"""
    temp_file = None
    try:
        logger.info(f"Sending board image to user {user_id}, game_id: {game_id}")
        image_bytes = get_board_image_bytes(game_id)
        if image_bytes:
            logger.info(f"Got board image, size: {len(image_bytes)} bytes")
            
            # Validate PNG header
            png_signature = b'\x89PNG\r\n\x1a\n'
            if len(image_bytes) >= 8 and image_bytes[:8] != png_signature:
                logger.error(f"Invalid PNG signature for game_id {game_id}. First bytes: {image_bytes[:8]}")
                return False
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                tmp_file.write(image_bytes)
                temp_file = tmp_file.name
            
            # Use FSInputFile with the temp file path
            photo = FSInputFile(temp_file, filename="board.png")
            await bot.send_photo(user_id, photo, caption=caption, reply_markup=reply_markup)
            
            # Clean up temp file
            try:
                os.unlink(temp_file)
            except:
                pass
            
            logger.info(f"Board image sent successfully to user {user_id}")
            return True
        else:
            logger.error(f"No board image bytes received for game_id: {game_id}")
    except Exception as e:
        logger.error(f"Error sending board image to user {user_id}: {e}", exc_info=True)
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except:
                pass
    return False

@router.callback_query(F.data == "monopoly_roll")
async def roll_dice_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    """Handle dice roll"""
    user_id = callback.from_user.id
    data = await state.get_data()
    game_id = data.get("monopoly_game_id")
    
    if not game_id:
        from utils.utils import get_monopoly_game_by_user
        game_id = get_monopoly_game_by_user(user_id)
        if game_id:
            await state.update_data(monopoly_game_id=game_id)
            logger.info(f"Retrieved monopoly_game_id {game_id} for user {user_id}")
        else:
            await callback.answer("Ошибка: игра не найдена", show_alert=True)
            return
    
    try:
        # Get current game state
        game_state = get_monopoly_game_state(game_id)
        
        # Check if it's user's turn
        player_num = None
        if game_state.get("player1_id") == user_id:
            player_num = 1
        elif game_state.get("player2_id") == user_id:
            player_num = 2
        elif game_state.get("player3_id") == user_id:
            player_num = 3
        
        if game_state.get("current_turn") != player_num:
            await callback.answer("Не ваш ход!", show_alert=True)
            return
        
        # Roll dice
        payload = {"user_id": user_id, "game_id": game_id}
        response = requests.post(f"{monopoly_service_url}/roll_dice", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            message_text = result.get("message", "")
            new_position = result.get("new_position")
            can_buy = result.get("can_buy", False)
            
            # Send board with result
            caption = message_text
            if can_buy:
                caption += "\n\nВы можете купить эту недвижимость!"
            await send_board_image(bot, user_id, game_id, caption, 
                                  reply_markup=monopoly_keyboard(show_buy=can_buy, show_finish=True))
            
            # Get player IDs
            player_ids = []
            if game_state.get("player1_id"):
                player_ids.append(game_state["player1_id"])
            if game_state.get("player2_id"):
                player_ids.append(game_state["player2_id"])
            if game_state.get("player3_id"):
                player_ids.append(game_state["player3_id"])
            
            # Get usernames
            player_username = callback.from_user.username or callback.from_user.first_name or f"User_{user_id}"
            
            # Notify other players
            import asyncio
            for pid in player_ids:
                if pid != user_id:
                    try:
                        move_message = f"{player_username} сделал ход:\n{message_text}"
                        await send_board_image(bot, pid, game_id, move_message)
                        await asyncio.sleep(0.1)
                    except Exception as e:
                        logger.error(f"Error sending board to player {pid}: {e}", exc_info=True)
                        continue
            
            await callback.answer(f"Выпало: {result.get('dice_roll', '?')}")
        else:
            error_msg = response.json().get("detail", "Ошибка при броске кости")
            await callback.answer(error_msg, show_alert=True)
    except Exception as e:
        logger.error(f"Error in roll_dice_handler: {e}", exc_info=True)
        await callback.answer(f"Ошибка: {str(e)}", show_alert=True)

@router.callback_query(F.data == "monopoly_buy")
async def buy_property_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    """Handle property purchase"""
    user_id = callback.from_user.id
    data = await state.get_data()
    game_id = data.get("monopoly_game_id")
    
    if not game_id:
        from utils.utils import get_monopoly_game_by_user
        game_id = get_monopoly_game_by_user(user_id)
        if game_id:
            await state.update_data(monopoly_game_id=game_id)
        else:
            await callback.answer("Ошибка: игра не найдена", show_alert=True)
            return
    
    try:
        payload = {"user_id": user_id, "game_id": game_id}
        response = requests.post(f"{monopoly_service_url}/buy_property", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            message_text = result.get("message", "Недвижимость куплена!")
            
            # Send updated board
            await send_board_image(bot, user_id, game_id, message_text,
                                  reply_markup=monopoly_keyboard(show_finish=True))
            
            # Get player IDs and notify others
            game_state = get_monopoly_game_state(game_id)
            player_ids = []
            if game_state.get("player1_id"):
                player_ids.append(game_state["player1_id"])
            if game_state.get("player2_id"):
                player_ids.append(game_state["player2_id"])
            if game_state.get("player3_id"):
                player_ids.append(game_state["player3_id"])
            
            player_username = callback.from_user.username or callback.from_user.first_name or f"User_{user_id}"
            
            import asyncio
            for pid in player_ids:
                if pid != user_id:
                    try:
                        await send_board_image(bot, pid, game_id, f"{player_username} купил недвижимость!")
                        await asyncio.sleep(0.1)
                    except Exception as e:
                        logger.error(f"Error sending board to player {pid}: {e}", exc_info=True)
            
            await callback.answer("Недвижимость куплена!")
        else:
            error_msg = response.json().get("detail", "Ошибка при покупке")
            await callback.answer(error_msg, show_alert=True)
    except Exception as e:
        logger.error(f"Error in buy_property_handler: {e}", exc_info=True)
        await callback.answer(f"Ошибка: {str(e)}", show_alert=True)

@router.callback_query(F.data == "monopoly_end_turn")
async def end_turn_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    """Handle end turn"""
    user_id = callback.from_user.id
    data = await state.get_data()
    game_id = data.get("monopoly_game_id")
    
    if not game_id:
        from utils.utils import get_monopoly_game_by_user
        game_id = get_monopoly_game_by_user(user_id)
        if game_id:
            await state.update_data(monopoly_game_id=game_id)
        else:
            await callback.answer("Ошибка: игра не найдена", show_alert=True)
            return
    
    try:
        payload = {"user_id": user_id, "game_id": game_id}
        response = requests.post(f"{monopoly_service_url}/end_turn", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            new_state = result.get("new_state", {})
            
            # Get player IDs
            player_ids = []
            current_turn_player_id = None
            if new_state.get("player1_id"):
                player_ids.append(new_state["player1_id"])
            if new_state.get("player2_id"):
                player_ids.append(new_state["player2_id"])
            if new_state.get("player3_id"):
                player_ids.append(new_state["player3_id"])
            
            # Get current turn player
            current_turn_num = new_state.get("current_turn")
            if current_turn_num == 1:
                current_turn_player_id = new_state.get("player1_id")
            elif current_turn_num == 2:
                current_turn_player_id = new_state.get("player2_id")
            elif current_turn_num == 3:
                current_turn_player_id = new_state.get("player3_id")
            
            # Get usernames
            player_username = callback.from_user.username or callback.from_user.first_name or f"User_{user_id}"
            current_turn_username = await get_username(bot, current_turn_player_id) if current_turn_player_id else "Unknown"
            
            # Send board to all players
            for pid in player_ids:
                if pid == current_turn_player_id:
                    await send_board_image(bot, pid, game_id, monopoly_your_turn,
                                          reply_markup=monopoly_keyboard(show_finish=True))
                else:
                    await send_board_image(bot, pid, game_id, f"{player_username} завершил ход. Теперь ход {current_turn_username}")
            
            await callback.answer("Ход завершен")
        else:
            error_msg = response.json().get("detail", "Ошибка при завершении хода")
            await callback.answer(error_msg, show_alert=True)
    except Exception as e:
        logger.error(f"Error in end_turn_handler: {e}", exc_info=True)
        await callback.answer(f"Ошибка: {str(e)}", show_alert=True)

@router.callback_query(F.data == "monopoly_finish")
async def finish_game_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    """Handle game finish"""
    user_id = callback.from_user.id
    data = await state.get_data()
    game_id = data.get("monopoly_game_id")
    
    if not game_id:
        from utils.utils import get_monopoly_game_by_user
        game_id = get_monopoly_game_by_user(user_id)
        if game_id:
            await state.update_data(monopoly_game_id=game_id)
        else:
            await callback.answer("Ошибка: игра не найдена", show_alert=True)
            return
    
    try:
        payload = {"user_id": user_id, "game_id": game_id}
        response = requests.post(f"{monopoly_service_url}/finish", json=payload)
        
        if response.status_code == 200:
            # Get player IDs
            game_state = get_monopoly_game_state(game_id)
            player_ids = []
            if game_state.get("player1_id"):
                player_ids.append(game_state["player1_id"])
            if game_state.get("player2_id"):
                player_ids.append(game_state["player2_id"])
            if game_state.get("player3_id"):
                player_ids.append(game_state["player3_id"])
            
            player_username = callback.from_user.username or callback.from_user.first_name or f"User_{user_id}"
            
            import asyncio
            for pid in player_ids:
                if pid != user_id:
                    try:
                        await bot.send_message(pid, f"Игра завершена игроком {player_username}")
                        await asyncio.sleep(0.1)
                    except Exception as e:
                        logger.error(f"Error sending finish message to player {pid}: {e}", exc_info=True)
                        continue
            
            try:
                await callback.message.answer("Игра завершена")
                await callback.answer("Игра завершена")
            except Exception as e:
                logger.error(f"Error sending finish confirmation: {e}", exc_info=True)
            await state.clear()
        else:
            await callback.answer("Ошибка при завершении игры", show_alert=True)
    except Exception as e:
        logger.error(f"Error in finish_game_handler: {e}", exc_info=True)
        await callback.answer(f"Ошибка: {str(e)}", show_alert=True)

