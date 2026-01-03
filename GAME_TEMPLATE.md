# Game Template Guide

This guide explains how to add a new game to the TableTime platform.

## Game Structure

Each game should follow this structure:

```
games/
  your_game_name/
    app/
      __init__.py (empty file)
      endpoints/
        __init__.py (empty file)
        game.py (game logic endpoints)
      main.py (FastAPI app setup)
      models.py (Pydantic models)
    Dockerfile (standard Dockerfile)
    requirements.txt (dependencies)
```

## Step-by-Step Guide

### 1. Create Game Directory Structure

```bash
mkdir -p games/your_game_name/app/endpoints
touch games/your_game_name/app/__init__.py
touch games/your_game_name/app/endpoints/__init__.py
```

### 2. Create `requirements.txt`

```txt
fastapi
uvicorn[standard]
pydantic
httpx
```

### 3. Create `Dockerfile`

```dockerfile
# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY ./app ./app

# Открываем порт 8000
EXPOSE 8000

# Команда запуска сервера
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 4. Create `app/models.py`

**If using template**: Edit `games/your_game_name/app/models.py` and customize it.

**If creating from scratch**: Copy from `games/_TEMPLATE/app/models.py` or use this template:

```python
from pydantic import BaseModel
from typing import Optional, Dict, Any

class GameState(BaseModel):
    """Current state of the game"""
    game_id: int  # This will be the invite_code (6-digit)
    player1_id: int
    player2_id: Optional[int] = None
    status: str  # "waiting", "playing", "finished"
    # Add your game-specific fields here
    
class GameAction(BaseModel):
    """Action a player takes in the game"""
    user_id: int
    game_id: int
    # Add action-specific fields here
    
class GameActionResponse(BaseModel):
    """Response from performing an action"""
    success: bool
    message: str
    new_state: Optional[GameState] = None
    # Add additional response fields as needed

class CreateGameRequest(BaseModel):
    """Request to create a new game"""
    player1_id: int

class JoinGameRequest(BaseModel):
    """Request to join a game"""
    player2_id: int
    game_id: int  # This is the invite_code

class FinishGameRequest(BaseModel):
    """Request to finish a game (optional)"""
    user_id: int
    game_id: int
```

### 5. Create `app/endpoints/game.py`

**If using template**: Edit `games/your_game_name/app/endpoints/game.py` and implement your logic.

**If creating from scratch**: Copy from `games/_TEMPLATE/app/endpoints/game.py` or implement required endpoints:

```python
from fastapi import APIRouter, HTTPException
from app.models import (
    GameState,
    GameAction,
    GameActionResponse,
    CreateGameRequest,
    JoinGameRequest,
    FinishGameRequest  # Optional
)
from typing import Dict
import random

router = APIRouter()

# In-memory game storage (key is invite_code)
games: Dict[int, GameState] = {}

@router.post("/create", response_model=GameState)
async def create_game(request: CreateGameRequest):
    """Create a new game"""
    # Generate 6-digit invite code (same format as all games)
    invite_code = random.randint(100000, 999999)
    
    # Ensure unique invite code
    while invite_code in games:
        invite_code = random.randint(100000, 999999)
    
    # Create game state
    game = GameState(
        game_id=invite_code,  # Use invite_code as game_id
        # Initialize your game state
        status="waiting"
    )
    
    games[invite_code] = game
    return game

@router.post("/join", response_model=GameState)
async def join_game(request: JoinGameRequest):
    """Join an existing game"""
    if request.game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[request.game_id]
    
    # Validate game can be joined
    if game.status != "waiting":
        raise HTTPException(status_code=400, detail="Game is not waiting for players")
    
    # Add player 2
    # Update game state...
    game.status = "playing"
    
    return game

@router.post("/action", response_model=GameActionResponse)
async def perform_action(action: GameAction):
    """Perform a game action"""
    if action.game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[action.game_id]
    
    # Validate player is in the game
    # Implement your game logic here
    
    return GameActionResponse(
        success=True,
        message="Action performed",
        new_state=game
    )

@router.get("/{game_id}/state", response_model=GameState)
async def get_game_state(game_id: int):
    """Get current game state"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    return games[game_id]

@router.get("/{game_id}/status")
async def get_game_status(game_id: int):
    """Get game status"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    game = games[game_id]
    return {
        "game_id": game_id,
        "status": game.status,
        # Add other status fields
    }
```

### 6. Create `app/main.py`

```python
from fastapi import FastAPI
from app.endpoints import game

app = FastAPI(
    title="Your Game Name Service",
    version="0.1.0",
    description="Microservice for Your Game Name game logic"
)

app.include_router(
    game.router,
    prefix="/api/v1/your_game_name",  # Use lowercase, no spaces
    tags=["your_game_name"]
)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "your_game_name"}
```

### 7. Add to `docker-compose.yml`

Add your service to `docker-compose.yml`:

```yaml
  your_game_name:
    build:
      context: ./games/your_game_name
    depends_on:
      - gameengine
    ports:
      - "8007:8000"  # Use next available port
    networks:
      - game-network
```

### 8. Add to API Gateway

#### Update `apigateway/app/config.py`:

```python
YOUR_GAME_SERVICE_URL = os.getenv("YOUR_GAME_SERVICE_URL", "http://your_game_name:8000")
```

#### Update `apigateway/app/routes.py`:

Add import:
```python
from app.config import (
    # ... existing imports
    YOUR_GAME_SERVICE_URL
)
```

Add route:
```python
@router.api_route("/api/v1/your_game_name/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_your_game(path: str, request: Request):
    return await proxy_request(YOUR_GAME_SERVICE_URL, f"/api/v1/your_game_name/{path}", request.method, request)
```

#### Update `docker-compose.yml` for apigateway:

Add to environment variables:
```yaml
environment:
  # ... existing vars
  - YOUR_GAME_SERVICE_URL=http://your_game_name:8000
```

Add to depends_on:
```yaml
depends_on:
  # ... existing services
  - your_game_name
```

### 9. Add to Telegram Bot

#### Update `telegrambot/utils/buttons.py`:

```python
your_game_button = "Your Game Name 🎮"
games_buttons = [monopoly_button, rps_button, your_game_button]
```

#### Update `telegrambot/utils/game_config.py`:

```python
GAME_SERVICES = {
    # ... existing games
    "Your Game Name 🎮": {
        "service_name": "your_game_name",
        "service_url": "http://apigateway:8000/api/v1/your_game_name",
        "needs_separate_join": False
    }
}
```

#### Update `telegrambot/utils/urls.py` (if needed):

```python
your_game_service_url = "http://apigateway:8000/api/v1/your_game_name"
```

#### Create `telegrambot/handlers/your_game.py`:

Create a handler file similar to `rps.py` but for your game.

#### Update `telegrambot/main.py`:

```python
from handlers import admin, users, rps, your_game

routers = (admin.router, users.router, rps.router, your_game.router)
```

#### Update `telegrambot/utils/utils.py`:

Add utility functions for your game (create_game, join_game, etc.)

### 10. Update Admin Panel (Optional)

Update `telegrambot/handlers/admin.py`:

Add to `MICROSERVICES`:
```python
"Your Game Service": "http://your_game_name:8000/health",
```

## Important Notes

1. **Invite Codes**: All games must use 6-digit invite codes (100000-999999) for consistency
2. **Game ID**: Use the invite_code as the game_id in your GameState
3. **Join Flow**: All games use the unified join flow through the game engine
4. **Status Values**: Use consistent status values: "waiting", "playing", "finished"
5. **Service Name**: Use lowercase, no spaces for service names (e.g., "your_game_name")
6. **Port Numbers**: Use sequential ports starting from 8004 (monopoly=8004, rps=8006, next=8007, etc.)

## Testing

After adding your game:

1. Build and start services: `docker-compose up --build`
2. Check health: `curl http://localhost:8007/health`
3. Test via API Gateway: `curl http://localhost:8000/api/v1/your_game_name/health`
4. Test in Telegram bot: Create and join a game

## Example: RPS Game

See `games/rps/` for a complete working example of a game implementation.

