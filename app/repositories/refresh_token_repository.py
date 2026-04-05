from pymongo.asynchronous.collection import AsyncCollection
from app.schemas.refresh_token import RefreshTokenInDB, RefreshTokenCreate
from app.core.exceptions import ConflictException, NotFoundException

class RefreshTokenRepository:
    def __init__(self, collection: AsyncCollection):
        self.collection = collection

    async def create(self, refresh_token_in: RefreshTokenCreate) -> RefreshTokenInDB:
        """
        Create a new refresh token entry in the database.
        """
        refresh_token_db = RefreshTokenInDB(**refresh_token_in.model_dump())
        result = await self.collection.insert_one(refresh_token_db.model_dump(by_alias=True, exclude_none=True))
        refresh_token_db.id = str(result.inserted_id)
        return refresh_token_db

    async def get_by_token(self, token: str) -> RefreshTokenInDB:
        """
        Retrieve a refresh token by its token string.
        """
        refresh_token_raw = await self.collection.find_one({"refresh_token": token})
        return RefreshTokenInDB(**refresh_token_raw)

    async def delete_by_token(self, token: str):
        """
        Delete a refresh token by its token string.
        """
        result = await self.collection.delete_one({"refresh_token": token})
        if result.deleted_count == 0:
            raise NotFoundException(detail="Refresh token not found for deletion")
        
    async def delete_by_user_id(self, user_id: str):
        """
        Delete all refresh tokens for a given user ID.
        """
        await self.collection.delete_many({"user_id": user_id})
