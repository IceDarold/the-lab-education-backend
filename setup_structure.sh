#!/bin/bash

# Script to create the project structure and empty files according to the architectural plan
# Run this after the initial project setup

# Rename app directory to src to match the architecture
mv app src

# Create missing directories
mkdir -p src/api/v1
mkdir -p src/crud
mkdir -p src/db
mkdir -p src/models
mkdir -p src/schemas
mkdir -p src/services
mkdir -p alembic
mkdir -p tests

# Create empty Python files
touch src/api/v1/auth.py
touch src/api/v1/courses.py
touch src/api/v1/dashboard.py
touch src/api/__init__.py
touch src/core/security.py
touch src/crud/crud_user.py
touch src/crud/crud_course.py
touch src/db/base.py
touch src/db/session.py
touch src/models/user.py
touch src/models/course.py
touch src/models/lesson.py
touch src/schemas/user.py
touch src/schemas/course.py
touch src/schemas/token.py
touch src/services/auth_service.py
touch src/services/course_service.py
touch src/services/progress_service.py

# Create .env file
touch .env

echo "Project structure created successfully!"