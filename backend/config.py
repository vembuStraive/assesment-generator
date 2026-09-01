from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    database_url: str = os.getenv(
        "DATABASE_URL",
        "mysql+mysql-connector-python://root:@localhost:3306/assessbridge"
    )
    secret_key: str = os.getenv(
        "SECRET_KEY",
        "your-secret-key-change-this-in-production"
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
