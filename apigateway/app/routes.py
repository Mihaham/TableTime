from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, Response
import httpx
from app.config import (
    USER_SERVICE_URL,
    GAME_ENGINE_SERVICE_URL,
    MONOPOLY_SERVICE_URL,
    RPS_SERVICE_URL,
    DICELADDERS_SERVICE_URL,
    LOGGING_SERVICE_URL
)
from loguru import logger

router = APIRouter()

async def proxy_request(service_url: str, path: str, method: str, request: Request):
    """Proxy request to a microservice"""
    url = f"{service_url}{path}"
    logger.info(f"Proxying {method} request to {url}")
    
    # Get request body if exists
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.body()
        except:
            pass
    
    # Get query parameters
    params = dict(request.query_params)
    
    timeout = httpx.Timeout(60.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        try:
            response = await client.request(
                method=method,
                url=url,
                content=body,
                params=params,
                headers={k: v for k, v in request.headers.items() if k.lower() not in ['host', 'content-length']},
                timeout=timeout
            )
            
            # Get content type
            content_type = response.headers.get("content-type", "")
            
            # Handle binary/image responses (don't convert to JSON)
            if content_type.startswith("image/") or content_type.startswith("application/octet-stream"):
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers={
                        "Content-Type": content_type,
                        "Content-Length": str(len(response.content))
                    }
                )
            
            # Handle JSON responses
            if content_type.startswith("application/json"):
                try:
                    content = response.json()
                    return JSONResponse(
                        content=content,
                        status_code=response.status_code,
                        headers={"Content-Type": "application/json"}
                    )
                except Exception as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    return JSONResponse(
                        content={"error": "Failed to parse response", "text": response.text[:500]},
                        status_code=response.status_code
                    )
            
            # For other text responses, return as text
            return Response(
                content=response.text.encode(),
                status_code=response.status_code,
                headers={"Content-Type": content_type or "text/plain"}
            )
            
        except httpx.RequestError as e:
            logger.error(f"Request error in proxy: {e}")
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

# Rock Paper Scissors Service Routes
@router.api_route("/api/v1/rps/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_rps(path: str, request: Request):
    return await proxy_request(RPS_SERVICE_URL, f"/api/v1/rps/{path}", request.method, request)

# Dice and Ladders Service Routes
@router.api_route("/api/v1/diceladders/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_diceladders(path: str, request: Request):
    return await proxy_request(DICELADDERS_SERVICE_URL, f"/api/v1/diceladders/{path}", request.method, request)

# Logging Service Routes
@router.api_route("/api/v1/logs/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_logs(path: str, request: Request):
    return await proxy_request(LOGGING_SERVICE_URL, f"/api/v1/logs/{path}", request.method, request)


