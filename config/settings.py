from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path

# Project root — one level up from this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -------------------------------------------------------------------------
    # Application
    # -------------------------------------------------------------------------
    app_name: str = Field(default="Overland Intelligence System")
    app_version: str = Field(default="1.0.0")
    user_agent: str = Field(default="OverlandIntelBot/1.0")
    log_level: str = Field(default="INFO")
    output_dir: str = Field(default="output/reports")
    max_rows: int = Field(default=50000)
    suggested_question_count: int = Field(default=5)

    # -------------------------------------------------------------------------
    # LLM — all values from .env
    # -------------------------------------------------------------------------
    llm_provider: str = Field(default="")

    groq_api_key: str = Field(default="")
    groq_model: str = Field(default="")

    ollama_base_url: str = Field(default="")
    ollama_model_primary: str = Field(default="")
    ollama_model_secondary: str = Field(default="")

    # OpenAI — uncomment block in .env to activate, no code changes needed
    openai_api_key: str = Field(default="")
    openai_model_primary: str = Field(default="")
    openai_model_secondary: str = Field(default="")
    openai_base_url: str = Field(default="")   # optional — for Azure or compatible endpoints

    # -------------------------------------------------------------------------
    # Embeddings — all values from .env
    # -------------------------------------------------------------------------
    embedding_provider: str = Field(default="")
    embedding_model: str = Field(default="")

    # -------------------------------------------------------------------------
    # Search — all values from .env
    # -------------------------------------------------------------------------
    search_provider: str = Field(default="")
    tavily_api_key: str = Field(default="")
    brave_api_key: str = Field(default="")

    # -------------------------------------------------------------------------
    # RAG — tuning parameters, operational defaults are appropriate here
    # -------------------------------------------------------------------------
    rag_chunk_size: int = Field(default=500)
    rag_chunk_overlap: int = Field(default=50)
    rag_top_k: int = Field(default=5)


# Single shared instance — import this everywhere
settings = Settings()
