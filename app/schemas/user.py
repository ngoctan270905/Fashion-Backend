from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict
import re


class UserBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    fullname: str = Field(..., min_length=3, max_length=50)
    email: str = Field(...)
    phone_number: str = Field(..., min_length=10, max_length=15,)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v):
            raise ValueError("Email không hợp lệ")
        return v

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        if not re.match(r"^[0-9]+$", v):
            raise ValueError("Số điện thoại chỉ được chứa ký tự số")
        return v


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, examples=["StrongPassword123!"])


class UserResponse(UserBase):
    """
    Schema trả về thông tin người dùng trong API response.
    """
    id: str = Field(..., validation_alias="_id", description="ID duy nhất của người dùng")
    fullname: str = Field(..., min_length=3, max_length=50)
    email: str = Field(...)
    phone_number: str = Field(..., min_length=10, max_length=15, )
    is_active: bool
    role: str

class UserRegisterResponse(UserBase):
    """
    Schema trả về thông tin sau khi đăng kí trong API response.
    """
    id: str = Field(..., validation_alias="_id", description="ID duy nhất của người dùng")
    fullname: str = Field(...)
    email: str = Field(...)
    phone_number: str = Field(..., min_length=10, max_length=15, )
    avatar_url: Optional[str] = None
    is_active: bool
    role: str
    created_at: datetime

# class UserMeResponse(UserBase):
#     """
#     Schema trả về thông tin người dùng trong API response.
#     """
#     id: str = Field(..., validation_alias="_id", description="ID duy nhất của người dùng")
#     is_active: bool
#     role: str
#     avatar_url: Optional[str] = None

class UserMeResponse(BaseModel):
    """
    Schema trả về thông tin người dùng trong API response.
    """
    id: str = Field(..., validation_alias="_id", description="ID duy nhất của người dùng")
    fullname: str = Field(..., min_length=3, max_length=50)
    email: str = Field(...)
    phone_number: str = Field(..., min_length=10, max_length=15, )
    is_active: bool
    role: str
    avatar_url: Optional[str] = None


class UserUpdate(BaseModel):
    fullname: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[str] = Field(None)
    phone_number: Optional[str] = Field(None, min_length=10, max_length=15)
    # avatar_url: Optional[str] = None

class UserUpdateResponse(BaseModel):
    id: str | None = Field(None, validation_alias="_id", description="ID duy nhất của người dùng")
    fullname: str | None = Field(None, min_length=3, max_length=50)
    email: str | None = None
    phone_number: str | None = Field(None, min_length=10, max_length=15)
    is_active: bool
    role: str
    avatar_url: str | None = None

class UserInDB(UserBase):
    """
    Schema nội bộ đại diện cho dữ liệu người dùng lưu trong database.

    Được sử dụng trong tầng repository/service,
    không nên expose trực tiếp ra API.

    """

    id: str | None = Field(None, alias="_id")
    hashed_password: str
    model_config = ConfigDict(from_attributes=True)


class UserListItem(BaseModel):
    id: str = Field(..., validation_alias="_id", description="ID duy nhất của người dùng")
    avatar_url: Optional[str] = Field(None)
    fullname: str
    email: str
    phone_number: str
    role: str
    is_active: bool = Field(..., description="Trạng thái hoạt động của người dùng")
    created_at: datetime


class UserListResponse(BaseModel):
    total_count: Optional[int] = Field(None, description="Tổng số người dùng")
    page: int = Field(..., description="Số trang hiện tại")
    page_size: int = Field(..., description="Số lượng mục mỗi trang")
    items: list[UserListItem] = Field(..., description="Danh sách các tài khoản người dùng")