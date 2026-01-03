from aiogram import Router, F, Bot
from aiogram.types import Message, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from utils.buttons import rps_button, rps_finish_button
from utils.texts import (
    rps_game_started, 
    rps_waiting_for_opponent, 
    rps_choose_move,
    rps_round_result,
    rps_game_scores,
    rps_move_made,
    rps_invalid_move,
    rps_game_finished,
    rps_game_final_score,
    rps_game_winner,
    rps_game_tie
)
from utils.utils import create_rps_game, join_rps_game, make_rps_move, get_rps_game_state, send_seq_messages, finish_rps_game

router = Router()

class RPSStates(StatesGroup):
    WaitingForJoin = State()
    Playing = State()

# Map choice names to Russian
CHOICE_NAMES = {
    "rock": "Камень",
    "paper": "Бумага",
    "scissors": "Ножницы"
}

def rps_move_keyboard_inline(show_finish=True):
    """Create inline keyboard for RPS moves"""
    keyboard = [
        [
            InlineKeyboardButton(text="Камень 🪨", callback_data="rps_move_rock"),
            InlineKeyboardButton(text="Бумага 📄", callback_data="rps_move_paper"),
            InlineKeyboardButton(text="Ножницы ✂️", callback_data="rps_move_scissors")
        ]
    ]
    if show_finish:
        keyboard.append([
            InlineKeyboardButton(text=rps_finish_button, callback_data="rps_finish_game")
        ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@router.message(F.text == rps_button)
async def create_rps_handler(message: Message, bot: Bot, state: FSMContext):
    """Handle RPS game creation from games list"""
    user_id = message.from_user.id
    
    try:
        game = create_rps_game(user_id)
        invite_code = game["game_id"]  # game_id is now the invite_code
        
        await state.update_data(game_id=invite_code, player_number=1)
        await message.reply(
            f"Игра Камень-Ножницы-Бумага создана!\n"
            f"Код игры: {invite_code}\n"
            f"Ожидание второго игрока...\n\n"
            f"Отправьте этот код другу или подождите, пока кто-то присоединится.",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(RPSStates.WaitingForJoin)
        
        # Store invite_code in state for later use
        await state.update_data(game_id=invite_code)
        
    except ValueError as err:
        await message.reply(str(err))

@router.message(RPSStates.WaitingForJoin)
async def check_rps_game_joined(message: Message, bot: Bot, state: FSMContext):
    """Handle messages while waiting for player 2 to join"""
    data = await state.get_data()
    game_id = data.get("game_id")
    
    if not game_id:
        await message.reply("Ошибка: игра не найдена")
        await state.clear()
        return
    
    # Check if user is trying to join with a command or just checking status
    if message.text and message.text.startswith("/"):
        # Let other handlers process commands
        return
    
    try:
        game_state = get_rps_game_state(game_id)
        
        if game_state.get("player2_id") is not None:
            # Game has been joined, start playing
            player1_id = game_state["player1_id"]
            player2_id = game_state["player2_id"]
            
            await send_seq_messages(
                bot,
                [player1_id, player2_id],
                rps_game_started,
                reply_markup=rps_move_keyboard_inline(show_finish=True)
            )
            
            await state.set_state(RPSStates.Playing)
            await state.update_data(game_id=game_id)
        else:
            await message.reply(f"Ожидание второго игрока...\nКод игры: {game_id}\nДругой игрок может присоединиться командой: /rps_join {game_id}")
    except ValueError as err:
        await message.reply(str(err))

@router.callback_query(F.data.startswith("rps_move_"))
async def handle_rps_move(callback: CallbackQuery, bot: Bot, state: FSMContext):
    """Handle RPS move selection"""
    user_id = callback.from_user.id
    data = await state.get_data()
    game_id = data.get("game_id")
    
    if not game_id:
        await callback.answer("Ошибка: игра не найдена", show_alert=True)
        return
    
    # Extract choice from callback data
    choice_map = {
        "rps_move_rock": "rock",
        "rps_move_paper": "paper",
        "rps_move_scissors": "scissors"
    }
    choice = choice_map.get(callback.data)
    
    if not choice:
        await callback.answer("Неверный ход", show_alert=True)
        return
    
    try:
        result = make_rps_move(user_id, game_id, choice)
        game_state = result.get("new_state")
        
        if game_state:
            player1_id = game_state["player1_id"]
            player2_id = game_state.get("player2_id")
            player1_score = game_state["player1_score"]
            player2_score = game_state["player2_score"]
            round_result = result.get("round_result", "")
            
            choice_name = CHOICE_NAMES.get(choice, choice)
            
            # Send move confirmation
            await callback.message.edit_text(
                f"{rps_move_made.format(choice=choice_name)}\n\n"
                f"{rps_game_scores.format(player1_score=player1_score, player2_score=player2_score)}"
            )
            
            # If round is complete, send result to both players
            if round_result:
                result_message = (
                    f"{rps_round_result}\n{round_result}\n\n"
                    f"{rps_game_scores.format(player1_score=player1_score, player2_score=player2_score)}\n\n"
                    f"{rps_choose_move}"
                )
                
                await send_seq_messages(
                    bot,
                    [player1_id, player2_id],
                    result_message,
                    reply_markup=rps_move_keyboard_inline(show_finish=True)
                )
            else:
                # Waiting for opponent
                await callback.message.answer(rps_waiting_for_opponent)
        else:
            await callback.answer("Ход принят", show_alert=False)
            await callback.message.answer(rps_waiting_for_opponent)
            
    except ValueError as err:
        await callback.answer(str(err), show_alert=True)

@router.message(Command("rps_join"))
async def join_rps_command(message: Message, bot: Bot, state: FSMContext):
    """Join RPS game by command with invite code"""
    user_id = message.from_user.id
    command_parts = message.text.split()
    
    if len(command_parts) < 2:
        await message.reply("Использование: /rps_join <код_приглашения>\nПример: /rps_join 123456")
        return
    
    try:
        invite_code = int(command_parts[1])
        # Validate it's a 6-digit code
        if invite_code < 100000 or invite_code > 999999:
            await message.reply("Неверный код приглашения. Код должен быть 6-значным числом (100000-999999).\nПример: /rps_join 123456")
            return
            
        game = join_rps_game(user_id, invite_code)
        
        await state.update_data(game_id=invite_code, player_number=2)
        
        # Notify both players that game is starting
        player1_id = game["player1_id"]
        player2_id = game["player2_id"]
        
        await send_seq_messages(
            bot,
            [player1_id, player2_id],
            rps_game_started,
            reply_markup=rps_move_keyboard_inline(show_finish=True)
        )
        
        await state.set_state(RPSStates.Playing)
        
    except ValueError as e:
        error_msg = str(e)
        if "Игра не найдена" in error_msg or "not found" in error_msg.lower():
            await message.reply("Игра не найдена. Проверьте код приглашения.")
        elif "Неверный" in error_msg or "не число" in error_msg.lower():
            await message.reply("Неверный код приглашения. Используйте 6-значное число.\nПример: /rps_join 123456")
        else:
            await message.reply(error_msg)
    except Exception as err:
        await message.reply(f"Ошибка: {str(err)}")

@router.message(Command("rps_status"))
async def rps_status_command(message: Message, bot: Bot, state: FSMContext):
    """Check RPS game status"""
    data = await state.get_data()
    game_id = data.get("game_id")
    
    if not game_id:
        await message.reply("Вы не в игре. Создайте игру или присоединитесь к существующей.")
        return
    
    try:
        game_state = get_rps_game_state(game_id)
        player1_score = game_state["player1_score"]
        player2_score = game_state["player2_score"]
        status = game_state["status"]
        
        await message.reply(
            f"Статус игры: {status}\n"
            f"{rps_game_scores.format(player1_score=player1_score, player2_score=player2_score)}"
        )
    except ValueError as err:
        await message.reply(str(err))

@router.callback_query(F.data == "rps_finish_game")
async def handle_rps_finish(callback: CallbackQuery, bot: Bot, state: FSMContext):
    """Handle RPS game finish/end"""
    user_id = callback.from_user.id
    data = await state.get_data()
    game_id = data.get("game_id")
    
    if not game_id:
        await callback.answer("Ошибка: игра не найдена", show_alert=True)
        return
    
    try:
        game_state = finish_rps_game(user_id, game_id)
        player1_id = game_state["player1_id"]
        player2_id = game_state.get("player2_id")
        player1_score = game_state["player1_score"]
        player2_score = game_state["player2_score"]
        winner_id = game_state.get("winner")
        
        # Build final message
        final_message = f"{rps_game_finished}\n\n"
        final_message += f"{rps_game_final_score.format(player1_score=player1_score, player2_score=player2_score)}\n\n"
        
        if winner_id:
            if winner_id == player1_id:
                final_message += f"{rps_game_winner.format(player_num=1)}"
            else:
                final_message += f"{rps_game_winner.format(player_num=2)}"
        else:
            final_message += rps_game_tie
        
        # Send final message to both players
        await send_seq_messages(bot, [player1_id, player2_id], final_message)
        await callback.answer("Игра завершена!", show_alert=False)
        
        # Clear state
        await state.clear()
        
    except ValueError as err:
        await callback.answer(str(err), show_alert=True)

