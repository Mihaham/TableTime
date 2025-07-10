import os
from dotenv import load_dotenv
load_dotenv()

DB_USER = os.getenv("POSTGRES_APP_USER")
DB_PASSWORD = os.getenv("POSTGRES_APP_PASSWORD")
DB_NAME = os.getenv("POSTGRES_DB")
DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@postgres:5432/{DB_NAME}"
