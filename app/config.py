from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    app_name: str = "ScenePilot"

    app_env: str = "development"

    debug: bool = True

    google_cloud_project: str = ""

    google_cloud_location: str = "global"

    google_genai_use_vertexai: bool = True

    gemini_model: str = "gemini-2.5-flash"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:

    return Settings()


settings = get_settings()