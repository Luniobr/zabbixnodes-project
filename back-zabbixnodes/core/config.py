from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    SECRET_KEY: str
    ADMIN_USER: str = "admin"
    ADMIN_PASSWORD: str
    JWT_EXPIRATION_HOURS: int = 8
    ENCRYPTION_KEY: str
    API_RATE_LIMIT: int = 60
    ZABBIX_TIMEOUT_SECONDS: int = 10
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000"

    def get_allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


settings = Settings()
