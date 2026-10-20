import sys
from pathlib import Path
from pydantic_settings import BaseSettings

from app.core.paths import DB_PATH

# Descobre o caminho do .env dinamicamente
if getattr(sys, "frozen", False):
    ENV_FILE = Path(sys.executable).parent / ".env"
else:
    ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

class Settings(BaseSettings):
    # ----- Aplicação (com valores padrão à prova de falhas) -----
    APP_NAME: str = "Genesis - Faturação"
    APP_VERSION: str = "1.0.0"

    # ----- Segurança / JWT -----
    SECRET_KEY: str = "chave-secreta-padrao-mude-isso-em-producao-123456"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_MINUTES: int = 15

    # ----- Admin inicial (seed) -----
    INITIAL_ADMIN_USERNAME: str = "admin"
    INITIAL_ADMIN_PASSWORD: str = "admin123"

    # ----- Base de dados -----
    DATABASE_URL: str = f"sqlite:///{DB_PATH}"

    # ----- Fiscal -----
    PUBLIC_VERIFY_BASE_URL: str = "http://localhost:5173"
    SIGNING_ENABLED: bool = True

    # ----- CORS -----
    CORS_ORIGINS: str = "http://localhost:5173"

    class Config:
        # O Pydantic usa esta variável para saber onde procurar o ficheiro
        env_file = str(ENV_FILE)
        env_file_encoding = "utf-8"
        extra = "ignore"

# Forçar a criação da instância
settings = Settings()