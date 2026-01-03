from fastapi import FastAPI
from app.endpoints import logs
from app.database import Database
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await Database.get_pool()
    yield
    # Shutdown
    await Database.close_pool()

app = FastAPI(
    title="Game Logging Service",
    version="0.1.0",
    description="Microservice for logging game events",
    lifespan=lifespan
)

app.include_router(
    logs.router,
    prefix="/api/v1/logs",
    tags=["logs"]
)

@app.get("/health")
async def health_check():
    try:
        await Database.get_pool()
        return {"status": "ok", "service": "loggingservice"}
    except Exception as e:
        return {"status": "error", "service": "loggingservice", "error": str(e)}

