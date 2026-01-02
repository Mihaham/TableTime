from fastapi import FastAPI
from app.endpoints import database
from app.utils import init_db
import asyncio

app = FastAPI(
    title="Database Interface",
    version="0.1.0",
    description="Microservice for database operations"
)

app.include_router(
    database.router,
    prefix="/api/v1",
    tags=["database"]
)

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "databaseinterface"}
