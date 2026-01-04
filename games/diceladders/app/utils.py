import requests
import os

LOGGING_SERVICE_URL = os.getenv("LOGGING_SERVICE_URL", "http://apigateway:8000/api/v1/logs")

def log_game_creation(game_id: int, creator_user_id: int, invite_code: int):
    """Log game creation event"""
    try:
        payload = {
            "game_id": game_id,
            "game_type": "diceladders",
            "creator_user_id": creator_user_id,
            "invite_code": invite_code
        }
        requests.post(f"{LOGGING_SERVICE_URL}/creation", json=payload, timeout=1)
    except Exception as e:
        print(f"Logging error (creation): {e}")
        pass  # Fail silently if logging fails

def log_game_join(game_id: int, user_id: int):
    """Log game join event"""
    try:
        payload = {
            "game_id": game_id,
            "game_type": "diceladders",
            "user_id": user_id
        }
        requests.post(f"{LOGGING_SERVICE_URL}/join", json=payload, timeout=1)
    except Exception as e:
        print(f"Logging error (join): {e}")
        pass

def log_game_action(game_id: int, user_id: int, action_type: str, action_data: dict = None):
    """Log game action event with detailed information"""
    try:
        payload = {
            "game_id": game_id,
            "game_type": "diceladders",
            "user_id": user_id,
            "action_type": action_type,
            "action_data": action_data or {}
        }
        requests.post(f"{LOGGING_SERVICE_URL}/action", json=payload, timeout=2)
    except Exception as e:
        print(f"Logging error (action): {e}")
        pass

def log_game_finish(game_id: int, finished_by_user_id: int, winner_user_id: int = None, final_state: dict = None):
    """Log game finish event with detailed information"""
    try:
        payload = {
            "game_id": game_id,
            "game_type": "diceladders",
            "finished_by_user_id": finished_by_user_id,
            "winner_user_id": winner_user_id,
            "final_state": final_state or {}
        }
        requests.post(f"{LOGGING_SERVICE_URL}/finish", json=payload, timeout=2)
    except Exception as e:
        print(f"Logging error (finish): {e}")
        pass

