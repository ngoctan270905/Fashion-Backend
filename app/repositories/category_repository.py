from typing import Optional, Dict, Any, List
from bson import ObjectId
from pymongo.asynchronous.collection import AsyncCollection
from pymongo import ReturnDocument

class CategoryRepository:
    def __init__(self, collection: AsyncCollection):
        self.collection = collection

    async def create_category(self, category_data: dict) -> dict:
        result = await self.collection.insert_one(category_data)
        category_data["_id"] = str(result.inserted_id)
        return category_data

    async def get_category_by_id(self, category_id: str) -> Optional[dict]:
        category = await self.collection.find_one({"_id": ObjectId(category_id)})
        if category:
            category["_id"] = str(category["_id"])
        return category

    async def get_all_categories(self, skip: int = 0, limit: int = 100) -> tuple[list[dict], int]:
        cursor = self.collection.find().skip(skip).limit(limit)

        categories = []
        async for category in cursor:
            categories.append(category)

        for category in categories:
            category["_id"] = str(category["_id"])

        total_count = await self.collection.count_documents({})
        return categories, total_count

    async def update_category(self, category_id: str, update_data: dict) -> Optional[dict]:
        updated_document = await self.collection.find_one_and_update(
            {"_id": ObjectId(category_id)},
            {"$set": update_data},
            return_document=ReturnDocument.AFTER
        )
        if updated_document:
            updated_document["_id"] = str(updated_document["_id"])
        return updated_document

    async def delete_category(self, category_id: str) -> bool:
        result = await self.collection.delete_one({"_id": ObjectId(category_id)})
        return result.deleted_count > 0

    async def get_category_by_name(self, name: str) -> Optional[dict]:
        category = await self.collection.find_one({"name": name})

        if category:
            category["_id"] = str(category["_id"])  # Convert ObjectId sang string
        return category

    async def get_category_level_by_id(self, category_id: str) -> Optional[int]:
        """Lấy level của category theo id"""
        result = await self.collection.find_one(
            {"_id": ObjectId(category_id)},
            {"level": 1, "_id": 0}
        )
        if result is None:
            return None
        return result["level"]



    async def get_category_by_slug(self, slug: str) -> Optional[dict]:
        category = await self.collection.find_one({"slug": slug})
        if category:
            category["_id"] = str(category["_id"])
        return category

    async def is_slug_taken(self, slug: str, exclude_id: Optional[str] = None) -> bool:
        query = {"slug": slug}
        if exclude_id:
            query["_id"] = {"$ne": ObjectId(exclude_id)}
        count = await self.collection.count_documents(query)
        return count > 0

    async def get_children_categories(self, parent_id: str) -> List[dict]:
        cursor = self.collection.find({"parent_id": parent_id})

        children_categories = []
        async for category in cursor:
            children_categories.append(category)

        for child in children_categories:
            child["_id"] = str(child["_id"])
        return children_categories

    async def get_max_sort_order(self) -> int:
        category = await self.collection.find_one(
            {},
            sort=[("sort_order", -1)]
        )

        if not category:
            return 0

        return category.get("sort_order", 0)