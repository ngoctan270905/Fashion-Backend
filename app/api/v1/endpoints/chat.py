from fastapi import APIRouter, Depends, status, HTTPException
from typing import List, Optional
from datetime import datetime
from app.api.v1.dependencies import get_current_user
from app.db.mongodb import get_database
from app.schemas.chat import (
    ConversationResponse, 
    ConversationSummary, 
    ChatInput, 
    ChatMessageResponse,
    PaginatedHistory
)
from app.schemas.base import UnifiedResponse
from app.repositories.chat_repository import ChatRepository
from app.services import chat_service
from app.models.domain.user import User

router = APIRouter()

# ============================ DEPENDENCIES ============================================================================

async def get_chat_repo(db = Depends(get_database)) -> ChatRepository:
    """Dependency cung cấp ChatRepository quản lý cả 2 collections."""
    return ChatRepository(
        conv_collection=db["conversations"], 
        msg_collection=db["messages"]
    )
# ============================ ENDPOINT ================================================================================

@router.get(
    "/history",
    response_model=UnifiedResponse[PaginatedHistory],
    summary="Lấy lịch sử chat"
)
async def get_chat_history(
    limit: int = 20,
    cursor: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    chat_repo: ChatRepository = Depends(get_chat_repo)
):
    """Trả về danh sách các cuộc trò chuyện cũ với phân trang."""
    conversations = await chat_repo.get_user_conversations(
        user_id=str(current_user.id),
        limit=limit,
        cursor=cursor
    )
    
    next_cursor = None
    if len(conversations) == limit:
        next_cursor = conversations[-1]["updated_at"]
        
    return UnifiedResponse(
        success=True, 
        message="Success", 
        data=PaginatedHistory(items=conversations, next_cursor=next_cursor)
    )


@router.get(
    "/{conversation_id}",
    response_model=UnifiedResponse[ConversationResponse],
    summary="Lấy chi tiết cuộc trò chuyện"
)
async def get_chat_details(
    conversation_id: str,
    limit: int = 20,
    cursor: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    chat_repo: ChatRepository = Depends(get_chat_repo)
):
    """Lấy thông tin meta và tin nhắn (phân trang) thuộc cuộc hội thoại."""
    # 1. Lấy meta data
    conversation = await chat_repo.get_conversation_by_id(
        conversation_id=conversation_id,
        user_id=str(current_user.id)
    )
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # 2. Lấy tin nhắn (phân trang)
    messages = await chat_repo.get_messages_by_conversation_id(
        conversation_id=conversation_id,
        limit=limit,
        cursor=cursor
    )

    next_cursor = None
    if len(messages) == limit:
        next_cursor = messages[-1]["timestamp"]
    
    # 4. Hợp nhất dữ liệu
    conversation["messages"] = messages
    conversation["next_cursor"] = next_cursor
    
    return UnifiedResponse(success=True, message="Success", data=conversation)


@router.post(
    "/message",
    response_model=UnifiedResponse[ChatMessageResponse],
    summary="Gửi tin nhắn"
)
async def send_chat_message(
    chat_input: ChatInput,
    current_user: User = Depends(get_current_user),
    chat_repo: ChatRepository = Depends(get_chat_repo)
):
    """Xử lý gửi tin nhắn, tích hợp Gemini và lưu vào 2 collections."""
    try:
        result = await chat_service.process_chat_message(
            chat_repo=chat_repo,
            chat_input=chat_input,
            user_id=str(current_user.id)
        )
        return UnifiedResponse(success=True, message="Success", data=result)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
