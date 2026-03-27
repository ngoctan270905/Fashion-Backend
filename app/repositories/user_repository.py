from typing import Optional, Dict, Any

from bson import ObjectId
from pymongo.asynchronous.collection import AsyncCollection
from pymongo import ReturnDocument


class UserRepository:
    """
    Repository thao tác dữ liệu User với MongoDB (async).
    """

    def __init__(self, collection: AsyncCollection):
        """
        Args:
            collection (AsyncCollection): MongoDB collection của users.
        """
        self.collection = collection

    async def get_by_email(self, email: str) -> Optional[dict]:
        """
        Tìm user theo email.

        Returns:
            dict | None: Thông tin user nếu tồn tại.
        """
        return await self.collection.find_one({"email": email})

    async def create(self, user_data: dict) -> Dict[str, Any]:
        """
        Tạo mới user và trả về ID vừa tạo.
        """
        new_user = await self.collection.insert_one(user_data)
        user_data["_id"] = str(new_user.inserted_id)
        return user_data

    async def get_user_by_id(self, user_id: str) -> Optional[dict]:
        """
        Tìm user theo ID.
        """
        return await self.collection.find_one({"_id": ObjectId(user_id)})


    async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Optional[dict]:
        """
        Cập nhật thông tin user theo ID.

        Args:
            user_id (str): ID của user cần cập nhật.
            user_data (Dict[str, Any]): Dữ liệu cập nhật.

        Returns:
            dict | None: User đã cập nhật nếu tồn tại, ngược lại là None.
        """
        if not user_data:
            return await self.get_user_by_id(user_id)

        user_data.pop("_id", None)

        updated_document = await self.collection.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$set": user_data},
            return_document=ReturnDocument.AFTER
        )

        if updated_document:
            updated_document["_id"] = str(updated_document["_id"])
        return updated_document