import requests
from config import ADMIN_USER_ID
from utils.urls import game_engine_url, rps_service_url

def is_admin(user_id):
    """Check if user is admin based on ADMIN_USER_ID from config"""
    if ADMIN_USER_ID is None:
        return False
    return user_id == ADMIN_USER_ID


def create_game(user_id, name):
    payload = {"user_id" : user_id, "game" : name}
    response = requests.post(f"{game_engine_url}/create", json = payload)
    if response.status_code != 200:
        pass
    return response.json()['invite_code']

def join_game(user_id, invite_code):
    """Join a game - tries game engine first, then RPS service"""
    # Convert invite_code to int if it's a string
    try:
        code_int = int(invite_code)
    except (ValueError, TypeError):
        raise ValueError("Код приглашения должен быть числом")
    
    # First try game engine
    payload = {"user_id": user_id, "invite_code": code_int}
    response = requests.post(f"{game_engine_url}/join", json=payload)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 406:
        raise ValueError("Вы уже присоединены к другой игре")
    
    # If not found in game engine, try RPS service (for 6-digit codes)
    if 100000 <= code_int <= 999999:
        rps_payload = {"player2_id": user_id, "game_id": code_int}
        rps_response = requests.post(f"{rps_service_url}/join", json=rps_payload)
        if rps_response.status_code == 200:
            # Return format compatible with game engine join
            game_data = rps_response.json()
            # Extract player1_id to notify them
            player1_id = game_data.get("player1_id")
            if player1_id:
                return [player1_id]  # Return list of user IDs to notify (like game engine does)
        elif rps_response.status_code == 404:
            raise ValueError("Такого кода приглашения не существует")
        elif rps_response.status_code == 400:
            error_detail = rps_response.json().get("detail", "Не удалось присоединиться к игре")
            raise ValueError(error_detail)
    
    # Code not found in either service
    raise ValueError("Такого кода приглашения не существует")


def check_button(button : str, list_buttons : list):
    return bool(button in list_buttons)

def start_game(user_id):
    payload = {"user_id" : user_id}
    response = requests.post(f"{game_engine_url}/start", json = payload)
    if response.status_code == 404:
        raise ValueError("Вы не присоединены ни к одной игре")
    elif response.status_code == 406:
        raise ValueError("Вы не являетесь хостом в игре")
    return response.json()


async def send_seq_messages(bot, user_ids, message, **kwargs):
    for id in user_ids:
        await bot.send_message(id, message, **kwargs)

# RPS Game Functions
def create_rps_game(player1_id):
    """Create a new RPS game"""
    payload = {"player1_id": player1_id}
    response = requests.post(f"{rps_service_url}/create", json=payload)
    if response.status_code != 200:
        raise ValueError("Не удалось создать игру")
    return response.json()

def join_rps_game(player2_id, game_id):
    """Join an existing RPS game"""
    payload = {"player2_id": player2_id, "game_id": game_id}
    response = requests.post(f"{rps_service_url}/join", json=payload)
    if response.status_code == 404:
        raise ValueError("Игра не найдена")
    elif response.status_code == 400:
        error_msg = response.json().get("detail", "Не удалось присоединиться к игре")
        raise ValueError(error_msg)
    return response.json()

def make_rps_move(user_id, game_id, choice):
    """Make a move in RPS game"""
    payload = {"user_id": user_id, "game_id": game_id, "choice": choice}
    response = requests.post(f"{rps_service_url}/action", json=payload)
    if response.status_code == 404:
        raise ValueError("Игра не найдена")
    elif response.status_code == 403:
        raise ValueError("Вы не участвуете в этой игре")
    elif response.status_code == 400:
        error_msg = response.json().get("detail", "Неверный ход")
        raise ValueError(error_msg)
    return response.json()

def get_rps_game_state(game_id):
    """Get current RPS game state"""
    response = requests.get(f"{rps_service_url}/{game_id}/state")
    if response.status_code == 404:
        raise ValueError("Игра не найдена")
    return response.json()

def finish_rps_game(user_id, game_id):
    """Finish/end an RPS game"""
    payload = {"user_id": user_id, "game_id": game_id}
    response = requests.post(f"{rps_service_url}/finish", json=payload)
    if response.status_code == 404:
        raise ValueError("Игра не найдена")
    elif response.status_code == 403:
        raise ValueError("Вы не участвуете в этой игре")
    return response.json()

def list_rps_games():
    """List available RPS games waiting for player 2"""
    response = requests.get(f"{rps_service_url}/")
    if response.status_code != 200:
        return []
    return response.json().get("games", [])


