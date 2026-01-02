from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
from app.config import (
    USER_SERVICE_URL,
    GAME_ENGINE_SERVICE_URL,
    MONOPOLY_SERVICE_URL,
    DATABASE_INTERFACE_SERVICE_URL,
    NOTIFICATION_SERVICE_URL
)

router = APIRouter()

async def proxy_request(service_url: str, path: str, method: str, request: Request):
    """Proxy request to a microservice"""
    url = f"{service_url}{path}"
    
    # Get request body if exists
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.body()
        except:
            pass
    
    # Get query parameters
    params = dict(request.query_params)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=method,
                url=url,
                content=body,
                params=params,
                headers=dict(request.headers),
                timeout=30.0
            )
            return JSONResponse(
                content=response.json() if response.headers.get("content-type", "").startswith("application/json") else {"data": response.text},
                status_code=response.status_code
            )
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

# User Service Routes
@router.api_route("/api/v1/users/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_users(path: str, request: Request):
    return await proxy_request(USER_SERVICE_URL, f"/api/v1/users/{path}", request.method, request)

# Game Engine Routes
@router.api_route("/api/v1/game/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_game_engine(path: str, request: Request):
    return await proxy_request(GAME_ENGINE_SERVICE_URL, f"/api/v1/{path}", request.method, request)

# Monopoly Service Routes
@router.api_route("/api/v1/monopoly/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_monopoly(path: str, request: Request):
    return await proxy_request(MONOPOLY_SERVICE_URL, f"/api/v1/monopoly/{path}", request.method, request)

# Database Interface Routes
@router.api_route("/api/v1/database/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_database(path: str, request: Request):
    return await proxy_request(DATABASE_INTERFACE_SERVICE_URL, f"/api/v1/{path}", request.method, request)

# Notification Service Routes
@router.api_route("/api/v1/notifications/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_notifications(path: str, request: Request):
    return await proxy_request(NOTIFICATION_SERVICE_URL, f"/api/v1/notifications/{path}", request.method, request)

