# TableTime Platform Structure

This document describes the structure and organization of the TableTime microservices platform.

## Services Overview

### Core Services

1. **API Gateway** (Port 8000)
   - Main entry point for all API requests
   - Routes requests to appropriate microservices
   - Location: `apigateway/`

2. **User Service** (Port 8002)
   - User management
   - Location: `userservice/`

3. **Game Engine** (Port 8003)
   - Game session management
   - Invite code generation and validation
   - Location: `gameengine/`

4. **Telegram Bot**
   - Telegram bot integration
   - User interface for games
   - Location: `telegrambot/`

### Game Services

Each game is a separate microservice:

1. **Monopoly Service** (Port 8004)
   - Location: `games/monopoly/`

2. **Rock Paper Scissors Service** (Port 8006)
   - Location: `games/rps/`

## Directory Structure

```
TableTime-1/
├── apigateway/          # API Gateway service
│   ├── app/
│   │   ├── config.py    # Service URLs configuration
│   │   ├── routes.py    # Routing logic
│   │   └── main.py      # FastAPI app
│   ├── Dockerfile
│   └── requirements.txt
│
├── userservice/         # User Service
│   ├── app/
│   │   ├── endpoints/
│   │   │   └── users.py # User CRUD endpoints
│   │   ├── models.py    # User models
│   │   └── main.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── gameengine/          # Game Engine
│   ├── app/
│   │   ├── endpoints/
│   │   │   └── game_creation.py
│   │   ├── GamesEngine/
│   │   │   └── Games.py
│   │   └── main.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── games/               # Game services directory
│   ├── _TEMPLATE/       # Template for new games (DO NOT DELETE)
│   ├── monopoly/        # Monopoly game service
│   └── rps/             # Rock Paper Scissors game service
│
├── telegrambot/         # Telegram Bot
│   ├── handlers/        # Message handlers
│   │   ├── admin.py     # Admin commands
│   │   ├── users.py     # User commands
│   │   └── rps.py       # RPS game handler
│   ├── utils/           # Utilities
│   │   ├── buttons.py   # Button text definitions
│   │   ├── keyboard.py  # Keyboard builders
│   │   ├── texts.py     # Text messages
│   │   ├── urls.py      # Service URLs
│   │   ├── utils.py     # Helper functions
│   │   └── game_config.py # Game configuration
│   ├── config.py        # Bot configuration
│   ├── main.py          # Bot entry point
│   └── Dockerfile
│
├── docker-compose.yml   # Docker Compose configuration
├── GAME_TEMPLATE.md     # Guide for adding new games
└── README.md            # Main documentation
```

## Game Service Structure

Each game service follows this structure:

```
games/game_name/
├── app/
│   ├── __init__.py
│   ├── endpoints/
│   │   ├── __init__.py
│   │   └── game.py      # Game logic endpoints
│   ├── models.py        # Pydantic models
│   └── main.py          # FastAPI app setup
├── Dockerfile
└── requirements.txt
```

### Required Endpoints

Every game service must implement:

- `POST /create` - Create a new game
- `POST /join` - Join an existing game
- `POST /action` - Perform a game action
- `GET /{game_id}/state` - Get current game state
- `GET /{game_id}/status` - Get game status
- `POST /finish` - Finish a game (recommended)

### Game Models

Required models:

- `GameState` - Current game state
- `GameAction` - Player action
- `GameActionResponse` - Action response
- `CreateGameRequest` - Create game request
- `JoinGameRequest` - Join game request
- `FinishGameRequest` - Finish game request (optional)

## Adding a New Game

1. **Copy the template:**
   ```bash
   cp -r games/_TEMPLATE games/your_game_name
   ```

2. **Customize the template:**
   - Replace `your_game_name` with your game name
   - Implement game logic in `app/endpoints/game.py`
   - Define models in `app/models.py`

3. **Add to docker-compose.yml:**
   - Add service configuration
   - Use next available port

4. **Add to API Gateway:**
   - Update `apigateway/app/config.py`
   - Add route in `apigateway/app/routes.py`

5. **Add to Telegram Bot:**
   - Update `telegrambot/utils/buttons.py`
   - Update `telegrambot/utils/game_config.py`
   - Create handler in `telegrambot/handlers/your_game.py`
   - Update `telegrambot/main.py`

See `GAME_TEMPLATE.md` for detailed instructions.

## Important Conventions

1. **Invite Codes**: All games use 6-digit codes (100000-999999)
2. **Game ID**: Use invite_code as game_id in GameState
3. **Status Values**: Use "waiting", "playing", "finished"
4. **Service Names**: Use lowercase, no spaces
5. **Port Numbers**: Sequential starting from 8004 (monopoly=8004, rps=8006, next=8007)

## Service Communication

Services communicate through the API Gateway:

- All external requests → API Gateway (Port 8000)
- API Gateway → Individual services
- Services → Services (through API Gateway)

## Network

All services are on the `game-network` Docker network.

Service URLs use service names (e.g., `http://gameengine:8000`).

## Key Files

- `docker-compose.yml` - Service orchestration
- `GAME_TEMPLATE.md` - Guide for adding games
- `games/_TEMPLATE/` - Game template directory
- `telegrambot/utils/game_config.py` - Game registry
- `apigateway/app/config.py` - Service URLs
- `apigateway/app/routes.py` - Routing rules

