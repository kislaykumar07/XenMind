import os


def _csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings:
    app_name: str = os.getenv("APP_NAME", "XenMind - AI Agent Reliability Lab")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./xenmind.db")
    cors_origins: list[str] = _csv(
        os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,"
            "https://lovable.dev,https://*.lovable.app",
        )
    )
    max_user_message_chars: int = int(os.getenv("MAX_USER_MESSAGE_CHARS", "4000"))


settings = Settings()
