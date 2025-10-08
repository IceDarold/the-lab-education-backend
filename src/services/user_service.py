from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, desc, asc
from passlib.context import CryptContext
from src.models.user import User
from src.schemas.user import UserCreate


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
    async def create_user(user_data: UserCreate, db: AsyncSession) -> User:
        hashed_password = UserService.pwd_context.hash(user_data.password)
        user = User(
            fullName=user_data.full_name,
            email=user_data.email,
            hashed_password=hashed_password
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def authenticate_user(email: str, password: str, db: AsyncSession) -> User | None:
        user = await UserService.get_user_by_email(email, db)
        if not user or not UserService.pwd_context.verify(password, user.hashed_password):
            return None
        return user

    @staticmethod
    async def list_users(
        db: AsyncSession,
        search: str | None = None,
        role: str | None = None,
        status: str | None = None,
        sort_by: str = "registrationDate",
        sort_order: str = "desc",
        skip: int = 0,
        limit: int = 100
    ) -> list[User]:
        query = select(User)
        if search:
            query = query.where(
                or_(
                    User.fullName.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%")
                )
            )
        if role:
            query = query.where(User.role == role)
        if status:
            query = query.where(User.status == status)
        order_func = desc if sort_order == "desc" else asc
        query = query.order_by(order_func(getattr(User, sort_by)))
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()