from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from src.db.base import Base


class UserLessonProgress(Base):
    __tablename__ = "user_lesson_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    course_slug = Column(String(100), index=True, nullable=False)
    lesson_slug = Column(String(100), index=True, nullable=False)
    completion_date = Column(DateTime, nullable=False)

    # Relationships
    user = relationship("User", back_populates="progress_records")