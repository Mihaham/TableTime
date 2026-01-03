# Quick Start Guide

## Step 1: Verify Environment File

Make sure `database/.env` exists with these variables:
- POSTGRES_USER
- POSTGRES_PASSWORD  
- POSTGRES_DB
- POSTGRES_APP_USER
- POSTGRES_APP_PASSWORD

## Step 2: Start Services

### PowerShell (Windows):
```powershell
# Build and start all services
docker-compose up --build

# Or start in background
docker-compose up -d --build
```

### Bash (Linux/Mac):
```bash
# Build and start all services
docker-compose up --build

# Or start in background
docker-compose up -d --build
```

## Step 3: Verify Services

Open a new terminal and check health:

```powershell
# Check API Gateway
curl http://localhost:8000/health

# Check all services
curl http://localhost:8000/health  # API Gateway
curl http://localhost:8002/health  # User Service
curl http://localhost:8003/health  # Game Engine
curl http://localhost:8004/health  # Monopoly
curl http://localhost:8006/health  # Rock Paper Scissors
```

## Step 4: View Logs

```powershell
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f apigateway
```

## Step 5: Stop Services

```powershell
# Stop all
docker-compose down

# Stop and remove data
docker-compose down -v
```

## Common Issues

**Issue:** Environment variables not set
**Solution:** Create `database/.env` file (already created with defaults)

**Issue:** Port already in use
**Solution:** Change ports in `docker-compose.yml` or stop conflicting services

**Issue:** Database won't start
**Solution:** Run `docker-compose down -v` to clear old data, then restart

