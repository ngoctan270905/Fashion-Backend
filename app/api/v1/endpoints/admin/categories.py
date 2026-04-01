from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status, HTTPException, Form, UploadFile, File
from app.schemas.base import UnifiedResponse
from app.schemas.category import CategoryListResponse, CategoryResponse, CategoryCreate, CategoryUpdate, \
    CategoryCreateResponse
from app.api.v1.dependencies import get_category_service, get_admin_user
from app.services.category_service import CategoryService
from app.core.exceptions import NotFoundException, ConflictException, BadRequestException, InternalServerException
from app.core.config import settings

router = APIRouter()

# ======================================================================================================================
@router.get(
    "/",
    response_model=UnifiedResponse[CategoryListResponse],
    summary="Lây danh sách Categories",
    dependencies=[Depends(get_admin_user)]
)
async def list_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=1000),
    category_service: CategoryService = Depends(get_category_service)
):
    categories_list_response = await category_service.get_all_categories(skip=skip, limit=limit)
    
    for category in categories_list_response.items:
        if category.image_url:
            category.image_url = f"{settings.STATIC_FILES_URL}/{category.image_url}"

    return UnifiedResponse(
        success=True,
        message="Categories retrieved successfully",
        data=categories_list_response
    )

# ======================================================================================================================
@router.get(
    "/{category_id}",
    response_model=UnifiedResponse[CategoryResponse],
    summary="Lấy danh mục theo ID",
    dependencies=[Depends(get_admin_user)]
)
async def get_category_by_id(
    category_id: str,
    category_service: CategoryService = Depends(get_category_service)
):
    category = await category_service.get_category_by_id(category_id)
    if category.image_url:
        category.image_url = f"{settings.STATIC_FILES_URL}/{category.image_url}"

    return UnifiedResponse(
        success=True,
        message=f"Lấy thông tin danh mục thành công",
        data=category
    )

# ======================================================================================================================
@router.post(
    "/",
    response_model=UnifiedResponse[CategoryCreateResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Thêm danh mục mới",
    dependencies=[Depends(get_admin_user)]
)
async def create_category(
    name: str = Form(...),
    slug: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    parent_id: Optional[str] = Form(None),
    is_active: bool = Form(True),
    category_service: CategoryService = Depends(get_category_service)
):
    category_create_data = CategoryCreate(
        name=name,
        slug=slug,
        description=description,
        parent_id=parent_id,
        is_active=is_active
    )
    new_category = await category_service.create_category(category_create_data, image)
    if new_category.image_url:
        new_category.image_url = f"{settings.STATIC_FILES_URL}/{new_category.image_url}"
    return UnifiedResponse(
        success=True,
        message="Category created successfully",
        data=new_category
    )

# ======================================================================================================================
@router.put(
    "/{category_id}",
    response_model=UnifiedResponse[CategoryResponse],
    summary="Cập nhật Category theo ID",
    dependencies=[Depends(get_admin_user)]
)
async def update_category(
    category_id: str,
    name: Optional[str] = Form(None),
    slug: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    parent_id: Optional[str] = Form(None),
    is_active: Optional[bool] = Form(None),
    category_service: CategoryService = Depends(get_category_service)
):
    update_data = CategoryUpdate(
        name=name,
        slug=slug,
        description=description,
        parent_id=parent_id,
        is_active=is_active
    )
    updated_category = await category_service.update_category(category_id, update_data, image)
    if updated_category.image_url:
        updated_category.image_url = f"{settings.STATIC_FILES_URL}/{updated_category.image_url}"

    return UnifiedResponse(
        success=True,
        message=f"Category with ID {category_id} updated successfully",
        data=updated_category
    )

# ======================================================================================================================
@router.delete(
    "/{category_id}",
    response_model=UnifiedResponse[dict],
    summary="Xóa Category theo ID",
    dependencies=[Depends(get_admin_user)]
)
async def delete_category(
    category_id: str,
    category_service: CategoryService = Depends(get_category_service)
):

    await category_service.delete_category(category_id)
    return UnifiedResponse(
        success=True,
        message=f"Category with ID {category_id} deleted successfully"
    )

