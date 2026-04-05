from app.core.exceptions import ConflictException
from app.repositories.attribute_repository import AttributeRepository
from app.schemas.attribute import (
    AttributeCreate,
    AttributeUpdate,
    AttributeCreateResponse,
    AttributeUpdateResponse, AttributeListAll,
)
from typing import List
from fastapi import HTTPException, status


class AttributeService:
    def __init__(self, attribute_repository: AttributeRepository):
        """
        Args:
            attribute_repository (AttributeRepository): Repository để tương tác với dữ liệu thuộc tính.
        """
        self._attribute_repository = attribute_repository


    async def get_all_attributes(self) -> AttributeListAll:
        """
        Lấy tất cả các thuộc tính.
        """
        raw_attributes = await self._attribute_repository.get_all()

        attributes_list = []

        for attr in raw_attributes:
            item = AttributeCreateResponse.model_validate(attr)
            attributes_list.append(item)

        return AttributeListAll(
            attributes=attributes_list
        )


    async def create_attribute(self, attribute_data: AttributeCreate) -> AttributeCreateResponse:
        """
        Tạo một thuộc tính mới.
        Kiểm tra tính duy nhất của 'code' trước khi tạo.
        """

        all_attributes = await self._attribute_repository.get_all()

        for attr in all_attributes:
            if attr["code"] == attribute_data.code:
                raise ConflictException(
                    detail=f"Thuộc tính với mã '{attribute_data.code}' đã tồn tại.",
                )

        raw_data = attribute_data.model_dump(exclude_unset=True, by_alias=True)
        new_attribute_raw = await self._attribute_repository.create(raw_data)
        return AttributeCreateResponse.model_validate(new_attribute_raw)


    async def update_attribute(
        self, attribute_id: str, attribute_data: AttributeUpdate
    ) -> AttributeUpdateResponse | None:
        """
        Cập nhật một thuộc tính hiện có.
        Kiểm tra tính duy nhất của 'code' nếu 'code' được cập nhật.
        """
        if attribute_data.code:
            all_attributes = await self._attribute_repository.get_all()
            for attr in all_attributes:
                if attr["_id"] != attribute_id and attr["code"] == attribute_data.code:
                    raise ConflictException(
                        detail=f"Thuộc tính với mã '{attribute_data.code}' đã tồn tại.",
                    )

        raw_data = attribute_data.model_dump(exclude_unset=True, by_alias=True)
        updated_attribute_raw = await self._attribute_repository.update(
            attribute_id, raw_data
        )
        if updated_attribute_raw:
            return AttributeUpdateResponse.model_validate(updated_attribute_raw)
        return None