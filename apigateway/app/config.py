import os
from dotenv import load_dotenv

load_dotenv()

# Service URLs
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://userservice:8000")
GAME_ENGINE_SERVICE_URL = os.getenv("GAME_ENGINE_SERVICE_URL", "http://gameengine:8000")
MONOPOLY_SERVICE_URL = os.getenv("MONOPOLY_SERVICE_URL", "http://monopoly:8000")
DATABASE_INTERFACE_SERVICE_URL = os.getenv("DATABASE_INTERFACE_SERVICE_URL", "http://databaseinterface:8000")
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://notificationservice:8000")

