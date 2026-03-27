from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings
from app.core.exceptions import UnauthorizedException
from app.core.security import decode_token
from app.db.mongodb import get_database
from app.repositories.token_repository import TokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserMeResponse
from app.services.auth_service import AuthService
from app.services.token_service import TokenService
from app.services.user_service import UserService # New import
from app.models.domain.user import User

# Định nghĩa scheme xác thực OAuth2 (header Authorization: Bearer <token>)
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

async def get_user_service(db = Depends(get_database)) -> UserService:
    user_repo = UserRepository(collection=db["users"])
    return UserService(user_repository=user_repo)

async def get_token_service(db = Depends(get_database)) -> TokenService:
    token_repo = TokenRepository(collection=db["refresh_tokens"])
    return TokenService(token_repo=token_repo)

async def get_auth_service(db = Depends(get_database), token_service: TokenService = Depends(get_token_service)) -> AuthService:
    user_repo = UserRepository(collection=db["users"])
    return AuthService(user_repo=user_repo,token_service=token_service)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db = Depends(get_database)
) -> UserMeResponse:
    """
    Dependency lấy thông tin user hiện tại từ access token.
    Thực hiện truy vấn DB để đảm bảo user vẫn tồn tại và đang hoạt động.
    """
    # 1. Giải mã token để lấy email (subject)
    payload = decode_token(token)
    user_id: str = payload.get("sub")

    user_repo = UserRepository(collection=db["users"])
    user_raw = await user_repo.get_user_by_id(user_id)

    if user_raw is None:
        raise UnauthorizedException()

    if not user_raw["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="User account is inactive"
        )

    user_raw['_id'] = str(user_id)
        
    return UserMeResponse(**user_raw)
