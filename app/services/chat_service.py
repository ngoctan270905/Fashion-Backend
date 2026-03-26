import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.exceptions import NotFoundException
from app.repositories.chat_repository import ChatRepository
from app.schemas.chat import ChatInput

logger = logging.getLogger(__name__)

_GEMINI_MODEL_NAME = settings.GEMINI_MODEL
_GEMINI_TIMEOUT = settings.GEMINI_TIMEOUT
_MAX_HISTORY = settings.GEMINI_MAX_HISTORY

_client: Optional[genai.Client] = None
_client_lock = asyncio.Lock()


async def _get_client() -> genai.Client:
    """
        Lấy hoặc khởi tạo singleton Gemini client.

        Sử dụng cơ chế double-checked locking để đảm bảo client
        chỉ được tạo một lần trong môi trường async đồng thời.

        Raises:
            HTTPException(503): Khi chưa cấu hình GEMINI_API_KEY.

        Returns:
            genai.Client: Instance Gemini client đã được khởi tạo.
    """
    global _client
    if _client is not None:
        return _client
    async with _client_lock:
        if _client is not None:
            return _client
        api_key = getattr(settings, "GEMINI_API_KEY", None)
        if not api_key:
            logger.critical("GEMINI_API_KEY chưa được cấu hình")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service is not configured",
            )
        _client = genai.Client(api_key=api_key)
        logger.info("Gemini client initialized | model=%s", _GEMINI_MODEL_NAME)
    return _client


async def _get_gemini_response(
    content: str,
    history: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
        Gửi nội dung người dùng và lịch sử hội thoại đến Gemini
        để sinh phản hồi AI.

        Args:
            content (str): Nội dung tin nhắn hiện tại của người dùng.
            history (Optional[List[Dict]]): Danh sách tin nhắn trước đó
                theo định dạng [{"role": "...", "content": "..."}].

        Returns:
            str: Nội dung phản hồi từ AI.
    """
    client = await _get_client()

    contents = []
    if history is None:
        history = []

    history_limit = history[-10:]

    for m in history_limit:
        if m["role"] == "user":
            vai_tro = "user"
        else:
            vai_tro = "model"

        # Tạo đối tượng phần nội dung (Part)
        phan_noi_dung = types.Part(text=m["content"])

        # Đóng gói vào đối tượng Content
        tin_nhan_cu = types.Content(role=vai_tro, parts=[phan_noi_dung])

        # Thêm vào danh sách tổng
        contents.append(tin_nhan_cu)

    cau_hoi_moi = types.Content(role="user", parts=[types.Part(text=content)])
    contents.append(cau_hoi_moi)

    try:
        response = await asyncio.wait_for(
            client.aio.models.generate_content(
                model=_GEMINI_MODEL_NAME,
                contents=contents,
            ),
            timeout=_GEMINI_TIMEOUT,
        )
        return response.text

    except asyncio.TimeoutError:
        logger.error("Gemini timeout sau %.0fs", _GEMINI_TIMEOUT)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="AI service timed out, please retry",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise e


async def process_chat_message(chat_repo: ChatRepository, chat_input: ChatInput, user_id: str,) -> Dict[str, Any]:
    content = chat_input.content
    conv_id = chat_input.conversation_id

    # 1. Load history
    history: List[Dict] = []
    if conv_id:
        conversation = await chat_repo.get_conversation_by_id(conv_id, user_id)
        if not conversation:
            raise NotFoundException(detail="Conversation not found.")
        messages = await chat_repo.get_messages_by_conversation_id(conv_id, limit=_MAX_HISTORY)
        history = list(messages)

    # 2. Tạo conversation mới nếu chưa có
    if not conv_id:
        title = content[:30] + ("..." if len(content) > 30 else "")
        new_conv = await chat_repo.create_conversation({"user_id": user_id, "title": title})
        conv_id = new_conv["_id"]

    # 3. Lưu user message NGAY với timestamp riêng
    user_msg = {
        "role": "user",
        "content": content,
        "timestamp": datetime.now(timezone.utc),
        "conversation_id": conv_id,
    }
    try:
        await chat_repo.create_message(user_msg)
        await chat_repo.update_conversation_timestamp(conv_id)
    except Exception as e:
        logger.error("DB persist user message error: %s", e, exc_info=True)
        raise

    # 4. Gọi AI
    ai_content = await _get_gemini_response(content, history)

    # 5. Lưu AI message với timestamp riêng
    ai_msg = {
        "role": "assistant",
        "content": ai_content,
        "timestamp": datetime.now(timezone.utc),
        "conversation_id": conv_id,
    }
    try:
        await chat_repo.create_message(ai_msg)
        await chat_repo.update_conversation_timestamp(conv_id)
    except Exception as e:
        logger.error("DB persist AI message error: %s", e, exc_info=True)
        raise

    return {
        "role": "assistant",
        "content": ai_content,
        "conversation_id": conv_id,
    }