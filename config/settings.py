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
    # LLM
    # -------------------------------------------------------------------------
    llm_provider: str = Field(default="groq")

    # Groq
    groq_api_key: str = Field(default="")
    groq_model: str = Field(default="llama-3.3-70b-versatile")

    # Ollama
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_model_primary: str = Field(default="llama3.2")
    ollama_model_secondary: str = Field(default="mistral")

    # OpenAI — showcased, not active by default
    # openai_api_key: str = Field(default="")
    # openai_model: str = Field(default="gpt-4o")

    # -------------------------------------------------------------------------
    # Embeddings
    # -------------------------------------------------------------------------
    embedding_provider: str = Field(default="ollama")
    embedding_model: str = Field(default="nomic-embed-text")

    # -------------------------------------------------------------------------
    # Search
    # -------------------------------------------------------------------------
    search_provider: str = Field(default="tavily")
    tavily_api_key: str = Field(default="")
    # brave_api_key: str = Field(default="")   # Brave — showcased

    # -------------------------------------------------------------------------
    # RAG
    # -------------------------------------------------------------------------
    rag_chunk_size: int = Field(default=500)
    rag_chunk_overlap: int = Field(default=50)
    rag_top_k: int = Field(default=5)


# Single shared instance — import this everywhere
settings = Settings()