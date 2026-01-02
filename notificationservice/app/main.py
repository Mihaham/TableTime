from fastapi import FastAPI
from app.endpoints import notifications

app = FastAPI(
    title="Notification Service",
    version="0.1.0",
    description="Microservice for sending notifications"
)

app.include_router(
    notifications.router,
    prefix="/api/v1/notifications",
    tags=["notifications"]
)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "notificationservice"}

