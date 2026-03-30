from typing import Optional, Dict, Any, List
from bson import ObjectId
from pymongo.asynchronous.collection import AsyncCollection
from pymongo import ReturnDocument


class UserRepository:

    def __init__(self, collection: AsyncCollection):
        """
        Args: collection (AsyncCollection): MongoDB collection của users.
        """
        self.collection = collection


    async def get_by_email(self, email: str) -> Optional[dict]:
        return await self.collection.find_one({"email": email})


    async def create(self, user_data: dict) -> Dict[str, Any]:
        new_user = await self.collection.insert_one(user_data)
        user_data["_id"] = str(new_user.inserted_id)
        return user_data


    async def get_user_by_id(self, user_id: str) -> Optional[dict]:
        user = await self.collection.find_one({"_id": ObjectId(user_id)})
        if user:
            user["_id"] = str(user["_id"])
        return user


    async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Optional[dict]:
        updated_document = await self.collection.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$set": user_data},
            return_document=ReturnDocument.AFTER
        )
        if updated_document:
            updated_document["_id"] = str(updated_document["_id"])
        return updated_document


    async def delete_user(self, user_id: str) -> int:
        result = await self.collection.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count


    async def get_users_paginated(
        self,
        page: int,
        page_size: int,
        search: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[Dict[str, Any]]:

        query: Dict[str, Any] = {}

        if search:
            search_regex = {"$regex": search, "$options": "i"} # "i" cho tìm kiếm không phân biệt chữ hoa chữ thường
            query["$or"] = [
                {"fullname": search_regex},
                {"email": search_regex}
            ]

        if role:
            query["role"] = role

        if is_active is not None:
            query["is_active"] = is_active

        # Tính toán skip cho phân trang offset
        skip = (page - 1) * page_size

        # Sắp xếp theo _id để đảm bảo thứ tự nhất quán
        cursor = self.collection.find(query).sort("_id", 1).skip(skip).limit(page_size)
        users = [user async for user in cursor]

        # Chuyển đổi ObjectId sang string cho tất cả các user
        for user in users:
            user["_id"] = str(user["_id"])

        total_count = await self.collection.count_documents(query)

        return users, total_count