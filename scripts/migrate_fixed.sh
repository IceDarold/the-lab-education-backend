#!/bin/bash

# Database Migration Script
# This script handles database migrations for the education backend

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    log_error "DATABASE_URL environment variable is not set"
    echo "Please set DATABASE_URL to your database connection string"
    echo "Example: export DATABASE_URL='postgresql://user:password@localhost:5432/dbname'"
    exit 1
fi

# Check if alembic is available
if ! command -v alembic &> /dev/null; then
    log_error "Alembic is not installed or not in PATH"
    echo "Please install alembic: pip install alembic"
    exit 1
fi

# Function to seed database with test data
seed_database() {
    log_info "Seeding database with test data..."

    if [ ! -f "scripts/simple_seed.py" ]; then
        log_error "Seed script not found: scripts/simple_seed.py"
        exit 1
    fi

    if python3 scripts/simple_seed.py; then
        log_success "Database seeding completed"
    else
        log_error "Database seeding failed"
        exit 1
    fi
}

# Function to apply migrations
apply_migrations() {
    log_info "Applying database migrations..."

    # Apply migrations
    if alembic upgrade head; then
        log_success "Migrations applied successfully"
        echo "Status after migration:"
        alembic current
    else
        log_error "Failed to apply migrations"
        exit 1
    fi
}

# Main script logic
case "${1:-apply}" in
    "apply")
        if apply_migrations; then
            log_success "Migration process completed successfully"
        else
            log_error "Migration process failed"
            exit 1
        fi
        ;;
    "seed")
        seed_database
        ;;
    "status")
        log_info "Checking current migration status..."
        alembic current
        ;;
    *)
        log_error "Unknown command: $1"
        echo "Usage: $0 [apply|seed|status]"
        exit 1
        ;;
esac