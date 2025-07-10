from aiogram import Router, F, Bot
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from utils.keyboard import start_keyboard, games_keyboard, game_start_keyboard
from utils.buttons import create_button, join_button, games_buttons, start_button
from utils.texts import start_text, games_placeholder, join_text, game_creation_text, success_join, game_is_starting, user_joined_text
from utils.utils import create_game, join_game, check_button, send_seq_messages, start_game

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

@router.message(lambda message: message.text and message.text in games_buttons)
async def game_creation(message : Message, bot : Bot, state: FSMContext):
    user_id = message.from_user.id
    invite_code = create_game(user_id, message.text)

    await message.reply(f"{game_creation_text} {invite_code}", reply_markup=game_start_keyboard(user_id))
    await state.set_state(UserStates.InGame)

@router.message(UserStates.WaitingInviteCode)
async def games_joining(message : Message, bot : Bot, state: FSMContext):
    user_id = message.from_user.id
    try:
        ids = join_game(user_id, message.text)
        await send_seq_messages(bot, ids, f"{user_joined_text} {message.from_user.username}")
    except ValueError as err:
        await message.reply(str(err))
        return
    await message.reply(success_join)
    await state.set_state(UserStates.InGame)

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

