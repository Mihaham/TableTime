from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import Bot
from utils.buttons import diceladders_roll_button, diceladders_move_button, diceladders_finish_button
from utils.utils import get_diceladders_game_state, send_seq_messages
from utils.urls import diceladders_service_url
from utils.texts import diceladders_game_started, diceladders_your_turn
import requests
import io
import tempfile
import os
from loguru import logger

router = Router()

class DiceLaddersStates(StatesGroup):
    Playing = State()

def diceladders_keyboard(show_finish: bool = False, show_move: bool = False):
    """Create keyboard for dice-ladders game"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = [
        [InlineKeyboardButton(text=diceladders_roll_button, callback_data="diceladders_roll")]
    ]
    if show_move:
        buttons.append([InlineKeyboardButton(text=diceladders_move_button, callback_data="diceladders_move")])
    if show_finish:
        buttons.append([InlineKeyboardButton(text=diceladders_finish_button, callback_data="diceladders_finish")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_board_image_bytes(game_id: int) -> bytes:
    """Get board image from dice-ladders service"""
    try:
        url = f"{diceladders_service_url}/{game_id}/board"
        logger.info(f"Getting board image from: {url}")
        response = requests.get(url)
        logger.info(f"Board image response: {response.status_code}, content-type: {response.headers.get('content-type', 'unknown')}")
        
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            
            # Check if response is JSON-wrapped (legacy API gateway behavior)
            if content_type.startswith('application/json'):
                try:
                    json_data = response.json()
                    # Try to extract base64 encoded image or direct data
                    if 'data' in json_data:
                        import base64
                        # If it's base64 encoded
                        try:
                            image_bytes = base64.b64decode(json_data['data'])
                            logger.info(f"Decoded base64 image, size: {len(image_bytes)} bytes")
                            return image_bytes
                        except:
                            # If it's raw text representation, this is corrupted
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
            
            # Validate PNG header (first 8 bytes should be PNG signature)
            png_signature = b'\x89PNG\r\n\x1a\n'
            if len(image_bytes) >= 8 and image_bytes[:8] != png_signature:
                logger.error(f"Invalid PNG signature for game_id {game_id}. First bytes: {image_bytes[:8]}")
                return False
            
            # Save to temporary file and use FSInputFile (more reliable for large images)
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
        # Clean up temp file on error
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except:
                pass
    return False

@router.callback_query(F.data == "diceladders_roll")
async def roll_dice_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    """Handle dice roll"""
    user_id = callback.from_user.id
    data = await state.get_data()
    game_id = data.get("diceladders_game_id")  # Use the service-specific game_id
    
    # If game_id is not in state, try to retrieve it from the service
    if not game_id:
        from utils.utils import get_diceladders_game_by_user
        game_id = get_diceladders_game_by_user(user_id)
        if game_id:
            await state.update_data(diceladders_game_id=game_id)
            logger.info(f"Retrieved diceladders_game_id {game_id} for user {user_id}")
        else:
            await callback.answer("Ошибка: игра не найдена", show_alert=True)
            return
    
    try:
        # Get current game state
        game_state = get_diceladders_game_state(game_id)
        
        # Check if it's user's turn
        # current_turn is a player number (1, 2, 3), not user_id
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
        response = requests.post(f"{diceladders_service_url}/roll_dice", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            dice_roll = result.get("dice_roll")
            
            # Send board with dice result and move button
            caption = f"🎲 Выпало: {dice_roll}\n\nТеперь сделайте ход!"
            await send_board_image(bot, user_id, game_id, caption, reply_markup=diceladders_keyboard(show_finish=True, show_move=True))
            
            # Get player IDs
            player_ids = []
            if game_state.get("player1_id"):
                player_ids.append(game_state["player1_id"])
            if game_state.get("player2_id"):
                player_ids.append(game_state["player2_id"])
            if game_state.get("player3_id"):
                player_ids.append(game_state["player3_id"])
            
            # Notify other players
            import asyncio
            for pid in player_ids:
                if pid != user_id:
                    try:
                        await send_board_image(bot, pid, game_id, f"🎲 Игрок {callback.from_user.username} выбросил {dice_roll}")
                        await asyncio.sleep(0.1)  # Small delay to avoid rate limiting
                    except Exception as e:
                        logger.error(f"Error sending board to player {pid}: {e}", exc_info=True)
                        continue
            
            await callback.answer(f"Выпало: {dice_roll}")
        else:
            await callback.answer("Ошибка при броске кости", show_alert=True)
    except Exception as e:
        logger.error(f"Error in roll_dice_handler: {e}", exc_info=True)
        await callback.answer(f"Ошибка: {str(e)}", show_alert=True)

@router.callback_query(F.data == "diceladders_move")
async def move_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    """Handle player move after dice roll"""
    user_id = callback.from_user.id
    data = await state.get_data()
    game_id = data.get("diceladders_game_id")  # Use the service-specific game_id
    
    # If game_id is not in state, try to retrieve it from the service
    if not game_id:
        from utils.utils import get_diceladders_game_by_user
        game_id = get_diceladders_game_by_user(user_id)
        if game_id:
            await state.update_data(diceladders_game_id=game_id)
            logger.info(f"Retrieved diceladders_game_id {game_id} for user {user_id}")
        else:
            await callback.answer("Ошибка: игра не найдена", show_alert=True)
            return
    
    try:
        # Get current game state
        game_state = get_diceladders_game_state(game_id)
        
        # Check if it's user's turn
        # current_turn is a player number (1, 2, 3), not user_id
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
        
        if not game_state.get("last_dice_roll"):
            await callback.answer("Сначала бросьте кость!", show_alert=True)
            return
        
        # Make move
        payload = {"user_id": user_id, "game_id": game_id}
        response = requests.post(f"{diceladders_service_url}/move", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            new_position = result.get("new_position")
            new_state = result.get("new_state")
            winner_id = new_state.get("winner_id") if new_state else None
            
            # Get updated player IDs from new_state
            player_ids = []
            if new_state:
                if new_state.get("player1_id"):
                    player_ids.append(new_state["player1_id"])
                if new_state.get("player2_id"):
                    player_ids.append(new_state["player2_id"])
                if new_state.get("player3_id"):
                    player_ids.append(new_state["player3_id"])
            else:
                # Fallback to old game_state
                if game_state.get("player1_id"):
                    player_ids.append(game_state["player1_id"])
                if game_state.get("player2_id"):
                    player_ids.append(game_state["player2_id"])
                if game_state.get("player3_id"):
                    player_ids.append(game_state["player3_id"])
            
            # Get current turn player_id from new_state
            current_turn_player_id = None
            if new_state and new_state.get("current_turn"):
                current_turn_num = new_state["current_turn"]
                if current_turn_num == 1:
                    current_turn_player_id = new_state.get("player1_id")
                elif current_turn_num == 2:
                    current_turn_player_id = new_state.get("player2_id")
                elif current_turn_num == 3:
                    current_turn_player_id = new_state.get("player3_id")
            
            # Send updated board to all players
            if winner_id:
                caption = f"🏆 Игрок {callback.from_user.username} выиграл!"
                for pid in player_ids:
                    await send_board_image(bot, pid, game_id, caption)
                    if pid == user_id:
                        await callback.message.answer("🎉 Поздравляем! Вы выиграли!")
                    else:
                        await bot.send_message(pid, f"🎉 Игрок {callback.from_user.username} выиграл игру!")
                await callback.answer("Вы выиграли! 🎉")
                await state.clear()  # Clear state after game finishes
            else:
                caption = f"Позиция: {new_position}/100"
                for pid in player_ids:
                    if pid == current_turn_player_id:
                        await send_board_image(bot, pid, game_id, f"{caption}\n\n{diceladders_your_turn}", reply_markup=diceladders_keyboard(show_finish=True))
                    else:
                        await send_board_image(bot, pid, game_id, caption)
                await callback.answer(f"Ход сделан! Позиция: {new_position}")
        else:
            await callback.answer("Ошибка при ходе", show_alert=True)
    except Exception as e:
        logger.error(f"Error in move_handler: {e}", exc_info=True)
        await callback.answer(f"Ошибка: {str(e)}", show_alert=True)

@router.callback_query(F.data == "diceladders_finish")
async def finish_game_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    """Handle game finish"""
    user_id = callback.from_user.id
    data = await state.get_data()
    game_id = data.get("diceladders_game_id")  # Use the service-specific game_id
    
    # If game_id is not in state, try to retrieve it from the service
    if not game_id:
        from utils.utils import get_diceladders_game_by_user
        game_id = get_diceladders_game_by_user(user_id)
        if game_id:
            await state.update_data(diceladders_game_id=game_id)
            logger.info(f"Retrieved diceladders_game_id {game_id} for user {user_id}")
        else:
            await callback.answer("Ошибка: игра не найдена", show_alert=True)
            return
    
    try:
        payload = {"user_id": user_id, "game_id": game_id}
        response = requests.post(f"{diceladders_service_url}/finish", json=payload)
        
        if response.status_code == 200:
            # Get player IDs
            game_state = get_diceladders_game_state(game_id)
            player_ids = []
            if game_state.get("player1_id"):
                player_ids.append(game_state["player1_id"])
            if game_state.get("player2_id"):
                player_ids.append(game_state["player2_id"])
            if game_state.get("player3_id"):
                player_ids.append(game_state["player3_id"])
            
            import asyncio
            for pid in player_ids:
                if pid != user_id:
                    try:
                        await bot.send_message(pid, f"Игра завершена игроком {callback.from_user.username}")
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

