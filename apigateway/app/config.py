import os
from dotenv import load_dotenv

load_dotenv()

# Service URLs
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://userservice:8000")
GAME_ENGINE_SERVICE_URL = os.getenv("GAME_ENGINE_SERVICE_URL", "http://gameengine:8000")
MONOPOLY_SERVICE_URL = os.getenv("MONOPOLY_SERVICE_URL", "http://monopoly:8000")
RPS_SERVICE_URL = os.getenv("RPS_SERVICE_URL", "http://rps:8000")
DICELADDERS_SERVICE_URL = os.getenv("DICELADDERS_SERVICE_URL", "http://diceladders:8000")
LOGGING_SERVICE_URL = os.getenv("LOGGING_SERVICE_URL", "http://loggingservice:8000")

