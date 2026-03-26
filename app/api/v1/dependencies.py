from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings
from app.core.exceptions import UnauthorizedException
from app.core.security import decode_token
from app.db.mongodb import get_database
from app.repositories.user_repository import UserRepository
from app.models.domain.user import User

# Định nghĩa scheme xác thực OAuth2 (header Authorization: Bearer <token>)
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db = Depends(get_database)
) -> User:
    """
    Dependency lấy thông tin user hiện tại từ access token.
    Thực hiện truy vấn DB để đảm bảo user vẫn tồn tại và đang hoạt động.
    """
    # 1. Giải mã token để lấy email (subject)
    payload = decode_token(token)
    email: str = payload.get("sub") # Assuming 'sub' in JWT payload is the user's email
    print(f"DEBUG: Email extracted from token: {email}") # DEBUGGING
    
    # 2. Truy vấn DB thông qua UserRepository
    user_repo = UserRepository(collection=db["users"])
    user_raw = await user_repo.get_by_email(email)
    print(f"DEBUG: Result from user_repo.get_by_email: {user_raw}") # DEBUGGING
    
    if user_raw is None:
        raise UnauthorizedException()
        
    # 3. Ánh xạ sang Domain Model
    user = User(
        _id=str(user_raw["_id"]),
        fullname=user_raw["fullname"],
        email=user_raw["email"],
        phone_number=user_raw["phone_number"],
        hashed_password=user_raw["hashed_password"],
        is_active=user_raw.get("is_active", True),
        role=user_raw.get("role", "user"),
        avatar = user_raw.get("avatar"),
        created_at=user_raw.get("created_at"),
        updated_at=user_raw.get("updated_at")
    )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="User account is inactive"
        )
        
    return user
