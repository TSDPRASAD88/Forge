
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Aptitude Forge API"
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "aptitude_forge"
    cors_origins: list[str] = ["http://localhost:5173"]

    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash-lite"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
