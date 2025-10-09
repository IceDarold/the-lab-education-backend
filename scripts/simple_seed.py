#!/usr/bin/env python3
"""
Simple Database Seeding Script using Supabase Client
Populates the database with test data for development and testing
"""
import os
import sys
from datetime import datetime, timedelta
from uuid import uuid4

# Add src to path for imports
sys.path.insert(0, str(os.path.dirname(os.path.dirname(__file__))))

from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ SUPABASE_URL and SUPABASE_KEY environment variables are required")
    sys.exit(1)

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def create_users():
    """Create test users"""
    users_data = [
        {
            "id": str(uuid4()),
            "email": "admin@example.com",
            "full_name": "Admin User",
            "is_active": True,
            "is_superuser": True,
            "created_at": datetime.utcnow().isoformat(),
        },
        {
            "id": str(uuid4()),
            "email": "student1@example.com",
            "full_name": "Alice Johnson",
            "is_active": True,
            "is_superuser": False,
            "created_at": (datetime.utcnow() - timedelta(days=30)).isoformat(),
        },
        {
            "id": str(uuid4()),
            "email": "student2@example.com",
            "full_name": "Bob Smith",
            "is_active": True,
            "is_superuser": False,
            "created_at": (datetime.utcnow() - timedelta(days=20)).isoformat(),
        },
        {
            "id": str(uuid4()),
            "email": "student3@example.com",
            "full_name": "Charlie Brown",
            "is_active": True,
            "is_superuser": False,
            "created_at": (datetime.utcnow() - timedelta(days=10)).isoformat(),
        },
        {
            "id": str(uuid4()),
            "email": "inactive@example.com",
            "full_name": "Inactive User",
            "is_active": False,
            "is_superuser": False,
            "created_at": (datetime.utcnow() - timedelta(days=60)).isoformat(),
        },
    ]

    for user_data in users_data:
        try:
            result = supabase.table('users').insert(user_data).execute()
            print(f"✅ Created user: {user_data['email']}")
        except Exception as e:
            print(f"⚠️  User {user_data['email']} may already exist: {e}")

    return users_data

def create_courses():
    """Create test courses"""
    courses_data = [
        {
            "id": str(uuid4()),
            "title": "Introduction to Python Programming",
            "slug": "python-basics",
            "description": "Learn the fundamentals of Python programming language",
            "short_description": "Python basics for beginners",
            "difficulty_level": "beginner",
            "estimated_duration_hours": 20,
            "is_published": True,
            "created_at": (datetime.utcnow() - timedelta(days=45)).isoformat(),
            "updated_at": (datetime.utcnow() - timedelta(days=5)).isoformat(),
        },
        {
            "id": str(uuid4()),
            "title": "Machine Learning Fundamentals",
            "slug": "ml-fundamentals",
            "description": "Comprehensive introduction to machine learning concepts and algorithms",
            "short_description": "ML basics and algorithms",
            "difficulty_level": "intermediate",
            "estimated_duration_hours": 40,
            "is_published": True,
            "created_at": (datetime.utcnow() - timedelta(days=30)).isoformat(),
            "updated_at": (datetime.utcnow() - timedelta(days=2)).isoformat(),
        },
    ]

    for course_data in courses_data:
        try:
            result = supabase.table('courses').insert(course_data).execute()
            print(f"✅ Created course: {course_data['title']}")
        except Exception as e:
            print(f"⚠️  Course {course_data['title']} may already exist: {e}")

    return courses_data

def create_lessons(courses):
    """Create test lessons"""
    lessons_data = [
        {
            "id": str(uuid4()),
            "course_id": courses[0]['id'],
            "title": "Getting Started with Python",
            "slug": "python-getting-started",
            "description": "Introduction to Python installation and basic syntax",
            "content_path": "content/courses/python-basics/getting-started.lesson",
            "order": 1,
            "estimated_duration_minutes": 45,
            "is_published": True,
            "created_at": (datetime.utcnow() - timedelta(days=40)).isoformat(),
        },
        {
            "id": str(uuid4()),
            "course_id": courses[0]['id'],
            "title": "Variables and Data Types",
            "slug": "python-variables-types",
            "description": "Understanding Python variables and built-in data types",
            "content_path": "content/courses/python-basics/variables-types.lesson",
            "order": 2,
            "estimated_duration_minutes": 60,
            "is_published": True,
            "created_at": (datetime.utcnow() - timedelta(days=35)).isoformat(),
        },
        {
            "id": str(uuid4()),
            "course_id": courses[1]['id'],
            "title": "What is Machine Learning?",
            "slug": "ml-introduction",
            "description": "Overview of machine learning concepts and applications",
            "content_path": "content/courses/ml-fundamentals/introduction.lesson",
            "order": 1,
            "estimated_duration_minutes": 50,
            "is_published": True,
            "created_at": (datetime.utcnow() - timedelta(days=25)).isoformat(),
        },
    ]

    for lesson_data in lessons_data:
        try:
            result = supabase.table('lessons').insert(lesson_data).execute()
            print(f"✅ Created lesson: {lesson_data['title']}")
        except Exception as e:
            print(f"⚠️  Lesson {lesson_data['title']} may already exist: {e}")

    return lessons_data

def main():
    """Main seeding function"""
    print("🌱 Starting database seeding with Supabase...")

    # Check environment
    if os.getenv("ENVIRONMENT") == "production":
        print("❌ Seeding is not allowed in production environment")
        return

    try:
        # Create test data
        users = create_users()
        courses = create_courses()
        lessons = create_lessons(courses)

        print("\n🎉 Database seeding completed successfully!")
        print(f"   📊 Summary:")
        print(f"      👥 Users: {len(users)}")
        print(f"      📚 Courses: {len(courses)}")
        print(f"      📖 Lessons: {len(lessons)}")

        print("\n🔑 Test accounts:")
        print("   Admin: admin@example.com")
        print("   Students: student1-3@example.com")

    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()