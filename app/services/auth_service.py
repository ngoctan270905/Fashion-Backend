from typing import Dict

from loguru import logger
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, status, Response
from app.core.config import settings
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserRegisterResponse
from app.schemas.token import Token
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.exceptions import ConflictException, UnauthorizedException
from app.services.token_service import TokenService


class AuthService:
    def __init__(self, user_repo: UserRepository, token_service: TokenService):
        self.user_repo = user_repo
        self.token_service = token_service


    async def register_user(self, user_in: UserCreate) -> UserRegisterResponse:
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

        hashed_password = get_password_hash(user_in.password)
        new_user_dict = {
            "fullname": user_in.fullname,
            "email": user_in.email,
            "phone_number": user_in.phone_number,
            "hashed_password": hashed_password,
            "is_active": True,
            "role": "user",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }

        user_id = await self.user_repo.create(new_user_dict)
        return UserRegisterResponse(**user_id)

    # ==================================================================================================================
    async def authenticate_user(self, email: str, password: str, response: Response) -> Token:
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

        access_token = create_access_token(
            subject=str(user_raw["_id"])
        )

        refresh_token = await self.token_service.create_refresh_token(user=user_raw)

        # Đặt refresh token về cooki httpOnly
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=settings.ENVIRONMENT == "production",
            samesite="lax",
            max_age=settings.REFRESH_TOKEN_EXPIRE_SECONDS
        )

        return Token(access_token=access_token)

    # ==================================================================================================================
    async def logout(self, response: Response, user_id: str) -> Dict:
        deleted = await self.token_service.delete_refresh_token(user_id=user_id)
        response.delete_cookie(key="refresh_token")
        return {
            "success": True,
            "message": "Đăng xuất thành công",
            "data": "ok"
        }

