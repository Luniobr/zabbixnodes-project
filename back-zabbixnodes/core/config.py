import json
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Ler variáveis de ambiente PRIMEIRO, depois do arquivo .env se existir
    # Isso permite que docker run -e VAR=valor sobrescreva o .env
    model_config = SettingsConfigDict(
        env_file=".env" if Path(".env").exists() else None,
        extra="ignore",
        # Priorizar variáveis de ambiente sobre arquivo .env
        case_sensitive=False,
    )

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
        raw = self.ALLOWED_ORIGINS.strip()
        # Aceita formato de lista JSON: ["http://a", "http://b"]
        if raw.startswith("["):
            try:
                parsed = json.loads(raw)
                return [str(o).strip() for o in parsed if str(o).strip()]
            except json.JSONDecodeError:
                pass
        # Aceita formato separado por vírgula: http://a,http://b
        return [origin.strip() for origin in raw.split(",") if origin.strip()]


settings = Settings()
