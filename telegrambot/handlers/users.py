from aiogram import Router, F, Bot
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from utils.keyboard import start_keyboard, games_keyboard, game_start_keyboard
from utils.buttons import create_button, join_button, games_buttons, start_button, rps_button
from utils.texts import start_text, games_placeholder, join_text, game_creation_text, success_join, game_is_starting, user_joined_text
from utils.utils import create_game, join_game, check_button, send_seq_messages, start_game, get_rps_game_state

router = Router()

class UserStates(StatesGroup):
    WaitingInviteCode = State()
    InGame = State()
    PlayingGame = State()



@router.message(Command("start"))
async def start(message : Message, bot : Bot, state: FSMContext):
    user_id = message.from_user.id
    await message.reply(f"Привет, {message.from_user.username}!\n{start_text}", reply_markup=start_keyboard(user_id))

@router.message(Command("create_game"))


@router.message(Command("join"))
@router.message(F.text == join_button)
async def join(message : Message, bot : Bot, state: FSMContext):
    user_id = message.from_user.id
    await message.reply(join_text, reply_markup=ReplyKeyboardRemove())
    await state.set_state(UserStates.WaitingInviteCode)


@router.message(Command("create"))
@router.message(F.text == create_button)
async def create(message : Message, bot : Bot, state: FSMContext):
    user_id = message.from_user.id
    await message.reply(games_placeholder, reply_markup=games_keyboard(user_id))

@router.message(lambda message: message.text and message.text in games_buttons and message.text != rps_button)
async def game_creation(message : Message, bot : Bot, state: FSMContext):
    user_id = message.from_user.id
    invite_code = create_game(user_id, message.text)

    await message.reply(f"{game_creation_text} {invite_code}", reply_markup=game_start_keyboard(user_id))
    await state.set_state(UserStates.InGame)

@router.message(UserStates.WaitingInviteCode)
async def games_joining(message : Message, bot : Bot, state: FSMContext):
    user_id = message.from_user.id
    try:
        invite_code = message.text.strip()
        # Validate it's a number
        try:
            code_int = int(invite_code)
        except ValueError:
            await message.reply("Код приглашения должен быть числом")
            return
        
        ids = join_game(user_id, invite_code)
        
        # Check if this is an RPS game (6-digit code, and join_game returned a list with one ID)
        if 100000 <= code_int <= 999999 and isinstance(ids, list) and len(ids) == 1:
            # This might be an RPS game - try to get the game state to confirm
            try:
                game_state = get_rps_game_state(code_int)
                if game_state.get("status") == "playing" and game_state.get("player2_id") == user_id:
                    # RPS game - switch to RPS handler flow
                    from handlers.rps import RPSStates
                    from utils.texts import rps_game_started
                    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                    
                    from handlers.rps import rps_move_keyboard_inline
                    
                    player1_id = game_state["player1_id"]
                    player2_id = game_state.get("player2_id")
                    
                    # Successfully joined RPS game
                    await state.update_data(game_id=code_int, player_number=2)
                    await send_seq_messages(bot, [player1_id, player2_id], f"{user_joined_text} {message.from_user.username}")
                    await send_seq_messages(bot, [player1_id, player2_id], rps_game_started, reply_markup=rps_move_keyboard_inline(show_finish=True))
                    await state.set_state(RPSStates.Playing)
                    return
            except:
                # Not an RPS game or error, continue with normal flow
                pass
        
        # Normal game flow (through game engine)
        await send_seq_messages(bot, ids, f"{user_joined_text} {message.from_user.username}")
        await message.reply(success_join)
        await state.set_state(UserStates.InGame)
    except ValueError as err:
        await message.reply(str(err))
        return

@router.message(F.text == start_button)
async def start_game_handler(message : Message, bot : Bot, state: FSMContext):
    user_id = message.from_user.id
    try:
        ids = start_game(user_id)
        await send_seq_messages(bot, ids, game_is_starting, reply_markup=ReplyKeyboardRemove())
    except ValueError as err:
        await message.reply(str(err))
        return

    #for id in ids:
    #    await bot.set_state(UserStates.PlayingGame)

