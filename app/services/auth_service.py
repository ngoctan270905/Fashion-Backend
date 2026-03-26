from loguru import logger
import uuid
from datetime import datetime, timedelta, timezone

from app.core.context import get_client_ip, get_user_agent
from app.core.config import settings
from app.repositories.user_repository import UserRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.schemas.user import UserCreate
from app.schemas.token import Token
from app.schemas.refresh_token import RefreshTokenCreate
from app.models.domain.user import User
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.exceptions import ConflictException, UnauthorizedException

class AuthService:
    def __init__(self, user_repo: UserRepository, refresh_token_repo: RefreshTokenRepository):
        self.user_repo = user_repo
        self.refresh_token_repo = refresh_token_repo

    async def register_user(self, user_in: UserCreate) -> User:
        """
        Logic đăng ký người dùng:
        1. Kiểm tra email tồn tại.
        2. Băm mật khẩu.
        3. Lưu vào database thông qua Repository.
        """
        # 1. Kiểm tra tồn tại
        user_raw = await self.user_repo.get_by_email(user_in.email)
        if user_raw:
            raise ConflictException(detail="Email đã tồn tại trên hệ thống")

        # 2. Chuẩn bị Domain Model
        hashed_password = get_password_hash(user_in.password)
        new_user = User(
            fullname=user_in.fullname,
            email=user_in.email,
            phone_number=user_in.phone_number,
            hashed_password=hashed_password
        )

        # 3. Chuyển đổi sang dict và lưu qua Repository
        user_dict = new_user.model_dump(by_alias=True, exclude_none=True)
        user_id = await self.user_repo.create(user_dict)
        
        # 4. Gán ID và trả về Domain Model
        new_user.id = user_id
        return new_user


    async def authenticate_user(self, email: str, password: str) -> User:
        """
        Xác thực người dùng:
        1. Tìm user trong DB.
        2. Kiểm tra mật khẩu.
        """
        user_raw = await self.user_repo.get_by_email(email)
        if not user_raw:
            raise UnauthorizedException(detail="Email hoặc mật khẩu không chính xác")

        if not verify_password(password, user_raw["hashed_password"]):
            raise UnauthorizedException(detail="Email hoặc mật khẩu không chính xác")

        if not user_raw.get("is_active", True):
            raise UnauthorizedException(detail="Tài khoản đã bị vô hiệu hóa")

        # Map sang Domain Model
        return User(
            _id=str(user_raw["_id"]),
            fullname=user_raw["fullname"],
            email=user_raw["email"],
            phone_number=user_raw["phone_number"],
            hashed_password=user_raw["hashed_password"],
            is_active=user_raw.get("is_active", True),
            created_at=user_raw.get("created_at"),
            updated_at=user_raw.get("updated_at")
        )

    async def _create_and_store_refresh_token(self, user_id: str) -> str:
        """
        Generates a new refresh token, stores it in the database, and returns the token string.
        """
        refresh_token_string = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
        
        refresh_token_in_db = RefreshTokenCreate(
            user_id=user_id,
            refresh_token=refresh_token_string,
            expires_at=expires_at
        )
        await self.refresh_token_repo.create(refresh_token_in_db)
        return refresh_token_string


    async def create_user_token(self, user: User) -> tuple[Token, str]:
        """Tạo JWT Token và Refresh Token cho người dùng dựa trên thông tin định danh."""
        access_token = create_access_token(subject=user.email)
        refresh_token = await self._create_and_store_refresh_token(user_id=user.id) # type: ignore
        return Token(access_token=access_token, token_type="bearer"), refresh_token

