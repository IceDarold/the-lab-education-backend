"""
Database Migration API Endpoint for Vercel
This endpoint handles database migrations during deployment
"""
import os
import subprocess
import sys
from http import HTTPStatus

def handler(request):
    """
    Vercel serverless function for database migrations
    """
    # Only allow POST requests
    if request.method != 'POST':
        return {
            'statusCode': HTTPStatus.METHOD_NOT_ALLOWED,
            'body': '{"error": "Method not allowed"}',
            'headers': {'Content-Type': 'application/json'}
        }

    # Check for authorization (optional - add your own auth logic)
    auth_header = request.headers.get('authorization', '')
    expected_token = os.environ.get('MIGRATION_TOKEN')

    if expected_token and not auth_header.startswith(f'Bearer {expected_token}'):
        return {
            'statusCode': HTTPStatus.UNAUTHORIZED,
            'body': '{"error": "Unauthorized"}',
            'headers': {'Content-Type': 'application/json'}
        }

    try:
        # Get the action from query parameters or request body
        action = request.args.get('action', 'apply')

        # Set environment variables for alembic
        env = os.environ.copy()
        database_url = env.get('DATABASE_URL')
        if not database_url:
            return {
                'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
                'body': '{"error": "DATABASE_URL not configured"}',
                'headers': {'Content-Type': 'application/json'}
            }

        # Run alembic command
        if action == 'status':
            cmd = [sys.executable, '-m', 'alembic', 'current']
        elif action == 'check':
            cmd = [sys.executable, '-m', 'alembic', 'check']
        elif action == 'apply':
            cmd = [sys.executable, '-m', 'alembic', 'upgrade', 'head']
        else:
            return {
                'statusCode': HTTPStatus.BAD_REQUEST,
                'body': '{"error": "Invalid action. Use: status, check, or apply"}',
                'headers': {'Content-Type': 'application/json'}
            }

        # Execute the command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(__file__)),
            env=env
        )

        if result.returncode == 0:
            return {
                'statusCode': HTTPStatus.OK,
                'body': f'{{"message": "Migration {action} completed successfully", "output": "{result.stdout.strip()}"}}',
                'headers': {'Content-Type': 'application/json'}
            }
        else:
            return {
                'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
                'body': f'{{"error": "Migration {action} failed", "output": "{result.stderr.strip()}"}}',
                'headers': {'Content-Type': 'application/json'}
            }

    except Exception as e:
        return {
            'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
            'body': f'{{"error": "Internal server error: {str(e)}"}}',
            'headers': {'Content-Type': 'application/json'}
        }