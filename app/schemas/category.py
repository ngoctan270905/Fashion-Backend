from datetime import datetime, UTC
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class CategoryBase(BaseModel):

    name: str = Field(..., min_length=3, max_length=100)
    slug: Optional[str] = Field(None, max_length=120)
    description: Optional[str] = Field(None, max_length=500)
    image_url: Optional[str] = None
    parent_id: Optional[str] = None # Will be validated and used for level calculation in service
    is_active: bool = True # Keep is_active in base for create/update

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    slug: Optional[str] = Field(None, max_length=120)
    description: Optional[str] = Field(None, max_length=500)
    image_url: Optional[str] = None
    parent_id: Optional[str] = None  # Will be validated and used for level calculation in service
    is_active: bool = True  # Keep is_active in base for create/update

class CategoryCreateResponse(BaseModel):
    id: str = Field(..., validation_alias="_id")
    name: str = Field(..., min_length=3, max_length=100)
    slug: Optional[str] = Field(None, max_length=120)
    description: Optional[str] = Field(None, max_length=500)
    image_url: Optional[str] = None
    parent_id: Optional[str] = None
    is_active: bool = True
    level: int = Field(..., ge=1)
    sort_order: int = Field(..., ge=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

class CategoryUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    slug: Optional[str] = Field(None, max_length=120)
    description: Optional[str] = Field(None, max_length=500)
    image_url: Optional[str] = None
    parent_id: Optional[str] = None
    is_active: Optional[bool] = None


class CategoryUpdateResponse(CategoryBase):
    id: str = Field(..., validation_alias="_id")
    level: int = Field(..., ge=1)
    sort_order: int = Field(..., ge=1)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

class CategoryResponse(CategoryBase):
    id: str = Field(..., validation_alias="_id")
    level: int = Field(..., ge=1) # Level is always returned
    sort_order: int = Field(..., ge=0) # Sort order is always returned
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CategoryListItem(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    slug: Optional[str] = Field(None, max_length=120)
    description: Optional[str] = Field(None, max_length=500)
    image_url: Optional[str] = None
    parent_id: Optional[str] = None
    is_active: bool = True
    id: str = Field(..., validation_alias="_id")
    level: int = Field(..., ge=1)
    sort_order: int = Field(..., ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))



class CategoryListResponse(BaseModel):
    total_count: Optional[int] = Field(None, description="Tổng số danh mục")
    page: int = Field(..., description="Số trang hiện tại")
    page_size: int = Field(..., description="Số lượng mục mỗi trang")
    items: List[CategoryListItem] = Field(..., description="Danh sách các danh mục")

