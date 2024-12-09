 from pydantic import BaseSettings

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = "postgresql://username:password@localhost/db_name"

    # Application settings
    APP_NAME: str = "Wildfire Prediction System"
    DEBUG: bool = True

    # Security settings
    SECRET_KEY: str = "supersecretkey"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS settings
    ALLOWED_ORIGINS: list[str] = ["*"]  # Update with specific domains for production

    class Config:
        env_file = ".env"  # Load variables from .env file if available

# Load settings
settings = Settings()
