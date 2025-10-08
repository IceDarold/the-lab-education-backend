#!/usr/bin/env python3
"""
Database Seeding Script
Populates the database with test data for development and testing
"""
import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy.ext.asyncio import AsyncSession
from src.db.session import get_db_session
from src.models.user import User
from src.models.course import Course
from src.models.lesson import Lesson
from src.models.enrollment import Enrollment
from src.models.user_lesson_progress import UserLessonProgress
from src.models.user_activity_log import UserActivityLog
from src.core.security import get_password_hash


async def create_users(db: AsyncSession) -> list[User]:
    """Create test users"""
    users_data = [
        {
            "id": uuid4(),
            "email": "admin@example.com",
            "full_name": "Admin User",
            "hashed_password": get_password_hash("admin123"),
            "is_active": True,
            "is_superuser": True,
            "created_at": datetime.utcnow(),
        },
        {
            "id": uuid4(),
            "email": "student1@example.com",
            "full_name": "Alice Johnson",
            "hashed_password": get_password_hash("student123"),
            "is_active": True,
            "is_superuser": False,
            "created_at": datetime.utcnow() - timedelta(days=30),
        },
        {
            "id": uuid4(),
            "email": "student2@example.com",
            "full_name": "Bob Smith",
            "hashed_password": get_password_hash("student123"),
            "is_active": True,
            "is_superuser": False,
            "created_at": datetime.utcnow() - timedelta(days=20),
        },
        {
            "id": uuid4(),
            "email": "student3@example.com",
            "full_name": "Charlie Brown",
            "hashed_password": get_password_hash("student123"),
            "is_active": True,
            "is_superuser": False,
            "created_at": datetime.utcnow() - timedelta(days=10),
        },
        {
            "id": uuid4(),
            "email": "inactive@example.com",
            "full_name": "Inactive User",
            "hashed_password": get_password_hash("inactive123"),
            "is_active": False,
            "is_superuser": False,
            "created_at": datetime.utcnow() - timedelta(days=60),
        },
    ]

    users = []
    for user_data in users_data:
        user = User(**user_data)
        db.add(user)
        users.append(user)

    await db.commit()
    print(f"✅ Created {len(users)} test users")
    return users


async def create_courses(db: AsyncSession) -> list[Course]:
    """Create test courses"""
    courses_data = [
        {
            "id": uuid4(),
            "title": "Introduction to Python Programming",
            "slug": "python-basics",
            "description": "Learn the fundamentals of Python programming language",
            "short_description": "Python basics for beginners",
            "difficulty_level": "beginner",
            "estimated_duration_hours": 20,
            "is_published": True,
            "created_at": datetime.utcnow() - timedelta(days=45),
            "updated_at": datetime.utcnow() - timedelta(days=5),
        },
        {
            "id": uuid4(),
            "title": "Machine Learning Fundamentals",
            "slug": "ml-fundamentals",
            "description": "Comprehensive introduction to machine learning concepts and algorithms",
            "short_description": "ML basics and algorithms",
            "difficulty_level": "intermediate",
            "estimated_duration_hours": 40,
            "is_published": True,
            "created_at": datetime.utcnow() - timedelta(days=30),
            "updated_at": datetime.utcnow() - timedelta(days=2),
        },
        {
            "id": uuid4(),
            "title": "Advanced Data Structures",
            "slug": "data-structures-advanced",
            "description": "Deep dive into advanced data structures and algorithms",
            "short_description": "Advanced algorithms",
            "difficulty_level": "advanced",
            "estimated_duration_hours": 35,
            "is_published": True,
            "created_at": datetime.utcnow() - timedelta(days=15),
            "updated_at": datetime.utcnow() - timedelta(days=1),
        },
        {
            "id": uuid4(),
            "title": "Web Development with React",
            "slug": "react-web-dev",
            "description": "Build modern web applications with React",
            "short_description": "React development",
            "difficulty_level": "intermediate",
            "estimated_duration_hours": 30,
            "is_published": False,  # Draft course
            "created_at": datetime.utcnow() - timedelta(days=7),
            "updated_at": datetime.utcnow() - timedelta(hours=12),
        },
    ]

    courses = []
    for course_data in courses_data:
        course = Course(**course_data)
        db.add(course)
        courses.append(course)

    await db.commit()
    print(f"✅ Created {len(courses)} test courses")
    return courses


async def create_lessons(db: AsyncSession, courses: list[Course]) -> list[Lesson]:
    """Create test lessons for courses"""
    lessons_data = [
        # Python Basics Course
        {
            "id": uuid4(),
            "course_id": courses[0].id,
            "title": "Getting Started with Python",
            "slug": "python-getting-started",
            "description": "Introduction to Python installation and basic syntax",
            "content_path": "content/courses/python-basics/getting-started.lesson",
            "order": 1,
            "estimated_duration_minutes": 45,
            "is_published": True,
            "created_at": datetime.utcnow() - timedelta(days=40),
        },
        {
            "id": uuid4(),
            "course_id": courses[0].id,
            "title": "Variables and Data Types",
            "slug": "python-variables-types",
            "description": "Understanding Python variables and built-in data types",
            "content_path": "content/courses/python-basics/variables-types.lesson",
            "order": 2,
            "estimated_duration_minutes": 60,
            "is_published": True,
            "created_at": datetime.utcnow() - timedelta(days=35),
        },
        {
            "id": uuid4(),
            "course_id": courses[0].id,
            "title": "Control Flow",
            "slug": "python-control-flow",
            "description": "Learn about if statements, loops, and control structures",
            "content_path": "content/courses/python-basics/control-flow.lesson",
            "order": 3,
            "estimated_duration_minutes": 75,
            "is_published": True,
            "created_at": datetime.utcnow() - timedelta(days=30),
        },
        # ML Fundamentals Course
        {
            "id": uuid4(),
            "course_id": courses[1].id,
            "title": "What is Machine Learning?",
            "slug": "ml-introduction",
            "description": "Overview of machine learning concepts and applications",
            "content_path": "content/courses/ml-fundamentals/introduction.lesson",
            "order": 1,
            "estimated_duration_minutes": 50,
            "is_published": True,
            "created_at": datetime.utcnow() - timedelta(days=25),
        },
        {
            "id": uuid4(),
            "course_id": courses[1].id,
            "title": "Supervised vs Unsupervised Learning",
            "slug": "ml-supervised-unsupervised",
            "description": "Understanding different types of machine learning",
            "content_path": "content/courses/ml-fundamentals/supervised-unsupervised.lesson",
            "order": 2,
            "estimated_duration_minutes": 65,
            "is_published": True,
            "created_at": datetime.utcnow() - timedelta(days=20),
        },
        # Data Structures Course
        {
            "id": uuid4(),
            "course_id": courses[2].id,
            "title": "Advanced Trees and Graphs",
            "slug": "advanced-trees-graphs",
            "description": "Complex tree structures and graph algorithms",
            "content_path": "content/courses/data-structures/trees-graphs.lesson",
            "order": 1,
            "estimated_duration_minutes": 90,
            "is_published": True,
            "created_at": datetime.utcnow() - timedelta(days=10),
        },
    ]

    lessons = []
    for lesson_data in lessons_data:
        lesson = Lesson(**lesson_data)
        db.add(lesson)
        lessons.append(lesson)

    await db.commit()
    print(f"✅ Created {len(lessons)} test lessons")
    return lessons


async def create_enrollments(db: AsyncSession, users: list[User], courses: list[Course]) -> list[Enrollment]:
    """Create test enrollments"""
    enrollments_data = [
        # Active students in Python course
        {
            "id": uuid4(),
            "user_id": users[1].id,  # Alice
            "course_id": courses[0].id,  # Python Basics
            "enrolled_at": datetime.utcnow() - timedelta(days=25),
            "completed_at": None,
            "progress_percentage": 60.0,
        },
        {
            "id": uuid4(),
            "user_id": users[2].id,  # Bob
            "course_id": courses[0].id,  # Python Basics
            "enrolled_at": datetime.utcnow() - timedelta(days=20),
            "completed_at": datetime.utcnow() - timedelta(days=5),
            "progress_percentage": 100.0,
        },
        # Charlie in ML course
        {
            "id": uuid4(),
            "user_id": users[3].id,  # Charlie
            "course_id": courses[1].id,  # ML Fundamentals
            "enrolled_at": datetime.utcnow() - timedelta(days=15),
            "completed_at": None,
            "progress_percentage": 30.0,
        },
        # Alice also in Data Structures
        {
            "id": uuid4(),
            "user_id": users[1].id,  # Alice
            "course_id": courses[2].id,  # Data Structures
            "enrolled_at": datetime.utcnow() - timedelta(days=8),
            "completed_at": None,
            "progress_percentage": 10.0,
        },
    ]

    enrollments = []
    for enrollment_data in enrollments_data:
        enrollment = Enrollment(**enrollment_data)
        db.add(enrollment)
        enrollments.append(enrollment)

    await db.commit()
    print(f"✅ Created {len(enrollments)} test enrollments")
    return enrollments


async def create_progress(db: AsyncSession, users: list[User], lessons: list[Lesson]) -> list[UserLessonProgress]:
    """Create test lesson progress"""
    progress_data = [
        # Alice's progress in Python course
        {
            "id": uuid4(),
            "user_id": users[1].id,
            "lesson_id": lessons[0].id,  # Python getting started
            "started_at": datetime.utcnow() - timedelta(days=20),
            "completed_at": datetime.utcnow() - timedelta(days=18),
            "time_spent_minutes": 45,
            "score": 95.0,
        },
        {
            "id": uuid4(),
            "user_id": users[1].id,
            "lesson_id": lessons[1].id,  # Python variables
            "started_at": datetime.utcnow() - timedelta(days=15),
            "completed_at": datetime.utcnow() - timedelta(days=12),
            "time_spent_minutes": 60,
            "score": 88.0,
        },
        {
            "id": uuid4(),
            "user_id": users[1].id,
            "lesson_id": lessons[2].id,  # Python control flow
            "started_at": datetime.utcnow() - timedelta(days=10),
            "completed_at": None,
            "time_spent_minutes": 30,
            "score": None,
        },
        # Bob completed all Python lessons
        {
            "id": uuid4(),
            "user_id": users[2].id,
            "lesson_id": lessons[0].id,
            "started_at": datetime.utcnow() - timedelta(days=18),
            "completed_at": datetime.utcnow() - timedelta(days=16),
            "time_spent_minutes": 40,
            "score": 92.0,
        },
        {
            "id": uuid4(),
            "user_id": users[2].id,
            "lesson_id": lessons[1].id,
            "started_at": datetime.utcnow() - timedelta(days=14),
            "completed_at": datetime.utcnow() - timedelta(days=11),
            "time_spent_minutes": 55,
            "score": 87.0,
        },
        {
            "id": uuid4(),
            "user_id": users[2].id,
            "lesson_id": lessons[2].id,
            "started_at": datetime.utcnow() - timedelta(days=8),
            "completed_at": datetime.utcnow() - timedelta(days=5),
            "time_spent_minutes": 70,
            "score": 91.0,
        },
    ]

    progress_records = []
    for progress_item in progress_data:
        progress = UserLessonProgress(**progress_item)
        db.add(progress)
        progress_records.append(progress)

    await db.commit()
    print(f"✅ Created {len(progress_records)} test progress records")
    return progress_records


async def create_activity_logs(db: AsyncSession, users: list[User]) -> list[UserActivityLog]:
    """Create test activity logs"""
    activities = [
        ("login", "User logged in"),
        ("lesson_start", "Started lesson"),
        ("lesson_complete", "Completed lesson"),
        ("course_enroll", "Enrolled in course"),
        ("quiz_attempt", "Attempted quiz"),
        ("profile_update", "Updated profile"),
    ]

    activity_logs = []
    base_time = datetime.utcnow() - timedelta(days=30)

    for i, user in enumerate(users[1:4]):  # Skip admin and inactive user
        for j, (activity_type, description) in enumerate(activities):
            # Create multiple activities per user with some time variation
            for k in range(2 if activity_type in ["login", "lesson_start"] else 1):
                log_entry = UserActivityLog(
                    id=uuid4(),
                    user_id=user.id,
                    activity_type=activity_type,
                    description=f"{description} - Activity {k+1}",
                    metadata={"course_id": str(uuid4()), "lesson_id": str(uuid4())} if "lesson" in activity_type else {},
                    ip_address=f"192.168.1.{100+i}",
                    user_agent="Mozilla/5.0 (Test Browser)",
                    created_at=base_time + timedelta(days=j*2, hours=k*3),
                )
                db.add(log_entry)
                activity_logs.append(log_entry)

    await db.commit()
    print(f"✅ Created {len(activity_logs)} test activity logs")
    return activity_logs


async def main():
    """Main seeding function"""
    print("🌱 Starting database seeding...")

    # Check environment
    if os.getenv("ENVIRONMENT") == "production":
        print("❌ Seeding is not allowed in production environment")
        return

    async with get_db_session() as db:
        try:
            # Create test data in order
            users = await create_users(db)
            courses = await create_courses(db)
            lessons = await create_lessons(db, courses)
            enrollments = await create_enrollments(db, users, courses)
            progress = await create_progress(db, users, lessons)
            activities = await create_activity_logs(db, users)

            print("\n🎉 Database seeding completed successfully!")
            print(f"   📊 Summary:")
            print(f"      👥 Users: {len(users)}")
            print(f"      📚 Courses: {len(courses)}")
            print(f"      📖 Lessons: {len(lessons)}")
            print(f"      🎓 Enrollments: {len(enrollments)}")
            print(f"      📈 Progress records: {len(progress)}")
            print(f"      📋 Activity logs: {len(activities)}")

            print("\n🔑 Test accounts:")
            print("   Admin: admin@example.com / admin123")
            print("   Students: student1-3@example.com / student123")

        except Exception as e:
            print(f"❌ Error during seeding: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())