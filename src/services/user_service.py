from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, desc, asc
from passlib.context import CryptContext
from src.models.user import User
from src.schemas.user import UserCreate
from src.schemas import UserFilter
import uuid


class UserNotFoundException(Exception):
    pass


class IncorrectPasswordException(Exception):
    pass


class UserService:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    @staticmethod
    async def get_user_by_email(email: str, db: AsyncSession) -> User | None:
        query = select(User).where(User.email == email)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def _create_user_base(user_data: UserCreate, db: AsyncSession, user_id: str | None = None) -> User:
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
        return user

    @staticmethod
    async def create_user(user_data: UserCreate, db: AsyncSession) -> User:
        return await UserService._create_user_base(user_data, db)

    @staticmethod
    async def create_user_with_id(user_id: str, user_data: UserCreate, db: AsyncSession) -> User:
        return await UserService._create_user_base(user_data, db, user_id)

    @staticmethod
    async def authenticate_user(email: str, password: str, db: AsyncSession) -> User | None:
        user = await UserService.get_user_by_email(email, db)
        if not user or not UserService.pwd_context.verify(password, user.hashed_password):
            return None
        return user

    @staticmethod
    async def list_users(db: AsyncSession, filters: UserFilter) -> list[User]:
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
        return result.scalars().all()