from typing import List, Tuple

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from utils.utils import is_admin
from utils.buttons import start_button, join_button
from utils.texts import start_keyboard_placeholder, default_placeholder



def make_keyboard_from_buttons(buttons : list[str], input_field_placeholder = default_placeholder) -> ReplyKeyboardMarkup:
    buttons = [KeyboardButton(text = item) for item in buttons]

    return ReplyKeyboardMarkup(keyboard=[
            *buttons
        ],
        resize_keyboard=True,
        input_field_placeholder=input_field_placeholder,
        selective=True
    )

def start_keyboard(user_id):
    admin = is_admin(user_id)
    buttons = [start_button, join_button]
    admin_buttons = []
    return make_keyboard_from_buttons(buttons=[*buttons, *admin_buttons],
                                      input_field_placeholder=start_keyboard_placeholder)