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
    is_active: bool
    role: str

class UserMeResponse(UserBase):
    """
    Schema trả về thông tin người dùng trong API response.
    """
    id: str = Field(..., validation_alias="_id", description="ID duy nhất của người dùng")
    is_active: bool
    role: str
    avatar_url: Optional[str] = None



class UserInDB(UserBase):
    """
    Schema nội bộ đại diện cho dữ liệu người dùng lưu trong database.

    Được sử dụng trong tầng repository/service,
    không nên expose trực tiếp ra API.

    """

    id: str | None = Field(None, alias="_id")
    hashed_password: str
    model_config = ConfigDict(from_attributes=True)