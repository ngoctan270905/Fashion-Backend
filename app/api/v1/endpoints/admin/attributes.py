from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.attribute import (
    AttributeCreate,
    AttributeUpdate,
    AttributeCreateResponse,
    AttributeUpdateResponse,
    AttributeListAll,
)
from app.api.v1.dependencies import get_attribute_service, get_admin_user # Updated import
from app.schemas.base import UnifiedResponse
from app.services.attribute_service import AttributeService


router = APIRouter()


@router.get(
    "/attributes",
    response_model=UnifiedResponse[AttributeListAll],
    status_code=status.HTTP_200_OK,
    summary="Lấy tất cả thuộc tính",
    description="Truy xuất danh sách tất cả các thuộc tính sản phẩm.",
    dependencies=[Depends(get_admin_user)]
)
async def get_all_attributes(
    attribute_service: AttributeService = Depends(get_attribute_service),
):
    attributes = await attribute_service.get_all_attributes()
    return UnifiedResponse(
        success=True,
        message="Lấy danh sách thuộc tính thành công",
        data=attributes
    )


@router.post(
    "/attributes",
    response_model=UnifiedResponse[AttributeCreateResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Tạo thuộc tính mới",
    description="Tạo một thuộc tính sản phẩm mới",
    dependencies=[Depends(get_admin_user)] # Added security dependency
)
async def create_attribute(
    attribute_data: AttributeCreate,
    attribute_service: AttributeService = Depends(get_attribute_service),
):
    new_attribute = await attribute_service.create_attribute(attribute_data)
    return UnifiedResponse(
        success=True,
        message="Thêm thuộc tính thành công",
        data=new_attribute
    )


@router.put(
    "/attributes/{attribute_id}",
    response_model=UnifiedResponse[AttributeUpdateResponse],
    status_code=status.HTTP_200_OK,
    summary="Cập nhật thuộc tính",
    description="Cập nhật thông tin của một thuộc tính sản phẩm hiện có bằng ID.",
    dependencies=[Depends(get_admin_user)] # Added security dependency
)
async def update_attribute(
    attribute_id: str,
    attribute_data: AttributeUpdate,
    attribute_service: AttributeService = Depends(get_attribute_service),
):
    updated_attribute = await attribute_service.update_attribute(
        attribute_id, attribute_data
    )
    return UnifiedResponse(
        success=True,
        message="Cập nhật thuộc tính thành công",
        data=updated_attribute
    )
