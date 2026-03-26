from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pymongo.asynchronous.collection import AsyncCollection
from bson import ObjectId

class ChatRepository:
    def __init__(self, conv_collection: AsyncCollection, msg_collection: AsyncCollection):
        self.conv_collection = conv_collection
        self.msg_collection = msg_collection

    async def create_conversation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Tạo meta data cho cuộc trò chuyện mới."""
        now = datetime.now(timezone.utc)
        doc = {
            "user_id": data["user_id"],
            "title": data.get("title", "New Chat"),
            "created_at": now,
            "updated_at": now
        }
        result = await self.conv_collection.insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        return doc


    async def get_user_conversations(
        self, user_id: str, limit: int = 20,
        cursor: Optional[datetime] = None ) -> List[Dict[str, Any]]:
        """Lấy danh sách các cuộc trò chuyện của user với phân trang cursor."""
        query = {"user_id": user_id}
        if cursor:
            query["updated_at"] = {"$lt": cursor}
            
        cursor_obj = self.conv_collection.find(query).sort("updated_at", -1).limit(limit)
        conversations = await cursor_obj.to_list(length=limit)
        for conv in conversations:
            conv["_id"] = str(conv["_id"])
        return conversations


    async def get_conversation_by_id(self, conversation_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin meta của một cuộc trò chuyện."""
        conv = await self.conv_collection.find_one({
            "_id": ObjectId(conversation_id),
            "user_id": user_id
        })
        if conv:
            conv["_id"] = str(conv["_id"])
        return conv


    async def update_conversation_timestamp(self, conversation_id: str):
        """Cập nhật thời gian tương tác mới nhất của cuộc trò chuyện."""
        await self.conv_collection.update_one(
            {"_id": ObjectId(conversation_id)},
            {"$set": {"updated_at": datetime.now(timezone.utc)}}
        )


    async def create_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Lưu một tin nhắn mới vào collection messages."""
        msg_doc = {
            "conversation_id": data["conversation_id"],
            "role": data["role"],
            "content": data["content"],
            "timestamp": data.get("timestamp", datetime.now(timezone.utc))
        }
        result = await self.msg_collection.insert_one(msg_doc)
        msg_doc["_id"] = str(result.inserted_id)
        return msg_doc


    async def get_messages_by_conversation_id(
        self, 
        conversation_id: str, 
        limit: int = 20, 
        cursor: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Lấy lịch sử tin nhắn của một cuộc trò chuyện với phân trang cursor (mới nhất trước)."""
        query = {"conversation_id": conversation_id}
        if cursor:
            query["timestamp"] = {"$lt": cursor}
            
        cursor_obj = self.msg_collection.find(query).sort("timestamp", -1).limit(limit)
        messages = await cursor_obj.to_list(length=limit)

        for msg in messages:
            msg["_id"] = str(msg["_id"])

        return messages
