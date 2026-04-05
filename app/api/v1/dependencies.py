from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings
from app.core.exceptions import UnauthorizedException
from app.core.security import decode_token
from app.db.mongodb import get_database
from app.repositories.token_repository import TokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserMeResponse
from app.services.auth_service import AuthService
from app.services.token_service import TokenService
from app.services.user_service import UserService
from app.services.category_service import CategoryService
from app.repositories.category_repository import CategoryRepository
from app.services.attribute_service import AttributeService
from app.repositories.attribute_repository import AttributeRepository
from app.services.product_service import ProductService # New import
from app.repositories.product_repository import ProductRepository # New import
from app.repositories.product_variant_repository import ProductVariantRepository # New import
from app.models.domain.user import User

# Định nghĩa scheme xác thực OAuth2 (header Authorization: Bearer <token>)
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

async def get_user_service(db = Depends(get_database)) -> UserService:
    user_repo = UserRepository(collection=db["users"])
    token_repo = TokenRepository(collection=db["refresh_tokens"])
    return UserService(user_repository=user_repo, token_repo=token_repo)

async def get_token_service(db = Depends(get_database)) -> TokenService:
    token_repo = TokenRepository(collection=db["refresh_tokens"])
    return TokenService(token_repo=token_repo)

async def get_auth_service(db = Depends(get_database), token_service: TokenService = Depends(get_token_service)) -> AuthService:
    user_repo = UserRepository(collection=db["users"])
    return AuthService(user_repo=user_repo,token_service=token_service)

async def get_category_service(db = Depends(get_database)) -> CategoryService:
    category_repo = CategoryRepository(collection=db["categories"])
    return CategoryService(category_repository=category_repo)

async def get_attribute_service(db = Depends(get_database)) -> AttributeService:
    attribute_repo = AttributeRepository(collection=db["attributes"])
    return AttributeService(attribute_repository=attribute_repo)

async def get_product_service(
    db = Depends(get_database),
    category_service: CategoryService = Depends(get_category_service), # To validate category existence
    attribute_service: AttributeService = Depends(get_attribute_service) # To validate attribute existence
) -> ProductService:
    product_repo = ProductRepository(collection=db["products"])
    product_variant_repo = ProductVariantRepository(collection=db["product_variants"])
    
    # We pass the repositories to the service constructor
    # The service itself will call these repositories for data access
    return ProductService(
        product_repo=product_repo,
        product_variant_repo=product_variant_repo,
        category_repo=category_service._category_repository, # Access the injected repository from the service
        attribute_repo=attribute_service._attribute_repository # Access the injected repository from the service
    )

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db = Depends(get_database)
) -> UserMeResponse:
    """
    Dependency lấy thông tin user hiện tại từ access token.
    Thực hiện truy vấn DB để đảm bảo user vẫn tồn tại và đang hoạt động.
    """
    # 1. Giải mã token để lấy email (subject)
    payload = decode_token(token)
    user_id: str = payload.get("sub")

    user_repo = UserRepository(collection=db["users"])
    user_raw = await user_repo.get_user_by_id(user_id)

    if user_raw is None:
        raise UnauthorizedException()

    if not user_raw["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is inactive"
        )

    user_raw['_id'] = str(user_id)

    return UserMeResponse(**user_raw)


async def get_admin_user(current_user: UserMeResponse = Depends(get_current_user)) -> UserMeResponse:
    """
    Dependency để đảm bảo người dùng hiện tại có vai trò "admin".
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền truy cập vào tài nguyên này."
        )
    return current_user

