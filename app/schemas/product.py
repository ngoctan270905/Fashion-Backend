from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Literal, Annotated, List, Optional
from bson import ObjectId
from datetime import datetime
from pydantic.functional_validators import BeforeValidator

# Quy tắc 8: ObjectId MongoDB
PyObjectId = Annotated[str, BeforeValidator(str)]


# Schema cho đối tượng trong mảng 'attributeValues' của ProductVariant
class AttributeValueEmbed(BaseModel):
    attributeId: PyObjectId = Field(..., description="ID của thuộc tính")
    value: str = Field(..., min_length=1, max_length=100, description="Giá trị của thuộc tính")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {"attributeId": "65e6e8e8e8e8e8e8e8e8e8a1", "value": "Đen"}
        },
    )


# Schema cho dữ liệu tạo biến thể sản phẩm
class ProductVariantCreate(BaseModel):
    sku: str = Field(..., min_length=3, max_length=50, description="Mã SKU của biến thể (duy nhất)")
    price: float = Field(..., gt=0, description="Giá của biến thể")
    stock: int = Field(..., ge=0, description="Số lượng tồn kho của biến thể")
    attributeValues: List[AttributeValueEmbed] = Field(
        ..., min_length=1, description="Danh sách các giá trị thuộc tính của biến thể"
    )
    isDefaultVariant: bool = Field(False, description="Có phải là biến thể mặc định của sản phẩm không")
    featuredImage: Optional[str] = Field(None, description="Hình ảnh đại diện của biến thể")
    images: List[str] = Field(default_factory=list, description="Danh sách hình ảnh phụ của biến thể")

    @field_validator("sku")
    def validate_sku(cls, v):
        if not v.strip():
            raise ValueError("SKU không được để trống")
        return v

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "sku": "ATP-NAM-POLO-BLACK-S",
                "price": 199000,
                "stock": 45,
                "attributeValues": [
                    {"attributeId": "65e6e8e8e8e8e8e8e8e8e8a1", "value": "Đen"},
                    {"attributeId": "65e6e8e8e8e8e8e8e8e8e8a2", "value": "S"},
                ],
                "isDefaultVariant": True,
                "featuredImage": "uploads/variant_black_s.jpg",
                "images": ["uploads/variant_black_s_1.jpg", "uploads/variant_black_s_2.jpg"],
            }
        },
    )


# Schema trả về cho biến thể sản phẩm
class ProductVariantResponse(ProductVariantCreate):
    id: PyObjectId = Field(alias="_id", description="ID của biến thể")
    productId: PyObjectId = Field(..., description="ID của sản phẩm cha")
    createdAt: datetime = Field(..., description="Thời gian tạo")
    updatedAt: datetime = Field(..., description="Thời gian cập nhật")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": "65e6e8e8e8e8e8e8e8e8e8d1",
                "productId": "65e6e8e8e8e8e8e8e8e8e8c1",
                "sku": "ATP-NAM-POLO-BLACK-S",
                "price": 199000,
                "stock": 45,
                "attributeValues": [
                    {"attributeId": "65e6e8e8e8e8e8e8e8e8e8a1", "value": "Đen"},
                    {"attributeId": "65e6e8e8e8e8e8e8e8e8e8a2", "value": "S"},
                ],
                "isDefaultVariant": True,
                "featuredImage": "uploads/variant_black_s.jpg",
                "images": ["uploads/variant_black_s_1.jpg", "uploads/variant_black_s_2.jpg"],
                "createdAt": "2023-01-01T10:00:00Z",
                "updatedAt": "2023-01-01T10:00:00Z",
            }
        },
    )


# Schema cho dữ liệu cập nhật biến thể sản phẩm
class ProductVariantUpdate(BaseModel):
    sku: Optional[str] = Field(None, min_length=3, max_length=50, description="Mã SKU của biến thể (duy nhất)")
    price: Optional[float] = Field(None, gt=0, description="Giá của biến thể")
    stock: Optional[int] = Field(None, ge=0, description="Số lượng tồn kho của biến thể")
    attributeValues: Optional[List[AttributeValueEmbed]] = Field(
        None, min_length=1, description="Danh sách các giá trị thuộc tính của biến thể"
    )
    isDefaultVariant: Optional[bool] = Field(None, description="Có phải là biến thể mặc định của sản phẩm không")
    featuredImage: Optional[str] = Field(None, description="Hình ảnh đại diện của biến thể")
    images: Optional[List[str]] = Field(None, description="Danh sách hình ảnh phụ của biến thể")

    @field_validator("sku")
    def validate_sku(cls, v):
        if v is not None and not v.strip():
            raise ValueError("SKU không được để trống")
        return v

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "price": 200000,
                "stock": 50,
                "isDefaultVariant": False,
                "featuredImage": "uploads/variant_black_s_new.jpg",
                "images": ["uploads/variant_black_s_new_1.jpg"],
            }
        },
    )


# Schema cho dữ liệu tạo sản phẩm mới
class ProductCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200, description="Tên sản phẩm")
    slug: str = Field(
        ...,
        min_length=2,
        max_length=200,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        description="Slug duy nhất của sản phẩm (chỉ chứa chữ thường, số và dấu gạch ngang)",
    )
    description: Optional[str] = Field(None, description="Mô tả sản phẩm")
    featuredImage: Optional[str] = Field(None, description="Hình ảnh đại diện sản phẩm")
    category: PyObjectId = Field(..., description="ID của danh mục sản phẩm")
    brand: Optional[str] = Field(None, description="Thương hiệu của sản phẩm")
    isActive: bool = Field(True, description="Trạng thái hoạt động của sản phẩm")
    variants: List[ProductVariantCreate] = Field(
        ..., min_length=1, description="Danh sách các biến thể của sản phẩm"
    )

    @field_validator("name")
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("Tên sản phẩm không được để trống")
        return v

    @field_validator("slug")
    def validate_slug(cls, v):
        if not v.strip():
            raise ValueError("Slug không được để trống")
        return v

    @field_validator("variants")
    def validate_default_variant(cls, v):
        default_variants_count = sum(1 for variant in v if variant.isDefaultVariant)
        if default_variants_count > 1:
            raise ValueError("Chỉ có thể có một biến thể mặc định cho mỗi sản phẩm.")
        if default_variants_count == 0:
            raise ValueError("Phải có ít nhất một biến thể mặc định cho mỗi sản phẩm.")
        return v

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "name": "Áo Thun Nam Polo Basic",
                "slug": "ao-thun-nam-polo-basic",
                "description": "Áo thun nam chất liệu cotton cao cấp, thoáng mát...",
                "featuredImage": "uploads/product_main.jpg",
                "category": "65e6e8e8e8e8e8e8e8e8e8b1",
                "brand": "LocalBrandVN",
                "isActive": True,
                "variants": [
                    {
                        "sku": "ATP-NAM-POLO-BLACK-S",
                        "price": 199000,
                        "stock": 45,
                        "attributeValues": [
                            {"attributeId": "65e6e8e8e8e8e8e8e8e8e8a1", "value": "Đen"},
                            {"attributeId": "65e6e8e8e8e8e8e8e8e8e8a2", "value": "S"},
                        ],
                        "isDefaultVariant": True,
                        "featuredImage": "uploads/variant_black_s.jpg",
                        "images": ["uploads/variant_black_s_1.jpg"],
                    }
                ],
            }
        },
    )


# Schema trả về chi tiết sản phẩm
class ProductDetailResponse(BaseModel):
    id: PyObjectId = Field(alias="_id", description="ID của sản phẩm")
    name: str = Field(..., description="Tên sản phẩm")
    slug: str = Field(..., description="Slug của sản phẩm")
    description: Optional[str] = Field(None, description="Mô tả sản phẩm")
    featuredImage: Optional[str] = Field(None, description="Hình ảnh đại diện sản phẩm")
    category: PyObjectId = Field(..., description="ID của danh mục sản phẩm")
    brand: Optional[str] = Field(None, description="Thương hiệu của sản phẩm")
    isActive: bool = Field(..., description="Trạng thái hoạt động của sản phẩm")
    variants: List[ProductVariantResponse] = Field(..., description="Danh sách các biến thể của sản phẩm")
    createdAt: datetime = Field(..., description="Thời gian tạo")
    updatedAt: datetime = Field(..., description="Thời gian cập nhật")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": "65e6e8e8e8e8e8e8e8e8e8c1",
                "name": "Áo Thun Nam Polo Basic",
                "slug": "ao-thun-nam-polo-basic",
                "description": "Áo thun nam chất liệu cotton cao cấp, thoáng mát...",
                "featuredImage": "uploads/product_main.jpg",
                "category": "65e6e8e8e8e8e8e8e8e8e8b1",
                "brand": "LocalBrandVN",
                "isActive": True,
                "variants": [
                    {
                        "id": "65e6e8e8e8e8e8e8e8e8e8d1",
                        "productId": "65e6e8e8e8e8e8e8e8e8e8c1",
                        "sku": "ATP-NAM-POLO-BLACK-S",
                        "price": 199000,
                        "stock": 45,
                        "attributeValues": [
                            {"attributeId": "65e6e8e8e8e8e8e8e8e8e8a1", "value": "Đen"},
                            {"attributeId": "65e6e8e8e8e8e8e8e8e8e8a2", "value": "S"},
                        ],
                        "isDefaultVariant": True,
                        "featuredImage": "uploads/variant_black_s.jpg",
                        "images": ["uploads/variant_black_s_1.jpg"],
                        "createdAt": "2023-01-01T10:00:00Z",
                        "updatedAt": "2023-01-01T10:00:00Z",
                    }
                ],
                "createdAt": "2023-01-01T10:00:00Z",
                "updatedAt": "2023-01-01T10:00:00Z",
            }
        },
    )


# Schema cho dữ liệu cập nhật sản phẩm
class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200, description="Tên sản phẩm")
    slug: Optional[str] = Field(
        None,
        min_length=2,
        max_length=200,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        description="Slug duy nhất của sản phẩm (chỉ chứa chữ thường, số và dấu gạch ngang)",
    )
    description: Optional[str] = Field(None, description="Mô tả sản phẩm")
    featuredImage: Optional[str] = Field(None, description="Hình ảnh đại diện sản phẩm")
    category: Optional[PyObjectId] = Field(None, description="ID của danh mục sản phẩm")
    brand: Optional[str] = Field(None, description="Thương hiệu của sản phẩm")
    isActive: Optional[bool] = Field(None, description="Trạng thái hoạt động của sản phẩm")
    variants: Optional[List[ProductVariantCreate]] = Field(
        None, min_length=1, description="Danh sách các biến thể của sản phẩm"
    )

    @field_validator("name")
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Tên sản phẩm không được để trống")
        return v

    @field_validator("slug")
    def validate_slug(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Slug không được để trống")
        return v

    @field_validator("variants")
    def validate_default_variant(cls, v):
        if v is not None:
            default_variants_count = sum(1 for variant in v if variant.isDefaultVariant)
            if default_variants_count > 1:
                raise ValueError("Chỉ có thể có một biến thể mặc định cho mỗi sản phẩm.")
            if default_variants_count == 0:
                raise ValueError("Phải có ít nhất một biến thể mặc định cho mỗi sản phẩm.")
        return v

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "name": "Áo Thun Nam Polo Cao Cấp",
                "description": "Cập nhật mô tả sản phẩm...",
                "isActive": False,
                "variants": [
                    {
                        "sku": "ATP-NAM-POLO-BLACK-S",
                        "price": 200000,
                        "stock": 50,
                        "attributeValues": [
                            {"attributeId": "65e6e8e8e8e8e8e8e8e8e8a1", "value": "Đen"},
                            {"attributeId": "65e6e8e8e8e8e8e8e8e8e8a2", "value": "S"},
                        ],
                        "isDefaultVariant": True,
                        "featuredImage": "uploads/variant_black_s_new.jpg",
                        "images": ["uploads/variant_black_s_new_1.jpg"],
                    }
                ],
            }
        },
    )


# Schema đơn giản của ProductDetailResponse dùng làm phần tử trong danh sách
class ProductResponse(BaseModel):
    id: PyObjectId = Field(alias="_id", description="ID của sản phẩm")
    name: str = Field(..., description="Tên sản phẩm")
    slug: str = Field(..., description="Slug của sản phẩm")
    featuredImage: Optional[str] = Field(None, description="Hình ảnh đại diện sản phẩm")
    category: PyObjectId = Field(..., description="ID của danh mục sản phẩm")
    brand: Optional[str] = Field(None, description="Thương hiệu của sản phẩm")
    isActive: bool = Field(..., description="Trạng thái hoạt động của sản phẩm")
    # variants không được đưa vào đây để giữ cho ListResponse nhẹ nhàng
    createdAt: datetime = Field(..., description="Thời gian tạo")
    updatedAt: datetime = Field(..., description="Thời gian cập nhật")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": "65e6e8e8e8e8e8e8e8e8e8c1",
                "name": "Áo Thun Nam Polo Basic",
                "slug": "ao-thun-nam-polo-basic",
                "featuredImage": "uploads/product_main.jpg",
                "category": "65e6e8e8e8e8e8e8e8e8e8b1",
                "brand": "LocalBrandVN",
                "isActive": True,
                "createdAt": "2023-01-01T10:00:00Z",
                "updatedAt": "2023-01-01T10:00:00Z",
            }
        },
    )


# Schema chứa danh sách các sản phẩm và tổng số
class ProductListResponse(BaseModel):
    items: List[ProductResponse] = Field(..., description="Danh sách các sản phẩm")
    total_count: int = Field(..., ge=0, description="Tổng số sản phẩm")
    page: int = Field(..., ge=1, description="Trang hiện tại")
    page_size: int = Field(..., ge=1, description="Số lượng sản phẩm trên mỗi trang")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": "65e6e8e8e8e8e8e8e8e8e8c1",
                        "name": "Áo Thun Nam Polo Basic",
                        "slug": "ao-thun-nam-polo-basic",
                        "featuredImage": "uploads/product_main.jpg",
                        "category": "65e6e8e8e8e8e8e8e8e8e8b1",
                        "brand": "LocalBrandVN",
                        "isActive": True,
                        "createdAt": "2023-01-01T10:00:00Z",
                        "updatedAt": "2023-01-01T10:00:00Z",
                    }
                ],
                "total_count": 1,
                "page": 1,
                "page_size": 10,
            }
        },
    )