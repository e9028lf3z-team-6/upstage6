from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", 
        extra="ignore",
        env_prefix="",
        case_sensitive=False
    )

    frontend_origin: str = "http://localhost:5173"
    db_url: str = "sqlite+aiosqlite:///./data/team.db"

    upstage_api_key: str | None = None
    upstage_base_url: str = "https://api.upstage.ai/v1"
    upstage_document_parse_endpoint: str = "/document-ai/document-parse"

    # LangSmith (Observability / Eval)
    langsmith_api_key: str | None = None
    langsmith_project: str | None = None
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    langsmith_tracing: bool = False

    # Auth
    google_client_id: str | None = Field(default=None, validation_alias="GOOGLE_CLIENT_ID")
    google_client_secret: str | None = Field(default=None, validation_alias="GOOGLE_CLIENT_SECRET")
    secret_key: str = Field(default="temporary_secret_key_for_development", validation_alias="SECRET_KEY")
    access_token_expire_minutes: int = 60 * 24 * 7  # 1 week

    # Analysis feature flags (default enabled)
    enable_split_map: bool = True
    enable_normalized_issues: bool = True

_settings: Settings | None = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
