from typing import Optional

from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, HTTPException, status
from app.schemas.base import UnifiedResponse
from app.schemas.user import UserListResponse, UserUpdate, UserUpdateResponse, UserMeResponse
from app.api.v1.dependencies import get_user_service, get_admin_user, get_current_user
from app.services.user_service import UserService
from app.core.config import settings

router = APIRouter()


@router.get(
    "/",
    response_model=UnifiedResponse[UserListResponse],
    summary="Lấy danh sách tất cả người dùng (Admin Only)",
    dependencies=[Depends(get_admin_user)]
)
async def list_all_users(
    page: int = Query(1, ge=1, description="Số trang hiện tại"),
    page_size: int = Query(10, ge=1, le=100, description="Số user mỗi trang"),
    search: Optional[str] = Query(None, description="Tìm theo tên hoặc email"),
    role: Optional[str] = Query(None, description="Lọc role"),
    is_active: Optional[bool] = Query(None, description="Lọc trạng thái"),
    user_service: UserService = Depends(get_user_service)
):
    user_list_response = await user_service.list_users(
        page=page,
        page_size=page_size,
        search=search,
        role=role,
        is_active=is_active
    )

    for user in user_list_response.items:
        if user.avatar_url:
            user.avatar_url = f"{settings.STATIC_FILES_URL}/{user.avatar_url}"

    return UnifiedResponse(
        success=True,
        message="Lấy danh sách người dùng thành công",
        data=user_list_response
    )


@router.put(
    "/{user_id}",
    response_model=UnifiedResponse[UserUpdateResponse],
    summary="Cập nhật thông tin người dùng bởi ID (Admin Only)",
    dependencies=[Depends(get_admin_user)]
)
async def update_user_by_id(
    user_id: str,
    fullname: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    avatar_file: Optional[UploadFile] = File(None),
    user_service: UserService = Depends(get_user_service)
):
    """
    Endpoint cho phép quản trị viên cập nhật thông tin của một người dùng cụ thể.
    """
    user_update_data = UserUpdate(
        fullname=fullname,
        email=email,
        phone_number=phone_number
    )

    updated_user_response = await user_service.update_user(user_id, user_update_data, avatar_file)

    # Construct full avatar URL if available
    if updated_user_response.avatar_url:
        updated_user_response.avatar_url = f"{settings.STATIC_FILES_URL}/{updated_user_response.avatar_url}"

    return UnifiedResponse(
        success=True,
        message="Cập nhật thông tin người dùng thành công",
        data=updated_user_response
    )


@router.delete(
    "/{user_id}",
    response_model=UnifiedResponse[dict],
    summary="Xóa tài khoản người dùng bởi ID (Admin Only)",
    dependencies=[Depends(get_admin_user)]
)
async def delete_user_by_id(
    user_id: str,
    current_user: UserMeResponse = Depends(get_current_user), # To prevent admin from deleting themselves
    user_service: UserService = Depends(get_user_service)
):
    """
    Endpoint cho phép quản trị viên xóa một tài khoản người dùng cụ thể bằng ID của người dùng đó.
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Quản trị viên không thể tự xóa tài khoản của mình."
        )
    
    await user_service.delete_user(user_id)
    
    return UnifiedResponse(
        success=True,
        message="Xóa tài khoản người dùng thành công",
        data="ok"
    )