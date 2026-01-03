from typing import List, Tuple

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from utils.utils import is_admin
from utils.buttons import (
    start_button, join_button, monopoly_button, games_buttons, create_button,
    admin_status_button, admin_back_button, admin_buttons
)
from utils.texts import start_keyboard_placeholder, default_placeholder, games_placeholder, game_start_placeholder



def make_keyboard_from_buttons(buttons : list[str], input_field_placeholder = default_placeholder) -> ReplyKeyboardMarkup:
    Keyboardbuttons = [list([KeyboardButton(text = item)]) for item in buttons]

    return ReplyKeyboardMarkup(keyboard=Keyboardbuttons,
        resize_keyboard=True,
        input_field_placeholder=input_field_placeholder,
        selective=True
    )

def start_keyboard(user_id):
    admin = is_admin(user_id)
    buttons = [create_button, join_button]
    admin_btns = admin_buttons if admin else []
    return make_keyboard_from_buttons(buttons=[*buttons, *admin_btns],
                                      input_field_placeholder=start_keyboard_placeholder)


def games_keyboard(user_id):
    admin = is_admin(user_id)
    buttons = games_buttons
    admin_btns = admin_buttons if admin else []
    return make_keyboard_from_buttons(buttons=[*buttons, *admin_btns],
                                      input_field_placeholder=games_placeholder)

def game_start_keyboard(user_id):
    admin = is_admin(user_id)
    buttons = [start_button]
    admin_btns = admin_buttons if admin else []
    return make_keyboard_from_buttons(buttons=[*buttons, *admin_btns],
                                      input_field_placeholder=game_start_placeholder)

def admin_keyboard(user_id):
    """Admin panel keyboard"""
    buttons = [admin_status_button, admin_back_button]
    return make_keyboard_from_buttons(buttons=buttons,
                                      input_field_placeholder="Выберите действие администратора")