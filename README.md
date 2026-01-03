# TableTime - Microservices Game Platform

A microservices-based platform for tabletop games with Telegram bot integration.

## Architecture

The platform consists of the following microservices:

- **API Gateway** (Port 8000) - Main entry point for all API requests
- **User Service** (Port 8002) - User management
- **Game Engine** (Port 8003) - Game session management (invite codes, user sessions)
- **Monopoly Service** (Port 8004) - Monopoly game logic
- **Rock Paper Scissors Service** (Port 8006) - Rock Paper Scissors game logic
- **Telegram Bot** - Telegram bot integration

## Prerequisites

- Docker and Docker Compose installed
- PowerShell (for Windows) or Bash (for Linux/Mac)

## Setup

### 1. Configure Environment Variables

Environment files have been created with default values. For production, update them with secure values:

**Database Configuration** (`database/.env`):
- Copy `database/.env.example` to `database/.env` (already done)
- Update passwords for production use

**Root Configuration** (`.env`):
- Copy `.env.example` to `.env` (already done)
- Used by docker-compose for variable substitution

**Important:** 
- Never commit `.env` files to git (they're in `.gitignore`)
- Change default passwords in production!
- Use `.env.example` files as templates

### 2. Configure Telegram Bot (Optional)

The `telegrambot/.env` file has been created with a placeholder. To use the Telegram bot:

1. Get a bot token from [@BotFather](https://t.me/BotFather) on Telegram
2. Edit `telegrambot/.env` and replace `your_telegram_bot_token_here` with your actual token:

```env
TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

**Note:** The bot service will start even without a valid token, but it won't function properly. If you don't need the bot, you can disable it by uncommenting the `profiles: disabled` section in `docker-compose.yml`.

## Starting the Services

### Start All Services

```powershell
docker-compose up --build
```

### Start in Detached Mode (Background)

```powershell
docker-compose up -d --build
```

### Start Specific Services

```powershell
# Start only database
docker-compose up database

# Start all services except telegram bot
docker-compose up --build --scale telegrambot=0
```

### View Logs

```powershell
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f apigateway
docker-compose logs -f database
```

### Stop Services

```powershell
# Stop all services
docker-compose down

# Stop and remove volumes (clears database data)
docker-compose down -v
```

## Service Endpoints

Once started, you can access:

- **API Gateway**: http://localhost:8000
- **User Service**: http://localhost:8002
- **Game Engine**: http://localhost:8003
- **Monopoly Service**: http://localhost:8004
- **Rock Paper Scissors Service**: http://localhost:8006

### Health Checks

All services have health check endpoints:

```powershell
# API Gateway
curl http://localhost:8000/health

# Other services
curl http://localhost:8002/health  # User Service
curl http://localhost:8003/health  # Game Engine
curl http://localhost:8004/health  # Monopoly
curl http://localhost:8006/health  # Rock Paper Scissors
```

## API Gateway Routes

The API Gateway routes requests to appropriate services:

- `/api/v1/users/*` → User Service
- `/api/v1/game/*` → Game Engine
- `/api/v1/monopoly/*` → Monopoly Service
- `/api/v1/rps/*` → Rock Paper Scissors Service

## Troubleshooting

### Database Connection Issues

If the database service fails to start:

1. Check that the `.env` file exists in `database/` directory
2. Verify environment variables are set correctly
3. Remove old database data: `docker-compose down -v`
4. Restart: `docker-compose up --build`

### Port Conflicts

If you get port conflicts, you can change ports in `docker-compose.yml`:

```yaml
ports:
  - "8000:8000"  # Change 8000 to another port
```

### Service Not Starting

Check service logs:

```powershell
docker-compose logs [service_name]
```

## Development

### Rebuild After Code Changes

```powershell
docker-compose up --build
```

### Access Service Shells

```powershell
# Access a service container
docker-compose exec apigateway /bin/bash
docker-compose exec gameengine /bin/bash
```

## Production Considerations

1. **Change default passwords** in `database/.env`
2. **Use environment variables** instead of `.env` files
3. **Add authentication** to API Gateway
4. **Configure SSL/TLS** for production
5. **Set up monitoring** and logging
6. **Use secrets management** for sensitive data

