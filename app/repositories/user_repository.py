from typing import Optional
from pymongo.asynchronous.collection import AsyncCollection


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

    async def create(self, user_data: dict) -> str:
        """
        Tạo mới user và trả về ID vừa tạo.
        """
        new_user = await self.collection.insert_one(user_data)
        result = str(new_user.inserted_id)
        return result