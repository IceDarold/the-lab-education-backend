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

# Function to show current migration status
show_status() {
    log_info "Checking current migration status..."
    echo "Current revision:"
    alembic current
    echo ""
    echo "Heads:"
    alembic heads
    echo ""
    echo "History:"
    alembic history --verbose
}

# Function to check if migrations are needed
check_migrations() {
    log_info "Checking if migrations are needed..."
    if alembic check 2>/dev/null; then
        log_success "All migrations are up to date"
        return 0
    else
        log_warning "Migrations are needed"
        return 1
    fi
}

# Function to apply migrations
apply_migrations() {
    log_info "Applying database migrations..."

    # Show status before migration
    echo "Status before migration:"
    alembic current
    echo ""

    # Apply migrations
    if alembic upgrade head; then
        log_success "Migrations applied successfully"

        # Show status after migration
        echo ""
        echo "Status after migration:"
        alembic current
    else
        log_error "Failed to apply migrations"
        exit 1
    fi
}

# Function to create backup
create_backup() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="backup_${timestamp}.sql"

    log_info "Creating database backup: ${backup_file}"

    if command -v pg_dump &> /dev/null; then
        if pg_dump "$DATABASE_URL" > "$backup_file"; then
            log_success "Backup created: ${backup_file}"
            echo "To restore: psql '$DATABASE_URL' < ${backup_file}"
        else
            log_error "Failed to create backup"
            exit 1
        fi
    else
        log_warning "pg_dump not found, skipping backup"
    fi
}

# Function to rollback on failure
rollback_migration() {
    log_warning "Rolling back last migration..."
    if alembic downgrade -1; then
        log_success "Rollback completed"
    else
        log_error "Failed to rollback migration"
        exit 1
    fi
}

# Function to generate new migration
generate_migration() {
    local message="$1"
    if [ -z "$message" ]; then
        message="Auto-generated migration"
    fi

    log_info "Generating new migration: ${message}"
    if alembic revision --autogenerate -m "$message"; then
        log_success "Migration generated successfully"
        echo "Please review the generated migration file before applying"
    else
        log_error "Failed to generate migration"
        exit 1
    fi
}
# Function to seed database with test data
seed_database() {
    log_info "Seeding database with test data..."

    if [ ! -f "scripts/seed_database.py" ]; then
        log_error "Seed script not found: scripts/seed_database.py"
        exit 1
    fi

    if python scripts/seed_database.py; then
        log_success "Database seeding completed"
    else
        log_error "Database seeding failed"
        exit 1
    fi
}

# Main script logic
case "${1:-apply}" in
    "status")
        show_status
        ;;
    "check")
        if check_migrations; then
            exit 0
        else
            exit 1
        fi
        ;;
    "apply")
        create_backup
        if apply_migrations; then
            log_success "Migration process completed successfully"
        else
            log_error "Migration process failed"
            echo "You may need to rollback manually:"
    "seed")
        seed_database
        ;;
            echo "alembic downgrade -1"
            exit 1
        fi
        ;;
    "backup")
        create_backup
        ;;
    "rollback")
        rollback_migration
        ;;
    "generate")
        generate_migration "$2"
        ;;
  seed       Populate database with test data
    "help"|"-h"|"--help")
        echo "Database Migration Script"
        echo ""
        echo "Usage: $0 [command] [options]"
        echo ""
        echo "Commands:"
        echo "  status     Show current migration status"
        echo "  check      Check if migrations are needed"
        echo "  apply      Apply all pending migrations (default)"
        echo "  backup     Create database backup"
        echo "  rollback   Rollback last migration"
        echo "  generate   Generate new migration"
        echo "  help       Show this help message"
        echo ""
        echo "Environment variables:"
        echo "  DATABASE_URL    Database connection string (required)"
        echo ""
        echo "Examples:"
        echo "  $0 status"
        echo "  $0 apply"
        echo "  $0 generate 'Add new table'"
        ;;
    *)
        log_error "Unknown command: $1"
        echo "Run '$0 help' for usage information"
        exit 1
        ;;
esac