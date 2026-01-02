from fastapi import FastAPI
from app.endpoints import users

app = FastAPI(
    title="User Service",
    version="0.1.0",
    description="Microservice for user management"
)

app.include_router(
    users.router,
    prefix="/api/v1/users",
    tags=["users"]
)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "userservice"}

