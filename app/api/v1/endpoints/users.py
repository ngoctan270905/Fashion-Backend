from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from app.schemas.base import UnifiedResponse
from app.schemas.user import UserResponse, UserMeResponse, UserUpdate, UserUpdateResponse, UserListResponse
from app.api.v1.dependencies import get_current_user, get_user_service, get_admin_user
from app.models.domain.user import User
from app.services.user_service import UserService
from app.core.config import settings # New import

router = APIRouter()

@router.get(
    "/me",
    response_model=UnifiedResponse[UserMeResponse],
    summary="Lấy thông tin người dùng hiện tại"
)
async def read_current_user(current_user: UserMeResponse = Depends(get_current_user)):
    """
    Endpoint trả về thông tin chi tiết của người dùng đã xác thực.
    """
    # Construct full avatar URL if available
    if current_user.avatar_url:
        current_user.avatar_url = f"{settings.STATIC_FILES_URL}/{current_user.avatar_url}"

    return UnifiedResponse(success=True, message="Lấy thông tin người dùng thành công", data=current_user)


@router.put(
    "/me",
    response_model=UnifiedResponse[UserUpdateResponse],
    summary="Cập nhật thông tin người dùng hiện tại"
)
async def update_current_user(
    fullname: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    avatar_file: Optional[UploadFile] = File(None),
    current_user: UserMeResponse = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Endpoint cho phép người dùng đã xác thực cập nhật thông tin cá nhân của họ.
    """
    user_update_data = UserUpdate(
        fullname=fullname,
        email=email,
        phone_number=phone_number
    )
    updated_user_domain = await user_service.update_user(current_user.id, user_update_data, avatar_file)

    # Construct full avatar URL if available
    if updated_user_domain.avatar_url:
        updated_user_domain.avatar_url = f"{settings.STATIC_FILES_URL}/{updated_user_domain.avatar_url}"

    return UnifiedResponse(
        success=True,
        message="Cập nhật thông tin người dùng thành công",
        data=updated_user_domain
    )

