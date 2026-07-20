from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    BOT_TOKEN: str
    DATABASE_URL: str
    ADMIN_ID: int
    ADMIN_ID_2: int
    ADMIN_ID_3: int | None = None


settings = Settings()