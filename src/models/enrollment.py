from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.db.base import Base


class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    course_slug = Column(String(100), index=True, nullable=False)
    enrollment_date = Column(DateTime, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="enrollments")