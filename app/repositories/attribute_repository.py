from pymongo.asynchronous.collection import AsyncCollection
from bson import ObjectId
from datetime import datetime
from pymongo import ReturnDocument # Added import

class AttributeRepository:
    def __init__(self, collection: AsyncCollection):
        """
        Args:
            collection (AsyncCollection): MongoDB collection for attributes.
        """
        self.collection = collection

    async def get_all(self) -> list[dict]:
        """
        Lấy tất cả các thuộc tính từ cơ sở dữ liệu.
        Trả về một danh sách các dict thô.
        """
        attributes = []
        async for attribute in self.collection.find({}):
            attribute["_id"] = str(attribute["_id"])
            attributes.append(attribute)
        return attributes

    async def create(self, data: dict) -> dict:
        """
        Tạo một thuộc tính mới trong cơ sở dữ liệu.
        Args:
            data (dict): Dữ liệu thuộc tính thô để thêm.
        Trả về dữ liệu thuộc tính đã được thêm dưới dạng dict thô.
        """
        data["createdAt"] = datetime.utcnow()
        data["updatedAt"] = datetime.utcnow()
        result = await self.collection.insert_one(data)
        new_attribute = await self.collection.find_one({"_id": result.inserted_id})
        if new_attribute:
            new_attribute["_id"] = str(new_attribute["_id"])
            return new_attribute
        raise Exception("Không thể tạo thuộc tính")

    async def update(self, attribute_id: str, data: dict) -> dict | None:
        """
        Cập nhật một thuộc tính hiện có trong cơ sở dữ liệu.
        Args:
            attribute_id (str): ID của thuộc tính cần cập nhật.
            data (dict): Dữ liệu thuộc tính thô để cập nhật.
        Trả về dữ liệu thuộc tính đã được cập nhật dưới dạng dict thô, hoặc None nếu không tìm thấy.
        """
        # Loại bỏ _id nếu có trong data để tránh lỗi khi cập nhật
        data.pop("_id", None)
        data["updatedAt"] = datetime.utcnow()
        # Using find_one_and_update similar to CategoryRepository for consistency
        updated_document = await self.collection.find_one_and_update(
            {"_id": ObjectId(attribute_id)},
            {"$set": data},
            return_document=ReturnDocument.AFTER
        )
        if updated_document:
            updated_document["_id"] = str(updated_document["_id"])
        return updated_document


