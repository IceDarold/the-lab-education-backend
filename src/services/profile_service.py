from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from src.models.profile import Profile
from src.core.errors import DatabaseError, ValidationError
from src.core.logging import get_logger
from src.core.utils import maybe_await
import uuid

logger = get_logger(__name__)


class ProfileService:
    @staticmethod
    async def create_profile(
        profile_id: str,
        full_name: str,
        email: str,
        role: str = "student",
        db: AsyncSession = None
    ) -> Profile:
        """Create a new profile record"""
        logger.debug(f"Creating profile for user: {profile_id}")
        try:
            # Validate input
            if not profile_id or not full_name or not email:
                raise ValidationError("Profile ID, full name, and email are required")

            try:
                profile_uuid = uuid.UUID(profile_id)
            except ValueError:
                raise ValidationError(f"Invalid profile ID format: {profile_id}")

            profile = Profile(
                id=profile_uuid,
                email=email,
                full_name=full_name,
                role=role
            )

            if db:
                await maybe_await(db.add(profile))
                await db.commit()
                await db.refresh(profile)
            else:
                # If no db session provided, this is for future use
                pass

            logger.info(f"Successfully created profile: {profile_id}")
            return profile

        except IntegrityError as e:
            logger.warning(f"Integrity error creating profile {profile_id}: {str(e)}")
            if db:
                await db.rollback()
            if "id" in str(e).lower():
                raise ValidationError("A profile with this ID already exists")
            raise DatabaseError(f"Database constraint violation: {str(e)}")
        except SQLAlchemyError as e:
            logger.error(f"Database error creating profile {profile_id}: {str(e)}")
            if db:
                await db.rollback()
            raise DatabaseError(f"Failed to create profile: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error creating profile {profile_id}: {str(e)}")
            if db:
                await db.rollback()
            raise DatabaseError(f"Unexpected error during profile creation: {str(e)}")

    @staticmethod
    async def get_profile_by_id(profile_id: str, db: AsyncSession) -> Optional[Profile]:
        """Get profile by ID"""
        logger.debug(f"Looking up profile by ID: {profile_id}")
        try:
            try:
                profile_uuid = uuid.UUID(profile_id)
            except ValueError:
                raise ValidationError(f"Invalid profile ID format: {profile_id}")

            query = select(Profile).where(Profile.id == profile_uuid)
            result = await db.execute(query)
            profile = await maybe_await(result.scalar_one_or_none())
            if profile:
                logger.debug(f"Profile found: {profile_id}")
            else:
                logger.debug(f"Profile not found: {profile_id}")
            return profile
        except SQLAlchemyError as e:
            logger.error(f"Database error looking up profile {profile_id}: {str(e)}")
            raise DatabaseError(f"Failed to lookup profile: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error looking up profile {profile_id}: {str(e)}")
            raise DatabaseError(f"Unexpected error during profile lookup: {str(e)}")

    @staticmethod
    async def delete_profile(profile_id: str, db: AsyncSession) -> bool:
        """Delete a profile"""
        logger.info(f"Deleting profile: {profile_id}")
        try:
            from sqlalchemy import delete
            try:
                profile_uuid = uuid.UUID(profile_id)
            except ValueError:
                raise ValidationError(f"Invalid profile ID format: {profile_id}")

            query = delete(Profile).where(Profile.id == profile_uuid)
            result = await db.execute(query)
            await db.commit()
            deleted = result.rowcount > 0
            if deleted:
                logger.info(f"Successfully deleted profile: {profile_id}")
            else:
                logger.warning(f"Profile not found for deletion: {profile_id}")
            return deleted
        except SQLAlchemyError as e:
            logger.error(f"Database error deleting profile {profile_id}: {str(e)}")
            await db.rollback()
            raise DatabaseError(f"Failed to delete profile: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error deleting profile {profile_id}: {str(e)}")
            await db.rollback()
            raise DatabaseError(f"Unexpected error during profile deletion: {str(e)}")
