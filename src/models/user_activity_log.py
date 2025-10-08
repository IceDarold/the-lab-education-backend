from sqlalchemy import Column, Integer, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.db.base import Base


class UserActivityLog(Base):
    __tablename__ = "user_activity_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    activity_type = Column(Enum('LOGIN', 'LESSON_COMPLETED', 'QUIZ_ATTEMPT', 'CODE_EXECUTION', name='activity_type_enum'), nullable=False)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, server_default=func.now(), index=True)

    # Relationships
    user = relationship("User", back_populates="activity_logs")