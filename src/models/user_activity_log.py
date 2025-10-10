from sqlalchemy import Column, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from src.db.base import Base


class UserActivityLog(Base):
    __tablename__ = "user_activity_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    activity_type = Column(Enum('LOGIN', 'LESSON_COMPLETED', 'QUIZ_ATTEMPT', 'CODE_EXECUTION', name='activity_type_enum'), nullable=False)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, server_default=func.now(), index=True)

    # Relationships
    user = relationship("User", back_populates="activity_logs")
