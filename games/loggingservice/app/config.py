import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
POSTGRES_USER = os.getenv("POSTGRES_APP_USER", "app_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_APP_PASSWORD", "app_password")
POSTGRES_DB = os.getenv("POSTGRES_DB", "tabletime_db")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "database")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

