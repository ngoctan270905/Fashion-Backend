from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Literal, Annotated, List
from bson import ObjectId
from datetime import datetime
from pydantic.functional_validators import BeforeValidator

# Schema cho các phần tử trong mảng 'values' của thuộc tính
class AttributeValue(BaseModel):
    value: str = Field(
        ..., min_length=1, max_length=100, description="Giá trị của thuộc tính"
    )
    # colorCode chỉ có nếu type là 'color', validate bằng regex cho hex color
    colorCode: str | None = Field(
        None,
        pattern=r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$",
        description="Mã màu hex (nếu thuộc tính là màu sắc)",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {"value": "Đen", "colorCode": "#000000"}
        },
    )


# Schema cho dữ liệu tạo thuộc tính mới
class AttributeCreate(BaseModel):
    name: str = Field(
        ..., min_length=2, max_length=100, description="Tên thuộc tính (ví dụ: Màu sắc, Kích thước)"
    )
    code: str = Field(
        ...,
        min_length=2,
        max_length=50,
        pattern=r"^[a-z0-9_]+$",
        description="Mã thuộc tính duy nhất (ví dụ: color, size). Chỉ chứa chữ thường, số và gạch dưới.",
    )
    type: Literal["color", "button", "radio", "select", "text"] = Field(
        ..., description="Kiểu hiển thị của thuộc tính"
    )
    isVariantAttribute: bool = Field(
        False, description="Thuộc tính này có phải là thuộc tính biến thể của sản phẩm không"
    )
    isFilterable: bool = Field(
        False, description="Thuộc tính này có dùng để lọc sản phẩm không"
    )
    values: list[AttributeValue] = Field(
        default_factory=list, description="Danh sách các giá trị của thuộc tính"
    )

    @field_validator("name")
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("Tên không được để trống")
        return v

    @field_validator("code")
    def validate_code(cls, v):
        if not v.strip():
            raise ValueError("Mã thuộc tính không được để trống")
        return v

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "name": "Color",
                "code": "color",
                "type": "color",
                "isVariantAttribute": True,
                "isFilterable": True,
                "values": [
                    {"value": "Đen", "colorCode": "#000000"},
                    {"value": "Trắng", "colorCode": "#FFFFFF"},
                ],
            }
        },
    )


# Schema trả về sau khi tạo thuộc tính thành công
class AttributeCreateResponse(BaseModel):
    id: str = Field(validation_alias="_id", description="ID của thuộc tính")
    name: str = Field(..., description="Tên thuộc tính")
    code: str = Field(..., description="Mã thuộc tính")
    type: Literal["color", "button", "radio", "select_box", "text", "number"] = Field(
        ..., description="Kiểu hiển thị của thuộc tính"
    )
    isVariantAttribute: bool = Field(..., description="Thuộc tính biến thể")
    isFilterable: bool = Field(..., description="Thuộc tính dùng để lọc")
    values: list[AttributeValue] = Field(..., description="Danh sách các giá trị của thuộc tính")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": "65e6e8e8e8e8e8e8e8e8e8e8",
                "name": "Color",
                "code": "color",
                "type": "color",
                "isVariantAttribute": True,
                "isFilterable": True,
                "values": [
                    {"value": "Đen", "colorCode": "#000000"}
                ]
            }
        },
    )


# Schema cho dữ liệu cập nhật thuộc tính (tất cả các trường đều tùy chọn)
class AttributeUpdate(BaseModel):
    name: str | None = Field(
        None, min_length=2, max_length=100, description="Tên thuộc tính (ví dụ: Màu sắc, Kích thước)"
    )
    code: str | None = Field(
        None,
        min_length=2,
        max_length=50,
        pattern=r"^[a-z0-9_]+$",
        description="Mã thuộc tính duy nhất (ví dụ: color, size). Chỉ chứa chữ thường, số và gạch dưới.",
    )
    type: Literal["color", "button", "radio", "select", "text"] | None = Field(
        None, description="Kiểu hiển thị của thuộc tính"
    )
    isVariantAttribute: bool | None = Field(
        None, description="Thuộc tính này có phải là thuộc tính biến thể của sản phẩm không"
    )
    isFilterable: bool | None = Field(
        None, description="Thuộc tính này có dùng để lọc sản phẩm không"
    )
    values: list[AttributeValue] | None = Field(
        None, description="Danh sách các giá trị của thuộc tính"
    )

    @field_validator("name")
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Tên không được để trống")
        return v

    @field_validator("code")
    def validate_code(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Mã thuộc tính không được để trống")
        return v

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "name": "Color (Mới)",
                "isFilterable": True,
                "values": [
                    {"value": "Xám", "colorCode": "#CCCCCC"}
                ],
            }
        },
    )


# Schema trả về sau khi cập nhật thuộc tính thành công (có thể kế thừa từ CreateResponse)
class AttributeUpdateResponse(AttributeCreateResponse):
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": "65e6e8e8e8e8e8e8e8e8e8e8",
                "name": "Color (Mới)",
                "code": "color",
                "type": "color",
                "isVariantAttribute": True,
                "isFilterable": True,
                "values": [
                    {"value": "Xám", "colorCode": "#CCCCCC"}
                ],
                "createdAt": "2023-01-01T10:00:00Z",
                "updatedAt": "2023-01-01T10:05:00Z",
            }
        },
    )


# Schema cho danh sách các thuộc tính
class AttributeListAll(BaseModel):
    attributes: List[AttributeCreateResponse] = Field(..., description="Danh sách các thuộc tính sản phẩm")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "attributes": [
                    {
                        "id": "65e6e8e8e8e8e8e8e8e8e8e8",
                        "name": "Color",
                        "code": "color",
                        "type": "color",
                        "isVariantAttribute": True,
                        "isFilterable": True,
                        "values": [
                            {"value": "Đen", "colorCode": "#000000"}
                        ],
                    },
                    {
                        "id": "65e6e8e8e8e8e8e8e8e8e8e9",
                        "name": "Size",
                        "code": "size",
                        "type": "button",
                        "isVariantAttribute": True,
                        "isFilterable": True,
                        "values": [
                            {"value": "S", "colorCode": None},
                            {"value": "M", "colorCode": None},
                        ],
                    },
                ]
            }
        },
    )