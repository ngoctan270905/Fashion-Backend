from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class RefreshTokenCreate(BaseModel):
    """
    Schema for creating a new refresh token entry.
    """
    user_id: str = Field(...)
    refresh_token: str = Field(...)
    expires_at: datetime = Field(...)

class RefreshTokenInDB(RefreshTokenCreate):
    """
    Schema for a refresh token stored in the database.
    Includes database-specific fields like ID and creation timestamp.
    """
    id: Optional[str] = Field(None, alias="_id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "user_id": "60d0fe4f5311236168a109cc",
                "refresh_token": "some_long_and_secure_refresh_token_string",
                "expires_at": "2024-03-26T10:00:00Z",
                "created_at": "2024-03-26T08:00:00Z"
            }
        }
    )
