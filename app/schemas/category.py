from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class CategoryBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True) # Allow population by field name or alias

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

class CategoryCreateResponse(CategoryBase):
    id: str = Field(..., validation_alias="_id")
    level: int = Field(..., ge=1) # Level is always returned
    sort_order: int = Field(..., ge=0) # Sort order is always returned
    created_at: datetime = Field(default_factory=datetime.utcnow)
class CategoryUpdate(BaseModel): # Inherit from BaseModel directly to make all fields optional
    model_config = ConfigDict(populate_by_name=True)
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    slug: Optional[str] = Field(None, max_length=120)
    description: Optional[str] = Field(None, max_length=500)
    image_url: Optional[str] = None
    parent_id: Optional[str] = None
    is_active: Optional[bool] = None
    # Level and sort_order are managed by the service, not updated directly

class CategoryResponse(CategoryBase):
    id: str = Field(..., validation_alias="_id")
    level: int = Field(..., ge=1) # Level is always returned
    sort_order: int = Field(..., ge=0) # Sort order is always returned
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(populate_by_name=True) # Ensure this is also on response model for consistency


class CategoryListItem(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    slug: Optional[str] = Field(None, max_length=120)
    description: Optional[str] = Field(None, max_length=500)
    image_url: Optional[str] = None
    parent_id: Optional[str] = None  # Will be validated and used for level calculation in service
    is_active: bool = True  # Keep is_active in base for create/update
    id: str = Field(..., validation_alias="_id")  # Map MongoDB _id to Pydantic id
    level: int = Field(..., ge=1)  # Level is always returned
    sort_order: int = Field(..., ge=0)  # Sort order is always returned
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)



class CategoryListResponse(BaseModel):
    total_count: Optional[int] = Field(None, description="Tổng số danh mục")
    page: int = Field(..., description="Số trang hiện tại")
    page_size: int = Field(..., description="Số lượng mục mỗi trang")
    items: List[CategoryListItem] = Field(..., description="Danh sách các danh mục")

