from supabase import create_client, Client
from src.core.config import settings


def get_supabase_client() -> Client:
    """
    Создаем клиент внутри функции, чтобы обеспечить совместимость с бессерверной
    средой. Это гарантирует, что для каждого "холодного" вызова функции создается
    новый, свежий клиент.
    """
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_KEY
    return create_client(url, key)


def get_supabase_admin_client() -> Client:
    """
    Создаем клиент с service role key для административных операций,
    таких как проверка существования email без RLS ограничений.
    """
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_SERVICE_ROLE_KEY
    if not key:
        raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required for admin operations")
    return create_client(url, key)

