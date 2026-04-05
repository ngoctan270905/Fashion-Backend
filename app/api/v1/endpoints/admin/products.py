from fastapi import APIRouter, Depends, HTTPException, status, Query, Form
from typing import Dict, Any

from app.schemas.base import UnifiedResponse
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductDetailResponse,
    ProductListResponse,
)
from app.api.v1.dependencies import get_product_service, get_admin_user
from app.services.product_service import ProductService
from app.core.exceptions import NotFoundException, ConflictException, BadRequestException, InternalServerException

router = APIRouter()


@router.get(
    "/products",
    response_model=UnifiedResponse[ProductListResponse],
    summary="Lấy danh sách sản phẩm",
    description="Truy xuất danh sách tất cả các sản phẩm có phân trang, tìm kiếm và lọc.",
    dependencies=[Depends(get_admin_user)],
)
async def get_all_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: str | None = Query(None, min_length=1, max_length=100),
    # filters: Dict[str, Any] | None = Query(None), # For future advanced filtering
    product_service: ProductService = Depends(get_product_service),
):
    try:
        products_list_response = await product_service.get_all_products(
            page=page, page_size=page_size, search=search, filters=None
        )
        return UnifiedResponse[ProductListResponse](
            success=True,
            message="Danh sách sản phẩm được lấy thành công",
            data=products_list_response,
        )
    except Exception as e:
        raise InternalServerException(f"Lỗi khi lấy danh sách sản phẩm: {e}")


@router.get(
    "/products/{product_id}",
    response_model=UnifiedResponse[ProductDetailResponse],
    summary="Lấy chi tiết sản phẩm theo ID",
    description="Truy xuất thông tin chi tiết của một sản phẩm cụ thể.",
    dependencies=[Depends(get_admin_user)],
)
async def get_product_detail(
    product_id: str, product_service: ProductService = Depends(get_product_service)
):
    try:
        product = await product_service.get_product_detail(product_id)
        if not product:
            raise NotFoundException("Không tìm thấy sản phẩm")
        return UnifiedResponse[ProductDetailResponse](
            success=True, message="Lấy chi tiết sản phẩm thành công", data=product
        )
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise InternalServerException(f"Lỗi khi lấy chi tiết sản phẩm: {e}")


@router.post(
    "/products",
    response_model=UnifiedResponse[ProductDetailResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Tạo sản phẩm mới",
    description="Tạo một sản phẩm mới cùng với các biến thể của nó.",
    dependencies=[Depends(get_admin_user)],
)
async def create_product(
    product_data: str = Form(...),
    featuredImage: UploadFile | None = File(None),
    product_service: ProductService = Depends(get_product_service),
):
    new_product = await product_service.create_product(product_data)
    return UnifiedResponse[ProductDetailResponse](
        success=True, message="Tạo sản phẩm thành công", data=new_product
    )



@router.put(
    "/products/{product_id}",
    response_model=UnifiedResponse[ProductDetailResponse],
    summary="Cập nhật sản phẩm",
    description="Cập nhật thông tin của một sản phẩm hiện có bằng ID.",
    dependencies=[Depends(get_admin_user)],
)
async def update_product(
    product_id: str,
    product_data: ProductUpdate,
    product_service: ProductService = Depends(get_product_service),
):
    try:
        updated_product = await product_service.update_product(
            product_id, product_data
        )
        if not updated_product:
            raise NotFoundException("Không tìm thấy sản phẩm để cập nhật")
        return UnifiedResponse[ProductDetailResponse](
            success=True, message="Cập nhật sản phẩm thành công", data=updated_product
        )
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValueError as e: # For Pydantic validator errors (e.g. isDefaultVariant count)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise InternalServerException(f"Lỗi khi cập nhật sản phẩm: {e}")


@router.delete(
    "/products/{product_id}",
    response_model=UnifiedResponse[str],
    summary="Xóa sản phẩm",
    description="Xóa một sản phẩm và tất cả các biến thể liên quan của nó.",
    dependencies=[Depends(get_admin_user)],
)
async def delete_product(
    product_id: str, product_service: ProductService = Depends(get_product_service)
):
    try:
        deleted = await product_service.delete_product(product_id)
        if not deleted:
            raise NotFoundException("Không tìm thấy sản phẩm để xóa")
        return UnifiedResponse[str](
            success=True, message="Xóa sản phẩm thành công", data="ok"
        )
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise InternalServerException(f"Lỗi khi xóa sản phẩm: {e}")
