# TableTime Platform Architecture

This document describes the architecture and service communication flow of the TableTime microservices platform.

## Service Communication Flow

### Request Flow Diagram

```
User (Telegram)
    ↓
Telegram Bot
    ↓
API Gateway (Port 8000)
    ↓
    ├─→ User Service (Port 8002)
    │
    ├─→ Game Engine (Port 8003)
    │       │
    │       └─→ Database (PostgreSQL)
    │
    ├─→ Monopoly Service (Port 8004)
    │       │
    │       └─→ Game Engine
    │
    ├─→ RPS Service (Port 8006)
    │       │
    │       ├─→ Game Engine
    │       └─→ Logging Service
    │
    └─→ Logging Service (Port 8007)
            │
            └─→ Database (PostgreSQL)
```

## Detailed Service Communication

### 1. User Requests (Telegram Bot → API Gateway → Services)

**Telegram Bot** → **API Gateway** → **Game Engine** / **User Service** / **Game Services**

- User sends message to Telegram Bot
- Telegram Bot forwards requests to API Gateway
- API Gateway routes to appropriate service:
  - `/api/v1/users/*` → User Service
  - `/api/v1/game/*` → Game Engine
  - `/api/v1/monopoly/*` → Monopoly Service
  - `/api/v1/rps/*` → RPS Service
  - `/api/v1/logs/*` → Logging Service

### 2. Game Creation Flow

```
User (Telegram)
    ↓
Telegram Bot
    ↓
API Gateway
    ↓
Game Engine / Game Service (RPS/Monopoly)
    ↓
Logging Service (for RPS)
    ↓
Database (Logs)
```

### 3. Game Join Flow

```
User (Telegram)
    ↓
Telegram Bot
    ↓
API Gateway
    ↓
Game Engine (primary) or RPS Service (fallback for 6-digit codes)
    ↓
Logging Service (for RPS)
    ↓
Database (Logs)
```

### 4. Game Action Flow (RPS Example)

```
User (Telegram)
    ↓
Telegram Bot
    ↓
API Gateway
    ↓
RPS Service
    ↓
    ├─→ Process game action
    └─→ Logging Service (async)
            ↓
        Database (Logs)
```

### 5. Admin Logs View Flow

```
Admin User (Telegram)
    ↓
Telegram Bot
    ↓
API Gateway
    ↓
Logging Service
    ↓
Database (Read logs)
    ↓
Telegram Bot (Display to admin)
```

## Service Dependencies

### Database Dependencies
- **Logging Service** → Database (direct connection)
- **Game Engine** → Database (via direct connection if needed)

### Inter-Service Dependencies

1. **API Gateway** depends on:
   - User Service
   - Game Engine
   - Monopoly Service
   - RPS Service
   - Logging Service

2. **RPS Service** depends on:
   - Game Engine (for unified join flow)
   - Logging Service (for event logging)

3. **Monopoly Service** depends on:
   - Game Engine

4. **Logging Service** depends on:
   - Database (health check)

5. **Telegram Bot** depends on:
   - API Gateway
   - User Service

## Network Architecture

All services communicate through the `game-network` Docker network.

### Internal Communication
- Services use service names for communication (e.g., `http://apigateway:8000`)
- All requests go through API Gateway for external access
- Internal services can communicate directly using service names

### External Access
- **Port 8000**: API Gateway (main entry point)
- **Port 8002**: User Service (direct access for debugging)
- **Port 8003**: Game Engine (direct access for debugging)
- **Port 8004**: Monopoly Service (direct access for debugging)
- **Port 8006**: RPS Service (direct access for debugging)
- **Port 8007**: Logging Service (direct access for debugging)

## Data Flow Examples

### Example 1: Creating an RPS Game

1. User clicks "Камень Ножницы Бумага ✂️" in Telegram
2. Telegram Bot → API Gateway → RPS Service (`POST /api/v1/rps/create`)
3. RPS Service creates game, generates invite code
4. RPS Service → Logging Service (`POST /api/v1/logs/creation`)
5. Logging Service → Database (store creation log)
6. RPS Service returns game state to Telegram Bot
7. Telegram Bot displays invite code to user

### Example 2: Joining an RPS Game

1. User enters invite code in Telegram
2. Telegram Bot → API Gateway → Game Engine (`POST /api/v1/game/join`)
3. Game Engine checks game (not found for 6-digit codes)
4. Telegram Bot → API Gateway → RPS Service (`POST /api/v1/rps/join`)
5. RPS Service adds player 2
6. RPS Service → Logging Service (`POST /api/v1/logs/join`)
7. Logging Service → Database (store join log)
8. RPS Service returns game state
9. Telegram Bot notifies both players

### Example 3: Making a Move in RPS

1. User clicks move button (Rock/Paper/Scissors)
2. Telegram Bot → API Gateway → RPS Service (`POST /api/v1/rps/action`)
3. RPS Service processes move
4. RPS Service → Logging Service (`POST /api/v1/logs/action`) - async
5. Logging Service → Database (store action log)
6. RPS Service returns game state
7. Telegram Bot updates both players

### Example 4: Admin Viewing Logs

1. Admin clicks "📋 Логи игр" in Telegram
2. Telegram Bot → API Gateway → Logging Service (`GET /api/v1/logs/all`)
3. Logging Service → Database (query all log tables)
4. Database returns logs
5. Logging Service formats and returns logs
6. Telegram Bot displays formatted logs to admin

## Service Responsibilities

### API Gateway
- **Purpose**: Central entry point, request routing
- **Routes**: All `/api/v1/*` requests
- **Communication**: Proxies requests to backend services

### User Service
- **Purpose**: User management
- **Storage**: In-memory (can be extended to database)
- **Endpoints**: CRUD operations for users

### Game Engine
- **Purpose**: Game session management, invite codes
- **Storage**: In-memory (can be extended to database)
- **Responsibility**: Unified game creation/joining interface

### Game Services (Monopoly, RPS)
- **Purpose**: Game-specific logic
- **Storage**: In-memory game states
- **Communication**: 
  - Receives requests via API Gateway
  - Can call Game Engine for session management
  - Can call Logging Service for event logging

### Logging Service
- **Purpose**: Centralized game event logging
- **Storage**: PostgreSQL database
- **Tables**: 
  - `game_creation_logs`
  - `game_join_logs`
  - `game_action_logs`
  - `game_finish_logs`
  - `game_event_logs`

### Telegram Bot
- **Purpose**: User interface for games
- **Communication**: 
  - Sends requests to API Gateway
  - Receives user messages
  - Displays game state and controls

## Key Design Patterns

1. **API Gateway Pattern**: Single entry point for all requests
2. **Microservices Architecture**: Independent, scalable services
3. **Event Logging**: Centralized logging service for all game events
4. **Service Discovery**: Docker service names for internal communication
5. **Fail-Safe Logging**: Logging failures don't break game operations

## Scalability Considerations

- Each service can be scaled independently
- Database connections are pooled (asyncpg)
- Logging is asynchronous (doesn't block game operations)
- Services communicate via HTTP (stateless)
- Game state is currently in-memory (can be moved to database/Redis for scaling)

