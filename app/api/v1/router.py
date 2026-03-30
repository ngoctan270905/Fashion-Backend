from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, chat, users
from app.api.v1.endpoints.admin import user_management

api_router = APIRouter()

# Include các endpoint của v1
api_router.include_router(health.router, tags=["Health Check"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat Management"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])

api_router.include_router(
    user_management.router,
    prefix="/admin/users",
    tags=["Admin - User Management"]
)
