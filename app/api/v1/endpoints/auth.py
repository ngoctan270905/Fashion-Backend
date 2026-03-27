from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, status, Response
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import settings
from app.repositories.token_repository import TokenRepository
from app.schemas.user import UserCreate, UserResponse, UserRegisterResponse, UserMeResponse
from app.schemas.token import Token
from app.schemas.base import UnifiedResponse
from app.services import token_service
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.db.mongodb import get_database
from app.api.v1.dependencies import get_current_user, get_token_service, get_auth_service  # Import get_current_user
from app.models.domain.user import User # Import User model

router = APIRouter()

# ============================ ENDPOINT ================================================================================

@router.post(
    "/register", 
    response_model=UnifiedResponse[UserRegisterResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Đăng ký tài khoản mới"
)
async def register(
    user_in: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Endpoint hỗ trợ người dùng đăng ký tài khoản mới với Email và Password.
    """
    new_user = await auth_service.register_user(user_in)
    return UnifiedResponse(
        success=True,
        message="Đăng ký tài khoản thành công",
        data=new_user
    )

# ======================================================================================================================
@router.post(
    "/login",
    response_model=Token,
    summary="Đăng nhập nhận JWT token"
)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Xác thực email và password để nhận Access Token
    """

    return await auth_service.authenticate_user(
        email=form_data.username,
        password=form_data.password,
        response=response
    )

# ======================================================================================================================
@router.post(
    "/logout",
    summary="Đăng xuất và vô hiệu hóa token"
)
async def logout(
    response: Response,
    current_user: UserMeResponse = Depends(get_current_user), # Requires valid access token
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Endpoint hỗ trợ người dùng đăng xuất.
    Vô hiệu hóa refresh token trong DB và xóa cookie.
    """
    return await auth_service.logout(response, current_user.id)



