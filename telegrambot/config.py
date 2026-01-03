import os
import sys

from dotenv import load_dotenv

# Try to load from .env file (for local development)
# Docker Compose will inject env vars via env_file, so this is mainly for local dev
load_dotenv()

# Get TOKEN from environment (set by Docker Compose env_file or environment section)
TOKEN = os.getenv("TOKEN")

if not TOKEN or TOKEN.strip() == "":
    print("ERROR: TOKEN environment variable is not set!", file=sys.stderr)
    print("Please set the TOKEN environment variable in one of the following ways:", file=sys.stderr)
    print("1. Create a .env file in the telegrambot directory with: TOKEN=your_bot_token", file=sys.stderr)
    print("2. Set TOKEN environment variable in docker-compose.yml", file=sys.stderr)
    print("", file=sys.stderr)
    print("Current environment check:", file=sys.stderr)
    print(f"  TOKEN from os.getenv: '{TOKEN}'", file=sys.stderr)
    print(f"  Working directory: {os.getcwd()}", file=sys.stderr)
    env_file_path = os.path.join(os.getcwd(), ".env")
    print(f"  .env file path checked: {env_file_path}", file=sys.stderr)
    print(f"  .env file exists: {os.path.exists(env_file_path)}", file=sys.stderr)
    sys.exit(1)

# Get ADMIN_USER_ID from environment
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")
if ADMIN_USER_ID:
    try:
        ADMIN_USER_ID = int(ADMIN_USER_ID.strip())
    except ValueError:
        print("WARNING: ADMIN_USER_ID is not a valid integer, admin access will be disabled", file=sys.stderr)
        ADMIN_USER_ID = None
else:
    ADMIN_USER_ID = None