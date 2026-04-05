from typing import Dict, Any, Optional, List
from uuid import uuid4
from pathlib import Path
import aiofiles

from app.core.exceptions import NotFoundException, ConflictException, BadRequestException, InternalServerException
from app.repositories.token_repository import TokenRepository
from app.repositories.user_repository import UserRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.schemas.user import UserUpdate, UserUpdateResponse, UserListResponse, UserListItem, UserMeResponse
from fastapi import HTTPException, status, UploadFile
from app.core.config import settings


class UserService:
    def __init__(self, user_repository: UserRepository, token_repo: TokenRepository) -> None:
        self._user_repository = user_repository
        self._token_repository = token_repo

    async def list_users(
        self, page: int, page_size: int,
        search: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> UserListResponse:
        users_raw, total_count = await self._user_repository.get_users_paginated(
            page=page,
            page_size=page_size,
            search=search,
            role=role,
            is_active=is_active
        )
        user_items = [UserListItem(**user_data) for user_data in users_raw]
        return UserListResponse(
            total_count=total_count,
            page=page,
            page_size=page_size,
            items=user_items
        )


    async def update_user(self, user_id: str, user_update_data: UserUpdate, avatar_file: Optional[UploadFile] = None) -> Optional[UserUpdateResponse]:
        # Lấy dữ liệu user
        existing_user_raw = await self._user_repository.get_user_by_id(user_id)
        if not existing_user_raw:
            raise NotFoundException()

        existing_user_for_logic = UserUpdateResponse(**existing_user_raw)

        update_data = user_update_data.model_dump(exclude_none=True)

        # Kiểm tra email
        if "email" in update_data and update_data["email"] != existing_user_for_logic.email:
            if await self._user_repository.get_by_email(update_data["email"]):
                raise ConflictException()

        # Handle avatar file upload
        if avatar_file:
            if not avatar_file.filename:
                raise BadRequestException()

            # Validate file type (simple check for image types)
            if not avatar_file.content_type or not avatar_file.content_type.startswith("image/"):
                raise BadRequestException()

            # Generate unique filename
            file_extension = Path(avatar_file.filename).suffix
            unique_filename = f"{uuid4()}{file_extension}"
            file_path = Path(settings.UPLOADS_DIR) / unique_filename

            # Create uploads directory if it doesn't exist
            Path(settings.UPLOADS_DIR).mkdir(parents=True, exist_ok=True)
            
            # Save the file asynchronously
            async with aiofiles.open(file_path, "wb") as f:
                content = await avatar_file.read(1024)

                while content:
                    await f.write(content)
                    content = await avatar_file.read(1024)

            # Delete old avatar if it exists
            if existing_user_for_logic.avatar_url:
                # The avatar_url from the database might be a full URL if it passed through the API response previously
                # or just the relative path from the service. We need to handle both.
                # If it's a full URL (e.g., http://localhost:8000/static/uploads/abc.png), extract the filename.
                # If it's a relative path (e.g., uploads/abc.png), use it directly.

                # This logic assumes settings.STATIC_DIR exists and contains uploads,
                # which was identified as a potential issue. Let's simplify based on UPLOADS_DIR.
                
                # We need to extract just the filename from the avatar_url stored in the database
                # which would be something like "uploads/uuid.png"
                
                # Split by "/" to get the last part which should be the filename
                old_avatar_filename = Path(existing_user_for_logic.avatar_url).name
                old_avatar_path = Path(settings.UPLOADS_DIR) / old_avatar_filename
                
                # Check if the path points to a file within UPLOADS_DIR before attempting to delete
                if old_avatar_path.is_file(): # and old_avatar_path.parent == Path(settings.UPLOADS_DIR)
                    old_avatar_path.unlink()

            # Store relative path in update_data
            update_data["avatar_url"] = f"{Path(settings.UPLOADS_DIR).name}/{unique_filename}"

        if not update_data:
            return UserUpdateResponse(**existing_user_raw)

        updated_user_raw = await self._user_repository.update_user(user_id, update_data)
        if not updated_user_raw:
            raise InternalServerException()

        return UserUpdateResponse(**updated_user_raw)


    async def get_user_by_id(self, user_id: str) -> Optional[UserMeResponse]: # Changed return type
        user_raw = await self._user_repository.get_user_by_id(user_id)
        return UserMeResponse(**user_raw)


    async def delete_user(self, user_id: str) -> None:
        # Check if user exists
        user_to_delete_raw = await self._user_repository.get_user_by_id(user_id)
        if not user_to_delete_raw:
            raise NotFoundException(detail=f"User with id {user_id} not found.")
        
        user_to_delete = UserMeResponse(**user_to_delete_raw)

        # Delete avatar file if exists
        if user_to_delete.avatar_url:
            # Extract just the filename from the avatar_url
            old_avatar_filename = Path(user_to_delete.avatar_url).name
            old_avatar_path = Path(settings.UPLOADS_DIR) / old_avatar_filename
            if old_avatar_path.is_file():
                try:
                    old_avatar_path.unlink()
                except OSError as e:
                    # Log the error but don't prevent user deletion if file deletion fails
                    print(f"Error deleting old avatar file {old_avatar_path}: {e}")
        
        # Delete refresh tokens associated with the user
        await self._token_repository.delete_by_user_id(user_id)

        # Delete the user record
        deleted_count = await self._user_repository.delete_user(user_id)
        if deleted_count == 0:
            raise InternalServerException(detail="Failed to delete user record.")
