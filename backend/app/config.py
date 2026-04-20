from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/skill_tester"
    openrouter_api_key: str = ""
    brave_api_key: str = ""
    default_model: str = "moonshotai/kimi-k2"
    cors_origins: str = "http://localhost:5173"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
