from typing import Optional, List, Dict, Any
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse, CategoryListResponse, \
    CategoryListItem, CategoryCreateResponse
from app.core.exceptions import NotFoundException, ConflictException, BadRequestException, InternalServerException
from fastapi import UploadFile, HTTPException, status
from uuid import uuid4
from pathlib import Path
import aiofiles
from slugify import slugify
from app.core.config import settings
from datetime import datetime, timezone
from bson import ObjectId

class CategoryService:
    def __init__(self, category_repository: CategoryRepository) -> None:
        self._category_repository = category_repository

    # Create category =====================================================================================================
    async def create_category(self, category_data: CategoryCreate, image_file: Optional[UploadFile]) -> CategoryCreateResponse:
        # 1. Kiểm tra tồn tại name và slug
        category_name = await self._category_repository.get_category_by_name(category_data.name)
        if category_name:
            raise ConflictException(detail=f"Danh mục {category_data.name} đã tồn tại.")
        if not category_data.slug:
            category_data.slug = slugify(category_data.name)
        slug = await self._category_repository.is_slug_taken(category_data.slug)
        if slug:
            raise ConflictException(detail=f"Slug '{category_data.slug}' đã tồn tại.")

        # 2. Xử lý parent_id và tính toán level
        category_level = await self._calculate_category_level(category_data.parent_id)
        
        # 3. Xử lí upload ảnh
        # Handle image upload
        image_url = await self._handle_image_upload(image_file)

        # Chuyển model Pydantic thành dictionary để sử dụng trong repository
        category_dict = category_data.model_dump(exclude_unset=True)
        category_dict["level"] = category_level
        max_sort_order = await self._category_repository.get_max_sort_order()
        category_dict["sort_order"] = max_sort_order + 1
        category_dict["created_at"] = datetime.now(timezone.utc)
        category_dict["updated_at"] = datetime.now(timezone.utc)

        created_category_raw = await self._category_repository.create_category(category_dict)
        return CategoryCreateResponse(**created_category_raw)

    async def _calculate_category_level(self, parent_id: Optional[str]) -> int:
        """
        Tính level cho category mới
        """

        # Không có parent → danh mục gốc
        if not parent_id:
            return 1

        # Lấy level của parent
        parent_level = await self._category_repository.get_category_level_by_id(parent_id)

        if parent_level is None:
            raise NotFoundException(detail="Parent category not found.")

        # Chỉ cho phép parent là level 1
        if parent_level != 1:
            raise BadRequestException(
                detail="Parent category must be a top-level category (level 1)."
            )

        # Hard code level 2
        return 2


    async def _handle_image_upload(self, image_file: Optional[UploadFile]) -> Optional[str]:
        if not image_file:
            return None

        # 1. Kiểm tra filename
        if not image_file.filename:
            raise BadRequestException(detail="Image file is missing filename.")

        # 2. Kiểm tra content-type (chính xác hơn)
        if image_file.content_type not in settings.ALLOWED_IMAGE_TYPES:
            raise BadRequestException(
                detail=f"Invalid image file type. Allowed: {', '.join(settings.ALLOWED_IMAGE_TYPES)}"
            )

        # 3. Kiểm tra extension
        file_extension = Path(image_file.filename).suffix.lower()
        if file_extension not in settings.ALLOWED_EXTENSIONS:
            raise BadRequestException(detail="Invalid file extension.")

        # 4. Tạo tên file unique + an toàn
        unique_filename = f"{uuid4()}{file_extension}"
        file_path = Path(settings.UPLOADS_DIR) / unique_filename

        # Tạo thư mục nếu chưa có
        Path(settings.UPLOADS_DIR).mkdir(parents=True, exist_ok=True)

        # 5. Upload với giới hạn kích thước (ngăn DoS)
        MAX_SIZE = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        total_size = 0

        async with aiofiles.open(file_path, "wb") as f:
            while chunk := await image_file.read(1024):  # đọc từng 1KB
                total_size += len(chunk)
                if total_size > MAX_SIZE:
                    await f.close()  # đóng file trước
                    file_path.unlink(missing_ok=True)  # xóa file rác
                    raise BadRequestException(
                        detail=f"File too large. Maximum allowed is {settings.MAX_UPLOAD_SIZE_MB}MB."
                    )
                await f.write(chunk)

        # Trả về URL (không mutate category_data)
        return f"{Path(settings.UPLOADS_DIR).name}/{unique_filename}"
    async def get_category_by_id(self, category_id: str) -> CategoryResponse:
        category_raw = await self._category_repository.get_category_by_id(category_id)
        if not category_raw:
            raise NotFoundException(detail=f"Category with id {category_id} not found.")
        return CategoryResponse(**category_raw)

    async def get_all_categories(self, skip: int = 0, limit: int = 100) -> CategoryListResponse:
        categories_raw, total_count = await self._category_repository.get_all_categories(skip, limit)
        category_items = [CategoryListItem(**category_data) for category_data in categories_raw]
        return CategoryListResponse(
            total_count=total_count,
            page=skip // limit + 1 if limit > 0 else 1, # Calculate current page
            page_size=limit,
            items=category_items
        )

    async def update_category(self, category_id: str, update_data: CategoryUpdate, image_file: Optional[UploadFile]) -> CategoryResponse:
        existing_category_raw = await self._category_repository.get_category_by_id(category_id)
        if not existing_category_raw:
            raise NotFoundException(detail=f"Category with id {category_id} not found.")

        update_dict = update_data.model_dump(exclude_unset=True)

        # Handle slug update
        if "name" in update_dict and "slug" not in update_dict:
            update_dict["slug"] = slugify(update_dict["name"])
        if "slug" in update_dict and update_dict["slug"] != existing_category_raw.get("slug"):
            if await self._category_repository.is_slug_taken(update_dict["slug"], exclude_id=category_id):
                raise ConflictException(detail=f"Slug '{update_dict['slug']}' is already taken.")

        # Handle parent_id and level recalculation
        if "parent_id" in update_dict and update_dict["parent_id"] != existing_category_raw.get("parent_id"):
            new_parent_id = update_dict["parent_id"]
            new_level = 1 # Default for no parent

            if new_parent_id: # New parent_id is provided
                if not ObjectId.is_valid(new_parent_id):
                    raise BadRequestException(detail="Invalid parent_id format.")
                new_parent_category_raw = await self._category_repository.get_category_by_id(new_parent_id)
                if not new_parent_category_raw:
                    raise NotFoundException(detail="New parent category not found.")
                new_parent_category_response = CategoryResponse(**new_parent_category_raw)

                if new_parent_category_response.level != 1:
                    raise BadRequestException(detail="New parent category must be a top-level category (level 1).")
                new_level = 2
            
            update_dict["level"] = new_level
        
        # Handle image upload/replacement
        if image_file:
            if not image_file.filename:
                raise BadRequestException(detail="Image file is missing filename.")
            if not image_file.content_type or not image_file.content_type.startswith("image/"):
                raise BadRequestException(detail="Invalid image file type.")

            file_extension = Path(image_file.filename).suffix
            unique_filename = f"{uuid4()}{file_extension}"
            file_path = Path(settings.UPLOADS_DIR) / unique_filename

            Path(settings.UPLOADS_DIR).mkdir(parents=True, exist_ok=True)

            async with aiofiles.open(file_path, "wb") as f:
                while content := await image_file.read(1024):
                    await f.write(content)

            # Delete old image if it exists
            old_image_url = existing_category_raw.get("image_url")
            if old_image_url:
                old_image_filename = Path(old_image_url).name
                old_image_path = Path(settings.UPLOADS_DIR) / old_image_filename
                if old_image_path.is_file():
                    try:
                        old_image_path.unlink()
                    except OSError as e:
                        print(f"Error deleting old image file {old_image_path}: {e}")

            update_dict["image_url"] = f"{Path(settings.UPLOADS_DIR).name}/{unique_filename}"
        elif "image_url" in update_dict and update_dict["image_url"] is None:
            # If image_url is explicitly set to None, delete the old image
            old_image_url = existing_category_raw.get("image_url")
            if old_image_url:
                old_image_filename = Path(old_image_url).name
                old_image_path = Path(settings.UPLOADS_DIR) / old_image_filename
                if old_image_path.is_file():
                    try:
                        old_image_path.unlink()
                    except OSError as e:
                        print(f"Error deleting old image file {old_image_path}: {e}")

        update_dict["updated_at"] = datetime.utcnow()

        updated_category_raw = await self._category_repository.update_category(category_id, update_dict)
        if not updated_category_raw:
            raise InternalServerException(detail="Failed to update category.")
        return CategoryResponse(**updated_category_raw)

    async def delete_category(self, category_id: str) -> bool:
        category_to_delete_raw = await self._category_repository.get_category_by_id(category_id)
        if not category_to_delete_raw:
            raise NotFoundException(detail=f"Category with id {category_id} not found.")

        # Check for children categories
        children = await self._category_repository.get_children_categories(category_id)
        if children:
            raise BadRequestException(detail="Cannot delete category with existing child categories.")

        # Delete associated image file
        image_url = category_to_delete_raw.get("image_url")
        if image_url:
            image_filename = Path(image_url).name
            image_path = Path(settings.UPLOADS_DIR) / image_filename
            if image_path.is_file():
                try:
                    image_path.unlink()
                except OSError as e:
                    print(f"Error deleting image file {image_path}: {e}")

        deleted = await self._category_repository.delete_category(category_id)
        if not deleted:
            raise InternalServerException(detail="Failed to delete category.")
        return deleted