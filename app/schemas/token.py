from pydantic import BaseModel, ConfigDict
from typing import Optional

class Token(BaseModel):
    """
    Schema trả về cho Client sau khi login thành công.
    Tuân thủ chuẩn OAuth2.
    """
    access_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }
    )

class TokenData(BaseModel):
    """
    Schema chứa dữ liệu giải mã từ JWT payload (thông tin định danh).
    """
    username: Optional[str] = None
