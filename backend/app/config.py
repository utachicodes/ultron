from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Ultorn"
    debug: bool = True
    database_url: str = "sqlite:///./ultorn.db"
    secret_key: str = "dev-secret-change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # AI providers
    ai_provider: str = "anthropic"
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # Scanning
    scanner_timeout: int = 300
    nuclei_path: str = "nuclei"

    class Config:
        env_file = ".env"


settings = Settings()
