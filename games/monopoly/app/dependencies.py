import httpx

async def get_gameengine_client():
    """Get HTTP client for gameengine service"""
    async with httpx.AsyncClient(base_url="http://gameengine:8000") as client:
        yield client

