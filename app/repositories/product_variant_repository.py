from pymongo.asynchronous.collection import AsyncCollection
from bson import ObjectId
from datetime import datetime
from typing import Optional, Any, List
from pymongo import ReturnDocument


class ProductVariantRepository:
    def __init__(self, collection: AsyncCollection):
        """
        Args:
            collection (AsyncCollection): MongoDB collection for product variants.
        """
        self.collection = collection

    async def get_by_product_id(self, product_id: str) -> list[dict]:
        """
        Lấy tất cả các biến thể của một sản phẩm theo product_id.
        """
        variants = []
        async for variant in self.collection.find({"productId": ObjectId(product_id)}):
            variant["_id"] = str(variant["_id"])
            variant["productId"] = str(variant["productId"])
            variants.append(variant)
        return variants

    async def create_many(self, variants_data: list[dict]) -> list[dict]:
        """
        Thêm nhiều biến thể mới vào cơ sở dữ liệu.
        """
        if not variants_data:
            return []

        for data in variants_data:
            data["createdAt"] = datetime.utcnow()
            data["updatedAt"] = datetime.utcnow()
            # Ensure productId is ObjectId
            if "productId" in data and isinstance(data["productId"], str):
                data["productId"] = ObjectId(data["productId"])
            # Ensure attributeId in attributeValues are ObjectIds
            if "attributeValues" in data and isinstance(data["attributeValues"], list):
                for attr_val in data["attributeValues"]:
                    if "attributeId" in attr_val and isinstance(attr_val["attributeId"], str):
                        attr_val["attributeId"] = ObjectId(attr_val["attributeId"])

        result = await self.collection.insert_many(variants_data)
        inserted_ids = result.inserted_ids

        created_variants = []
        for _id in inserted_ids:
            variant = await self.collection.find_one({"_id": _id})
            if variant:
                variant["_id"] = str(variant["_id"])
                variant["productId"] = str(variant["productId"])
                created_variants.append(variant)
        return created_variants

    async def delete_by_product_id(self, product_id: str) -> int:
        """
        Xóa tất cả các biến thể của một sản phẩm theo product_id.
        """
        result = await self.collection.delete_many({"productId": ObjectId(product_id)})
        return result.deleted_count

    async def update_variant(self, variant_id: str, data: dict) -> Optional[dict]:
        """
        Cập nhật một biến thể sản phẩm cụ thể.
        """
        data.pop("_id", None)  # Ensure _id is not updated
        data.pop("productId", None) # Ensure productId is not updated
        data["updatedAt"] = datetime.utcnow()

        # Ensure attributeId in attributeValues are ObjectIds if present
        if "attributeValues" in data and isinstance(data["attributeValues"], list):
            for attr_val in data["attributeValues"]:
                if "attributeId" in attr_val and isinstance(attr_val["attributeId"], str):
                    attr_val["attributeId"] = ObjectId(attr_val["attributeId"])

        updated_document = await self.collection.find_one_and_update(
            {"_id": ObjectId(variant_id)},
            {"$set": data},
            return_document=ReturnDocument.AFTER,
        )
        if updated_document:
            updated_document["_id"] = str(updated_document["_id"])
            updated_document["productId"] = str(updated_document["productId"])
        return updated_document

    async def get_by_sku(self, sku: str) -> Optional[dict]:
        """
        Lấy biến thể theo SKU.
        """
        variant = await self.collection.find_one({"sku": sku})
        if variant:
            variant["_id"] = str(variant["_id"])
            variant["productId"] = str(variant["productId"])
        return variant

    async def set_default_variant(self, product_id: str, variant_id: str) -> None:
        """
        Đặt một biến thể làm mặc định và đảm bảo chỉ có một biến thể mặc định cho mỗi sản phẩm.
        Repository chỉ thực hiện các lệnh update. Logic đảm bảo duy nhất sẽ ở Service.
        """
        # Unset all other default variants for this product
        await self.collection.update_many(
            {"productId": ObjectId(product_id), "isDefaultVariant": True},
            {"$set": {"isDefaultVariant": False, "updatedAt": datetime.utcnow()}}
        )
        # Set the specified variant as default
        await self.collection.update_one(
            {"_id": ObjectId(variant_id)},
            {"$set": {"isDefaultVariant": True, "updatedAt": datetime.utcnow()}}
        )
