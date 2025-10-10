from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Critical environment variables - required for app startup
    SECRET_KEY: str = "change-me-in-production"
    DATABASE_URL: str

    # Optional Supabase settings
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # Default settings
    ALGORITHM: str = "HS256"
    CONTENT_ROOT: str = "content"
    EMAIL_CHECK_DELIVERABILITY: bool = True
    DEBUG: bool = False


settings = Settings()
