from typing import Dict, Any, Optional
from uuid import uuid4 # New import
from pathlib import Path # New import
import aiofiles # New import

from app.models.domain.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserUpdate, UserUpdateResponse
from fastapi import HTTPException, status, UploadFile # New import UploadFile
from app.core.config import settings # New import


class UserService:
    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    async def update_user(self, user_id: str, user_update_data: UserUpdate, avatar_file: Optional[UploadFile] = None) -> Optional[UserUpdateResponse]:
        update_data = user_update_data.model_dump(exclude_none=True)

        # Handle avatar file upload
        if avatar_file:
            if not avatar_file.filename:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Không có tên tệp cho avatar."
                )

            # Validate file type (simple check for image types)
            if not avatar_file.content_type or not avatar_file.content_type.startswith("image/"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Loại tệp avatar không hợp lệ. Chỉ chấp nhận hình ảnh."
                )

            # Generate unique filename
            file_extension = Path(avatar_file.filename).suffix
            unique_filename = f"{uuid4()}{file_extension}"
            file_path = Path(settings.UPLOADS_DIR) / unique_filename

            # Save the file asynchronously
            async with aiofiles.open(file_path, "wb") as f:
                while content := await avatar_file.read(1024):  # read in chunks
                    await f.write(content)

            # Store relative path in update_data
            # The URL path for static files will be /static/<filename>
            relative_path = f"{settings.UPLOADS_DIR.split('/')[-1]}/{unique_filename}"
            update_data["avatar_url"] = relative_path
        
        # If no other data to update and no avatar, return current user
        if not update_data:
            current_user_raw = await self._user_repository.get_user_by_id(user_id)
            if not current_user_raw:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with id {user_id} not found."
                )
            current_user_raw["_id"] = str(current_user_raw["_id"])
            return UserUpdateResponse(**current_user_raw)


        updated_user_raw = await self._user_repository.update_user(user_id, update_data)
        print(f"test : {user_update_data}")
        if not updated_user_raw:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found."
            )
        return UserUpdateResponse(**updated_user_raw)


    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        user_raw = await self._user_repository.get_user_by_id(user_id)
        return User(**user_raw) if user_raw else None # Convert raw data to domain model
