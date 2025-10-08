from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, desc, asc
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from passlib.context import CryptContext
from src.models.user import User
from src.schemas.user import UserCreate
from src.schemas import UserFilter
from src.core.errors import DatabaseError, ValidationError, AuthenticationError
from src.core.logging import get_logger
import uuid

logger = get_logger(__name__)


class UserNotFoundException(Exception):
    pass


class IncorrectPasswordException(Exception):
    pass


class UserService:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    @staticmethod
    async def get_user_by_email(email: str, db: AsyncSession) -> User | None:
        logger.debug(f"Looking up user by email: {email}")
        try:
            query = select(User).where(User.email == email)
            result = await db.execute(query)
            user = result.scalar_one_or_none()
            if user:
                logger.debug(f"User found: {email}")
            else:
                logger.debug(f"User not found: {email}")
            return user
        except SQLAlchemyError as e:
            logger.error(f"Database error looking up user {email}: {str(e)}")
            raise DatabaseError(f"Failed to lookup user: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error looking up user {email}: {str(e)}")
            raise DatabaseError(f"Unexpected error during user lookup: {str(e)}")

    @staticmethod
    async def _create_user_base(user_data: UserCreate, db: AsyncSession, user_id: str | None = None) -> User:
        logger.debug(f"Creating user: {user_data.email}")
        try:
            # Validate input
            if not user_data.email or not user_data.password or not user_data.full_name:
                raise ValidationError("Email, password, and full name are required")

            hashed_password = UserService.pwd_context.hash(user_data.password)
            user_kwargs = {
                "full_name": user_data.full_name,
                "email": user_data.email,
                "hashed_password": hashed_password
            }
            if user_id:
                user_kwargs["id"] = uuid.UUID(user_id)

            user = User(**user_kwargs)
            db.add(user)
            await db.commit()
            await db.refresh(user)
            logger.info(f"Successfully created user: {user_data.email}")
            return user

        except IntegrityError as e:
            logger.warning(f"Integrity error creating user {user_data.email}: {str(e)}")
            await db.rollback()
            if "email" in str(e).lower():
                raise ValidationError("A user with this email already exists")
            raise DatabaseError(f"Database constraint violation: {str(e)}")
        except SQLAlchemyError as e:
            logger.error(f"Database error creating user {user_data.email}: {str(e)}")
            await db.rollback()
            raise DatabaseError(f"Failed to create user: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error creating user {user_data.email}: {str(e)}")
            await db.rollback()
            raise DatabaseError(f"Unexpected error during user creation: {str(e)}")

    @staticmethod
    async def create_user(user_data: UserCreate, db: AsyncSession) -> User:
        return await UserService._create_user_base(user_data, db)

    @staticmethod
    async def create_user_with_id(user_id: str, user_data: UserCreate, db: AsyncSession) -> User:
        return await UserService._create_user_base(user_data, db, user_id)

    @staticmethod
    async def authenticate_user(email: str, password: str, db: AsyncSession) -> User:
        logger.debug(f"Authenticating user: {email}")
        try:
            user = await UserService.get_user_by_email(email, db)
            if not user:
                logger.warning(f"Authentication failed: user not found: {email}")
                raise AuthenticationError("Invalid email or password")

            if not UserService.pwd_context.verify(password, user.hashed_password):
                logger.warning(f"Authentication failed: invalid password for user: {email}")
                raise AuthenticationError("Invalid email or password")

            logger.info(f"Authentication successful for user: {email}")
            return user

        except AuthenticationError:
            raise
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during authentication for {email}: {str(e)}")
            raise AuthenticationError("Authentication service temporarily unavailable")

    @staticmethod
    async def delete_user(user_id: str, db: AsyncSession) -> bool:
        logger.info(f"Deleting user: {user_id}")
        try:
            from sqlalchemy import delete
            query = delete(User).where(User.id == uuid.UUID(user_id))
            result = await db.execute(query)
            await db.commit()
            deleted = result.rowcount > 0
            if deleted:
                logger.info(f"Successfully deleted user: {user_id}")
            else:
                logger.warning(f"User not found for deletion: {user_id}")
            return deleted
        except SQLAlchemyError as e:
            logger.error(f"Database error deleting user {user_id}: {str(e)}")
            await db.rollback()
            raise DatabaseError(f"Failed to delete user: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error deleting user {user_id}: {str(e)}")
            await db.rollback()
            raise DatabaseError(f"Unexpected error during user deletion: {str(e)}")

    @staticmethod
    async def list_users(db: AsyncSession, filters: UserFilter) -> list[User]:
        logger.debug(f"Listing users with filters: {filters}")
        try:
            query = select(User)
            if filters.search:
                query = query.where(
                    or_(
                        User.full_name.ilike(f"%{filters.search}%"),
                        User.email.ilike(f"%{filters.search}%")
                    )
                )
            if filters.role:
                query = query.where(User.role == filters.role)
            if filters.status:
                query = query.where(User.status == filters.status)
            order_func = desc if filters.sort_order == "desc" else asc
            query = query.order_by(order_func(getattr(User, filters.sort_by)))
            query = query.offset(filters.skip).limit(filters.limit)
            result = await db.execute(query)
            users = result.scalars().all()
            logger.info(f"Successfully retrieved {len(users)} users")
            return users
        except SQLAlchemyError as e:
            logger.error(f"Database error listing users: {str(e)}")
            raise DatabaseError(f"Failed to retrieve users: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error listing users: {str(e)}")
            raise DatabaseError(f"Unexpected error during user listing: {str(e)}")