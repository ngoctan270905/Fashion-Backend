from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, status, Response
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import settings
from app.schemas.user import UserCreate, UserResponse
from app.schemas.token import Token
from app.schemas.base import UnifiedResponse
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.db.mongodb import get_database
from app.api.v1.dependencies import get_current_user # Import get_current_user
from app.models.domain.user import User # Import User model

router = APIRouter()

# ============================ DEPENDENCIES ============================================================================

async def get_auth_service(db=Depends(get_database)) -> AuthService:
    """
    Dependency cung cấp AuthService với đầy đủ các thành phần phụ thuộc đã được inject.
    """
    user_repo = UserRepository(collection=db["users"])
    refresh_token_repo = RefreshTokenRepository(collection=db["refresh_tokens"])
    return AuthService(user_repo=user_repo, refresh_token_repo=refresh_token_repo)

# ============================ ENDPOINT ================================================================================

@router.post(
    "/register", 
    response_model=UnifiedResponse[UserResponse],
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
    
    # Map từ Domain Model sang Schema Response
    user_data = UserResponse(
        id=new_user.id,
        fullname=new_user.fullname,
        email=new_user.email,
        phone_number=new_user.phone_number,
        is_active=new_user.is_active,
        role=new_user.role # Include the role
    )
    
    return UnifiedResponse(
        success=True,
        message="Đăng ký tài khoản thành công",
        data=user_data
    )

@router.post(
    "/login",
    response_model=Token,
    summary="Đăng nhập nhận JWT token"
)
async def login(
    response: Response, # Inject Response object
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Xác thực email và password để nhận Access Token.
    Sử dụng chuẩn OAuth2 Password Flow.
    """
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    access_token, refresh_token = await auth_service.create_user_token(user)
    
    response.set_cookie(
        key="refresh_token", 
        value=refresh_token, 
        httponly=True, 
        samesite="lax",
        secure=False,
        max_age=settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60,
        expires=datetime.now(timezone.utc) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    )
    
    return access_token

@router.post(
    "/logout",
    response_model=UnifiedResponse[str],
    summary="Đăng xuất và vô hiệu hóa token"
)
async def logout(
    response: Response,
    current_user: User = Depends(get_current_user), # Requires valid access token
    auth_service: AuthService = Depends(get_auth_service)
):
    print(f"test")
    """
    Endpoint hỗ trợ người dùng đăng xuất.
    Vô hiệu hóa refresh token trong DB và xóa cookie.
    """
    # Xóa refresh token khỏi database
    await auth_service.refresh_token_repo.delete_by_user_id(current_user.id)
    
    # Xóa refresh token cookie
    response.delete_cookie("refresh_token")
    
    return UnifiedResponse(success=True, message="Đăng xuất thành công", data="OK")
