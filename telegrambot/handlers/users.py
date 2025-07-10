from aiogram import Router, F, Bot
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import Command

from texts import start_text
from utils.keyboard import start_keyboard, games_keyboard
from utils.buttons import create_button, join_button
from utils.texts import games_placeholder, join_text

router = Router()



@router.message(Command("start"))
async def start(bot : Bot, message : Message):
    user_id = message.from_user.id
    await message.reply(f"Привет, {message.from_user.username}!\n{start_text}", reply_markup=start_keyboard(user_id))

@router.message(Command("create_game"))


@router.message(Command("join"))
@router.message(F.text == join_button)
async def join(bot : Bot, message : Message):
    user_id = message.from_user.id
    await message.reply(join_text, reply_markup=ReplyKeyboardRemove())


@router.message(Command("create"))
@router.message(F.text == create_button)
async def create(bot : Bot, message : Message):
    user_id = message.from_user.id
    await message.reply(games_placeholder, reply_markup=games_keyboard(user_id))
