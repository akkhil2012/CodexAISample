from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CHARACTER_ID_")

    admin_user: str = "admin"
    admin_password: str = "admin"
    data_path: str = "./data/embeddings.json"
    max_upload_mb: int = 10
    top_k: int = 5
    low_confidence_threshold: float = 0.4
    request_rate_limit: int = 30
    request_rate_window_seconds: int = 60
    qdrant_url: str | None = None
    qdrant_collection: str = "characters"


settings = Settings()
