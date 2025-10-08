from supabase import create_client, Client
from src.core.config import settings


def get_supabase_client() -> Client:
    """
    Create the client inside the function to ensure compatibility with the serverless
    environment. This guarantees that for each "cold" function call, a new, fresh client is created.
    """
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_KEY
    return create_client(url, key)


def get_supabase_admin_client() -> Client:
    """
    Create a client with service role key for administrative operations,
    such as checking email existence without RLS restrictions.
    """
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_SERVICE_ROLE_KEY
    if not key:
        raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required for admin operations")
    return create_client(url, key)

