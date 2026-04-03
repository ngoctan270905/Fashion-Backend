from pymongo.asynchronous.collection import AsyncCollection
from bson import ObjectId
from datetime import datetime
from typing import Optional, Any, List, Dict
from pymongo import ReturnDocument


class ProductRepository:
    def __init__(self, collection: AsyncCollection):
        """
        Args:
            collection (AsyncCollection): MongoDB collection for products.
        """
        self.collection = collection

    async def get_all(
        self,
        page: int,
        page_size: int,
        search: str | None = None,
        filters: Dict[str, Any] | None = None,
    ) -> tuple[list[dict], int]:
        """
        Lấy tất cả các sản phẩm có phân trang, tìm kiếm và lọc.
        """
        query: Dict[str, Any] = {}
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"slug": {"$regex": search, "$options": "i"}},
            ]
        if filters:
            query.update(filters)

        skip = (page - 1) * page_size
        limit = page_size

        cursor = self.collection.find(query).skip(skip).limit(limit)

        products = []
        async for product in cursor:
            product["_id"] = str(product["_id"])
            if "category" in product:
                product["category"] = str(product["category"])
            products.append(product)

        total_count = await self.collection.count_documents(query)
        return products, total_count

    async def get_by_id(self, product_id: str) -> Optional[dict]:
        """
        Lấy chi tiết sản phẩm theo ID.
        """
        product = await self.collection.find_one({"_id": ObjectId(product_id)})
        if product:
            product["_id"] = str(product["_id"])
            if "category" in product:
                product["category"] = str(product["category"])
        return product

    async def create(self, data: dict) -> dict:
        """
        Tạo một sản phẩm mới trong cơ sở dữ liệu.
        """
        data["createdAt"] = datetime.utcnow()
        data["updatedAt"] = datetime.utcnow()
        result = await self.collection.insert_one(data)
        new_product = await self.collection.find_one({"_id": result.inserted_id})
        if new_product:
            new_product["_id"] = str(new_product["_id"])
            if "category" in new_product:
                new_product["category"] = str(new_product["category"])
            return new_product
        raise Exception("Không thể tạo sản phẩm")

    async def update(self, product_id: str, data: dict) -> Optional[dict]:
        """
        Cập nhật một sản phẩm hiện có trong cơ sở dữ liệu.
        """
        data.pop("_id", None)  # Ensure _id is not updated
        data["updatedAt"] = datetime.utcnow()

        updated_document = await self.collection.find_one_and_update(
            {"_id": ObjectId(product_id)},
            {"$set": data},
            return_document=ReturnDocument.AFTER,
        )
        if updated_document:
            updated_document["_id"] = str(updated_document["_id"])
            if "category" in updated_document:
                updated_document["category"] = str(updated_document["category"])
        return updated_document

    async def delete(self, product_id: str) -> bool:
        """
        Xóa một sản phẩm khỏi cơ sở dữ liệu.
        """
        result = await self.collection.delete_one({"_id": ObjectId(product_id)})
        return result.deleted_count > 0

    async def get_by_slug(self, slug: str) -> Optional[dict]:
        """
        Lấy sản phẩm theo slug.
        """
        product = await self.collection.find_one({"slug": slug})
        if product:
            product["_id"] = str(product["_id"])
            if "category" in product:
                product["category"] = str(product["category"])
        return product