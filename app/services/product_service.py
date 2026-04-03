from app.repositories.product_repository import ProductRepository
from app.repositories.product_variant_repository import ProductVariantRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.attribute_repository import AttributeRepository
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductDetailResponse,
    ProductResponse,
    ProductListResponse,
    ProductVariantCreate,
    ProductVariantResponse,
)
from app.schemas.attribute import AttributeCreateResponse  # To validate attribute IDs
from fastapi import HTTPException, status, UploadFile
from typing import List, Dict, Any, Optional
from uuid import uuid4
from pathlib import Path
import aiofiles
from app.core.config import settings
from datetime import datetime, timezone


class ProductService:
    def __init__(
        self,
        product_repo: ProductRepository,
        product_variant_repo: ProductVariantRepository,
        category_repo: CategoryRepository,
        attribute_repo: AttributeRepository,
    ):
        self._product_repo = product_repo
        self._product_variant_repo = product_variant_repo
        self._category_repo = category_repo
        self._attribute_repo = attribute_repo

    async def _handle_image_upload(self, image_file: Optional[UploadFile]) -> Optional[str]:
        if not image_file:
            return None

        if not image_file.filename:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image file is missing filename.")

        if image_file.content_type not in settings.ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid image file type. Allowed: {', '.join(settings.ALLOWED_IMAGE_TYPES)}",
            )

        file_extension = Path(image_file.filename).suffix.lower()
        if file_extension not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file extension.")

        unique_filename = f"{uuid4()}{file_extension}"
        file_path = Path(settings.UPLOADS_DIR) / unique_filename

        Path(settings.UPLOADS_DIR).mkdir(parents=True, exist_ok=True)

        MAX_SIZE = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        total_size = 0

        async with aiofiles.open(file_path, "wb") as f:
            while chunk := await image_file.read(1024):
                total_size += len(chunk)
                if total_size > MAX_SIZE:
                    await f.close()
                    file_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"File too large. Maximum allowed is {settings.MAX_UPLOAD_SIZE_MB}MB.",
                    )
                await f.write(chunk)

        return f"{Path(settings.UPLOADS_DIR).name}/{unique_filename}"

    async def _delete_image_file(self, image_path: Optional[str]) -> None:
        if not image_path:
            return

        full_path = Path(image_path)
        # Assuming image_path comes like "uploads/filename.jpg"
        if not full_path.is_absolute():
            full_path = Path(settings.UPLOADS_DIR) / Path(image_path).name

        if full_path.is_file():
            try:
                full_path.unlink()
            except OSError as e:
                print(f"Error deleting image file {full_path}: {e}")

    async def get_all_products(
        self,
        page: int,
        page_size: int,
        search: str | None,
        filters: Dict[str, Any] | None,
    ) -> ProductListResponse:
        products_raw, total_count = await self._product_repo.get_all(
            page, page_size, search, filters
        )
        products = [ProductResponse.model_validate(p) for p in products_raw]
        return ProductListResponse(items=products, total_count=total_count, page=page, page_size=page_size)

    async def get_product_detail(self, product_id: str) -> ProductDetailResponse | None:
        product_raw = await self._product_repo.get_by_id(product_id)
        if not product_raw:
            return None

        variants_raw = await self._product_variant_repo.get_by_product_id(product_id)
        variants = [ProductVariantResponse.model_validate(v) for v in variants_raw]

        product_raw["variants"] = variants
        return ProductDetailResponse.model_validate(product_raw)

    async def create_product(self, product_data: ProductCreate, featured_image_file: Optional[UploadFile] = None) -> ProductDetailResponse:
        # 1. Validate product name and slug uniqueness
        if await self._product_repo.get_by_slug(product_data.slug):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Sản phẩm với slug '{product_data.slug}' đã tồn tại.",
            )

        # 2. Validate category existence
        if not await self._category_repo.get_category_by_id(product_data.category):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Danh mục không tồn tại."
            )

        # 3. Validate attribute IDs in variants
        all_attributes = await self._attribute_repo.get_all()
        existing_attribute_ids = {attr["_id"] for attr in all_attributes}

        for variant in product_data.variants:
            for attr_val in variant.attributeValues:
                if attr_val.attributeId not in existing_attribute_ids:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Thuộc tính với ID '{attr_val.attributeId}' không tồn tại.",
                    )
            
            # Ensure unique SKU across all variants (even if not strictly required by prompt, good practice)
            if await self._product_variant_repo.get_by_sku(variant.sku):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"SKU '{variant.sku}' đã tồn tại.",
                )

        # Handle featured image upload for the product
        featured_image_path = await self._handle_image_upload(featured_image_file)
        
        product_raw_data = product_data.model_dump(
            exclude={"variants"}, exclude_unset=True, by_alias=True
        )
        if featured_image_path:
            product_raw_data["featuredImage"] = featured_image_path
        
        new_product_raw = await self._product_repo.create(product_raw_data)
        new_product_id = new_product_raw["_id"]

        # 5. Create variants
        variants_to_create = []
        for variant_create_data in product_data.variants:
            variant_raw = variant_create_data.model_dump(exclude_unset=True, by_alias=True)
            variant_raw["productId"] = new_product_id  # Link to parent product
            variants_to_create.append(variant_raw)

        new_variants_raw = await self._product_variant_repo.create_many(variants_to_create)
        new_variants = [ProductVariantResponse.model_validate(v) for v in new_variants_raw]

        new_product_raw["variants"] = new_variants
        return ProductDetailResponse.model_validate(new_product_raw)

    async def update_product(
        self, product_id: str, product_data: ProductUpdate, featured_image_file: Optional[UploadFile] = None
    ) -> ProductDetailResponse | None:
        existing_product = await self._product_repo.get_by_id(product_id)
        if not existing_product:
            return None

        # 1. Validate slug uniqueness if provided and changed
        if product_data.slug and product_data.slug != existing_product["slug"]:
            if await self._product_repo.get_by_slug(product_data.slug):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Sản phẩm với slug '{product_data.slug}' đã tồn tại.",
                )

        # 2. Validate category existence if provided
        if product_data.category:
            if not await self._category_repo.get_category_by_id(product_data.category):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Danh mục không tồn tại."
                )
        
        # Handle featured image update for the product
        update_dict_for_product = {}
        old_featured_image_path = existing_product.get("featuredImage")

        if featured_image_file:
            new_featured_image_path = await self._handle_image_upload(featured_image_file)
            if old_featured_image_path:
                await self._delete_image_file(old_featured_image_path)
            update_dict_for_product["featuredImage"] = new_featured_image_path
        elif product_data.featuredImage is None and "featuredImage" in product_data.model_fields_set:
            # User explicitly sent featuredImage: None, meaning delete existing one
            if old_featured_image_path:
                await self._delete_image_file(old_featured_image_path)
            update_dict_for_product["featuredImage"] = None
        # Else: If no file uploaded and featuredImage not explicitly None, keep existing or use product_data.featuredImage if provided as string.

        # 3. Handle variants update (complex logic, could be more granular)
        if product_data.variants is not None:
            # Validate attribute IDs in new/updated variants
            all_attributes = await self._attribute_repo.get_all()
            existing_attribute_ids = {attr["_id"] for attr in all_attributes}

            for variant in product_data.variants:
                for attr_val in variant.attributeValues:
                    if attr_val.attributeId not in existing_attribute_ids:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Thuộc tính với ID '{attr_val.attributeId}' không tồn tại.",
                        )
                
                # Ensure unique SKU across all variants (even if not strictly required by prompt, good practice)
                # This check needs to be more robust for updates, considering existing variants
                existing_variant_by_sku = await self._product_variant_repo.get_by_sku(variant.sku)
                if existing_variant_by_sku and existing_variant_by_sku["productId"] != product_id:
                     raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"SKU '{variant.sku}' đã tồn tại cho sản phẩm khác.",
                    )

            # Before deleting existing variants, delete their associated image files
            old_variants = await self._product_variant_repo.get_by_product_id(product_id)
            for old_variant in old_variants:
                if old_variant.get("featuredImage"):
                    await self._delete_image_file(old_variant["featuredImage"])
                for img_path in old_variant.get("images", []):
                    await self._delete_image_file(img_path)

            await self._product_variant_repo.delete_by_product_id(product_id)

            variants_to_create = []
            for variant_create_data in product_data.variants:
                variant_raw = variant_create_data.model_dump(exclude_unset=True, by_alias=True)
                variant_raw["productId"] = product_id  # Link to parent product
                variants_to_create.append(variant_raw)
            await self._product_variant_repo.create_many(variants_to_create)
            # Re-fetch all variants after updates
            variants_raw = await self._product_variant_repo.get_by_product_id(product_id)
            updated_variants = [ProductVariantResponse.model_validate(v) for v in variants_raw]

            # Update existing_product with the new variants for final response construction
            existing_product["variants"] = updated_variants

        # 4. Update product
        product_update_raw_data = product_data.model_dump(
            exclude={"variants"}, exclude_unset=True, by_alias=True
        )
        product_update_raw_data.update(update_dict_for_product) # Add image updates
        
        updated_product_raw = await self._product_repo.update(
            product_id, product_update_raw_data
        )

        if updated_product_raw:
            # Ensure the variants are attached to the final response
            if "variants" not in updated_product_raw:
                if "variants" in existing_product:
                    updated_product_raw["variants"] = existing_product["variants"]
                else:
                    variants_raw = await self._product_variant_repo.get_by_product_id(product_id)
                    updated_product_raw["variants"] = [ProductVariantResponse.model_validate(v) for v in variants_raw]

            return ProductDetailResponse.model_validate(updated_product_raw)
        return None

    async def delete_product(self, product_id: str) -> bool:
        # Check if product exists
        existing_product = await self._product_repo.get_by_id(product_id)
        if not existing_product:
            return False

        # Delete product's featured image
        if existing_product.get("featuredImage"):
            await self._delete_image_file(existing_product["featuredImage"])

        # Delete associated variants and their images first
        variants_to_delete = await self._product_variant_repo.get_by_product_id(product_id)
        for variant in variants_to_delete:
            if variant.get("featuredImage"):
                await self._delete_image_file(variant["featuredImage"])
            for img_path in variant.get("images", []):
                await self._delete_image_file(img_path)
        await self._product_variant_repo.delete_by_product_id(product_id)

        # Delete the product
        return await self._product_repo.delete(product_id)