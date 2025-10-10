from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from src.db.base import Base


class UserLessonProgress(Base):
    __tablename__ = "user_lesson_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    course_slug = Column(String(100), index=True, nullable=False)
    lesson_slug = Column(String(100), index=True, nullable=False)
    completion_date = Column(DateTime, nullable=False)

    # Relationships
    user = relationship("User", back_populates="progress_records")
