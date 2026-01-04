import requests
from config import ADMIN_USER_ID
from utils.urls import game_engine_url, rps_service_url, diceladders_service_url

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

def get_game_type_by_code(invite_code):
    """Get game type from game engine by invite code"""
    try:
        code_int = int(invite_code)
        response = requests.get(f"{game_engine_url}/game/{code_int}/info")
        if response.status_code == 200:
            game_info = response.json()
            game_name = game_info.get("game_name")
            from loguru import logger
            logger.info(f"Retrieved game_name '{game_name}' for invite_code {code_int}")
            return game_name
        else:
            from loguru import logger
            logger.warning(f"Failed to get game info for invite_code {code_int}: {response.status_code}")
    except Exception as e:
        from loguru import logger
        logger.error(f"Error getting game type by code {invite_code}: {e}", exc_info=True)
    return None

def get_game_info_by_user(user_id):
    """Get game information from game engine by user_id"""
    try:
        response = requests.get(f"{game_engine_url}/user/{user_id}/game")
        if response.status_code == 200:
            game_info = response.json()
            from loguru import logger
            logger.info(f"Retrieved game info for user {user_id}: {game_info}")
            return game_info
        else:
            from loguru import logger
            logger.warning(f"Failed to get game info for user {user_id}: {response.status_code}")
    except Exception as e:
        from loguru import logger
        logger.error(f"Error getting game info by user {user_id}: {e}", exc_info=True)
    return None

def join_game(user_id, invite_code):
    """Join a game - game engine manages which game type is being played"""
    from loguru import logger
    # Convert invite_code to int if it's a string
    try:
        code_int = int(invite_code)
        logger.info(f"Join game: user_id={user_id}, invite_code={code_int}")
    except (ValueError, TypeError):
        raise ValueError("Код приглашения должен быть числом")
    
    # First, try to get game info from game engine to know the game type
    game_name = get_game_type_by_code(code_int)
    logger.info(f"Retrieved game_name: {game_name} for invite_code: {code_int}")
    
    # Try game engine first (for games managed by game engine like Monopoly, Dice-Ladders)
    payload = {"user_id": user_id, "invite_code": code_int}
    logger.info(f"Attempting to join game engine with payload: {payload}")
    response = requests.post(f"{game_engine_url}/join", json=payload)
    logger.info(f"Game engine join response: status={response.status_code}, body={response.text}")
    
    if response.status_code == 200:
        player_ids = response.json()
        logger.info(f"Successfully joined game engine. Player IDs: {player_ids}, game_name: {game_name}")
        # Return game info with game name so telegram bot knows which handlers to use
        return {
            "service": "game_engine",
            "game_name": game_name,
            "player_ids": player_ids if isinstance(player_ids, list) else []
        }
    elif response.status_code == 406:
        raise ValueError("Вы уже присоединены к другой игре")
    elif response.status_code == 404:
        # Game not found in game engine, try RPS service
        logger.info(f"Game not found in game engine (404), trying RPS service for code: {code_int}")
        if 100000 <= code_int <= 999999:
            # Try RPS service (RPS games are created directly, not through game engine)
            rps_payload = {"player2_id": user_id, "game_id": code_int}
            rps_response = requests.post(f"{rps_service_url}/join", json=rps_payload)
            logger.info(f"RPS join response: status={rps_response.status_code}")
            if rps_response.status_code == 200:
                game_data = rps_response.json()
                player1_id = game_data.get("player1_id")
                if player1_id:
                    logger.info(f"Successfully joined RPS game. Player1 ID: {player1_id}")
                    return {"service": "rps", "player_ids": [player1_id], "game_data": game_data}
        
        # Code not found in any service
        error_detail = response.text if hasattr(response, 'text') else "Unknown error"
        logger.error(f"Game not found in game engine. Response: {error_detail}")
        raise ValueError(f"Такого кода приглашения не существует: {error_detail}")
    
    # Code not found in any service
    error_detail = response.text if hasattr(response, 'text') else "Unknown error"
    logger.error(f"Failed to join game. Status: {response.status_code}, Response: {error_detail}")
    raise ValueError(f"Ошибка при присоединении к игре: {error_detail}")


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
    """Send messages to multiple users with error handling"""
    from loguru import logger
    import asyncio
    for id in user_ids:
        try:
            await bot.send_message(id, message, **kwargs)
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Error sending message to user {id}: {e}", exc_info=True)
            # Continue with other users even if one fails
            continue

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

def get_diceladders_game_state(game_id):
    """Get current dice-ladders game state"""
    response = requests.get(f"{diceladders_service_url}/{game_id}/state")
    if response.status_code == 404:
        raise ValueError("Игра не найдена")
    return response.json()

def get_diceladders_game_by_user(user_id):
    """Get diceladders game_id by user_id"""
    try:
        response = requests.get(f"{diceladders_service_url}/user/{user_id}/game")
        if response.status_code == 200:
            game_info = response.json()
            return game_info.get("game_id")
    except Exception as e:
        from loguru import logger
        logger.error(f"Error getting diceladders game by user {user_id}: {e}", exc_info=True)
    return None

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


