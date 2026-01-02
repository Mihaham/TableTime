# TableTime Services Startup Script
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  TableTime Microservices Platform" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env file exists
if (-not (Test-Path "database\.env")) {
    Write-Host "ERROR: database\.env file not found!" -ForegroundColor Red
    Write-Host "Creating default database\.env file..." -ForegroundColor Yellow
    Set-Content -Path "database\.env" -Value @"
# PostgreSQL Database Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres_password
POSTGRES_DB=tabletime_db

# Application Database User
POSTGRES_APP_USER=app_user
POSTGRES_APP_PASSWORD=app_password
"@
    Write-Host "Created database\.env file" -ForegroundColor Green
}

# Check if root .env exists
if (-not (Test-Path ".env")) {
    Write-Host "Creating root .env file for docker-compose..." -ForegroundColor Yellow
    Set-Content -Path ".env" -Value @"
# Database Configuration (used by docker-compose for variable substitution)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres_password
POSTGRES_DB=tabletime_db
POSTGRES_APP_USER=app_user
POSTGRES_APP_PASSWORD=app_password
"@
    Write-Host "Created .env file" -ForegroundColor Green
}

# Check if telegrambot .env exists
if (-not (Test-Path "telegrambot\.env")) {
    Write-Host "Creating telegrambot\.env file..." -ForegroundColor Yellow
    Set-Content -Path "telegrambot\.env" -Value @"
# Telegram Bot Configuration
# Get your bot token from @BotFather on Telegram
# Format: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TOKEN=your_telegram_bot_token_here
"@
    Write-Host "Created telegrambot\.env file (update with your bot token)" -ForegroundColor Green
    Write-Host "Note: Telegram bot will not work until you add a valid token" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Starting services..." -ForegroundColor Yellow
Write-Host ""

# Start docker-compose
docker-compose up --build

