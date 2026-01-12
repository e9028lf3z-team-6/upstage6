from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    frontend_origin: str = "http://localhost:5173"
    db_url: str = "sqlite+aiosqlite:///./data/team.db"

    upstage_api_key: str | None = None
    upstage_base_url: str = "https://api.upstage.ai/v1"
    upstage_document_parse_endpoint: str = "/document-ai/document-parse"

_settings: Settings | None = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
