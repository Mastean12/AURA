from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "AURA"
    debug: bool = True
    secret_key: str = "change-me"

    database_url: str = "postgresql+asyncpg://aura:aura@localhost:5432/aura"

    chroma_host: str = "localhost"
    chroma_port: int = 8000
    chroma_collection: str = "aura_documents"

    ai_provider: str = "gemini"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""

    upload_dir: str = "app/uploads"
    vectorstore_dir: str = "app/vectorstore"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
