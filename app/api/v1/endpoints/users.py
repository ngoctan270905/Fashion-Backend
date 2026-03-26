from fastapi import APIRouter, Depends

from app.schemas.base import UnifiedResponse
from app.schemas.user import UserResponse, UserMeResponse
from app.api.v1.dependencies import get_current_user
from app.models.domain.user import User

router = APIRouter()

@router.get(
    "/me",
    response_model=UnifiedResponse[UserMeResponse],
    summary="Lấy thông tin người dùng hiện tại"
)
async def read_current_user(
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint trả về thông tin chi tiết của người dùng đã xác thực.
    """
    return UnifiedResponse(success=True, message="Lấy thông tin người dùng thành công", data=current_user)
