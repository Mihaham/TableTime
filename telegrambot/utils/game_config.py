"""
Game Configuration - Central registry for all games
Add new games here to make them available in the bot
"""

# Game service mappings - maps game name to service URL
GAME_SERVICES = {
    "Монополия 🏦": {
        "service_name": "monopoly",
        "service_url": "http://apigateway:8000/api/v1/monopoly",
        "needs_separate_join": False  # Uses game engine only
    },
    "Камень Ножницы Бумага ✂️": {
        "service_name": "rps",
        "service_url": "http://apigateway:8000/api/v1/rps",
        "needs_separate_join": False  # Will use game engine
    },
    "Кости и Лестницы 🎲": {
        "service_name": "diceladders",
        "service_url": "http://apigateway:8000/api/v1/diceladders",
        "needs_separate_join": False  # Will use game engine
    }
}

def get_game_service_config(game_name: str):
    """Get service configuration for a game"""
    return GAME_SERVICES.get(game_name)

def get_all_game_names():
    """Get list of all available game names"""
    return list(GAME_SERVICES.keys())

