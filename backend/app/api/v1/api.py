from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, trading, websocket

api_router = APIRouter()

# Include all routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(trading.router, prefix="/trading", tags=["trading"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"]) 