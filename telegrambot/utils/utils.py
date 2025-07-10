import requests
from utils.urls import databaseinterface_url, game_engine_url

def is_admin(user_id):
    return False #Пока не реализован database_interface


def create_game(user_id, name):
    payload = {"user_id" : user_id, "game" : name}
    response = requests.post(f"{game_engine_url}/create", json = payload)
    if response.status_code != 200:
        pass
    return response.json()['invite_code']

def join_game(user_id, invite_code):
    payload = {"user_id" : user_id, "invite_code" : invite_code}
    response = requests.post(f"{game_engine_url}/join", json = payload)
    if response.status_code == 404:
        raise ValueError("Такого кода приглашения не существует")
    elif response.status_code == 406:
        raise ValueError("Вы уже присоединены к другой игре")


def check_button(button : str, list_buttons : list):
    return bool(button in list_buttons)


