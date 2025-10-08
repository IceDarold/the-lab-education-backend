from sqlalchemy import Column, String, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from src.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum('STUDENT', 'ADMIN', name='user_role_enum'), nullable=False, default='STUDENT')
    status = Column(Enum('ACTIVE', 'BLOCKED', name='user_status_enum'), nullable=False, default='ACTIVE')
    registration_date = Column(DateTime, server_default=func.now())

    # Relationships
    enrollments = relationship("Enrollment", back_populates="user")
    progress_records = relationship("UserLessonProgress", back_populates="user")
    activity_logs = relationship("UserActivityLog", back_populates="user")