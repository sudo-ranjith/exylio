from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Exylio"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://exylio_user:exylio_secret@db:5432/exylio"

    # Redis
    REDIS_URL: str = "redis://:exylio_redis@redis:6379/0"

    # Auth
    SECRET_KEY: str = "change_this_secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Angel One
    ANGEL_API_KEY: str = ""
    ANGEL_CLIENT_CODE: str = ""
    ANGEL_PASSWORD: str = ""
    ANGEL_TOTP_SECRET: str = ""

    # Alerts
    SENDGRID_API_KEY: str = ""
    ALERT_FROM_EMAIL: str = "alerts@exylio.in"
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    # News / Radar
    NEWS_API_KEY: str = ""
    GDELT_ENABLED: bool = True

    # Trading defaults (₹2L capital plan)
    DEFAULT_CAPITAL: float = 200000
    MAX_POSITIONS: int = 4
    MAX_CAPITAL_PER_TRADE: float = 40000
    TARGET_PROFIT_PER_TRADE: float = 250
    STOP_LOSS_PER_TRADE: float = 200
    MAX_HOLDING_DAYS: int = 5
    DAILY_LOSS_CIRCUIT_BREAKER: float = 800
    EXCHANGE: str = "NSE"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
