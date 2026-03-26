from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import List, Optional


class MessageSchema(BaseModel):
    """
    Schema đại diện cho một tin nhắn trong cuộc hội thoại.

    Attributes:
        id (str):
            ID của tin nhắn.
            Sử dụng validation_alias="_id" để ánh xạ từ MongoDB ObjectId (_id)
            sang field id khi trả về API response.

        role (str):
            Vai trò của người gửi tin nhắn.

        content (str):
            Nội dung văn bản của tin nhắn.

        timestamp (datetime):
            Thời điểm tạo tin nhắn.
    """

    id: str = Field(..., validation_alias="_id")
    role: str = Field(..., description="Vai trò: user hoặc assistant")
    content: str = Field(..., description="Nội dung tin nhắn")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )


class ConversationBase(BaseModel):
    """
    Schema cơ sở cho cuộc hội thoại.

    Chứa các thuộc tính chung được sử dụng lại trong
    nhiều schema khác nhau (Create, Response, Summary...).

    Attributes:
        title (str):
            Tiêu đề của cuộc hội thoại.
            - Mặc định: "New Chat"
            - Độ dài tối thiểu: 1 ký tự
            - Độ dài tối đa: 100 ký tự
    """

    title: str = Field(default="New Chat", min_length=1, max_length=100)


class ConversationCreate(ConversationBase):
    """
    Schema dùng khi tạo mới một cuộc hội thoại.
    Kế thừa từ ConversationBase.
    """
    pass


class ConversationResponse(ConversationBase):
    """
    Schema trả về đầy đủ thông tin của một cuộc hội thoại.
    """

    id: str = Field(..., validation_alias="_id")
    user_id: str
    messages: List[MessageSchema] = []
    next_cursor: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )


class ConversationSummary(BaseModel):
    """
    Schema dùng để trả về thông tin rút gọn của một cuộc hội thoại.

    Thường sử dụng trong:
    - API danh sách conversations
    - Sidebar hiển thị lịch sử chat

    Attributes:
        id (str):
            ID của conversation (map từ _id).

        title (str):
            Tiêu đề cuộc hội thoại.

        updated_at (datetime):
            Thời điểm cập nhật gần nhất,
            dùng để sắp xếp theo thứ tự mới nhất.
    """

    id: str = Field(..., validation_alias="_id")
    title: str
    updated_at: datetime

    model_config = ConfigDict(populate_by_name=True)


class PaginatedHistory(BaseModel):
    """Schema cho danh sách hội thoại có phân trang."""
    items: List[ConversationSummary]
    next_cursor: Optional[datetime] = None


class ChatInput(BaseModel):
    """
    Schema dữ liệu đầu vào khi người dùng gửi tin nhắn.

    Attributes:
        content (str):
            Nội dung tin nhắn của user.
            - Bắt buộc
            - Tối thiểu 1 ký tự

        conversation_id (Optional[str]):
            ID của cuộc hội thoại hiện tại.
            - Nếu có: tiếp tục cuộc hội thoại cũ
            - Nếu None: hệ thống sẽ tạo conversation mới
    """

    content: str = Field(..., min_length=1)
    conversation_id: Optional[str] = None


class ChatMessageResponse(BaseModel):
    """
    Schema phản hồi tin nhắn từ hệ thống (assistant).

    Attributes:
        role (str):
            Vai trò mặc định là "assistant".

        content (str):
            Nội dung phản hồi từ AI.

        conversation_id (str):
            ID của cuộc hội thoại mà tin nhắn thuộc về.
            Dùng để frontend tiếp tục duy trì session chat.
    """

    role: str = "assistant"
    content: str
    conversation_id: str