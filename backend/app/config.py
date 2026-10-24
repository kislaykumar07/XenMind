import os


def _csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _default_database_url() -> str:
    if os.getenv("DATABASE_URL"):
        url = os.environ["DATABASE_URL"]
        # Hosted Postgres strings (e.g. Neon) arrive as postgresql://, but the
        # only Postgres driver we ship is psycopg v3 — SQLAlchemy needs the
        # explicit dialect, so normalise it here instead of relying on the
        # env var's exact spelling.
        if url.startswith("postgresql://"):
            url = "postgresql+psycopg://" + url[len("postgresql://"):]
        return url
    if os.getenv("VERCEL"):
        # Serverless filesystem is read-only except /tmp.
        return "sqlite:////tmp/xenmind.db"
    return "sqlite:///./xenmind.db"


class Settings:
    app_name: str = os.getenv("APP_NAME", "XenMind - AI Agent Reliability Lab")
    database_url: str = _default_database_url()
    cors_origins: list[str] = _csv(
        os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,"
            "https://lovable.dev,https://*.lovable.app",
        )
    )
    max_user_message_chars: int = int(os.getenv("MAX_USER_MESSAGE_CHARS", "4000"))
    # Session tokens for the lab's own auth (Google sign-in verified server-side).
    # Set a real value in production; the fallback only ever signs demo sessions.
    session_secret: str = os.getenv("SESSION_SECRET", "xenmind-dev-secret-change-me")
    google_client_id: str = os.getenv(
        "GOOGLE_CLIENT_ID",
        "565488602493-f0nopvv1a1jard8v2t0rqe0bsi480us6.apps.googleusercontent.com",
    )
    # Cron protection for /api/cron/daily (Vercel Cron). Empty = endpoint disabled.
    cron_secret: str = os.getenv("CRON_SECRET", "")
    # Razorpay (optional — billing stays in preview mode until both are set).
    razorpay_key_id: str = os.getenv("RAZORPAY_KEY_ID", "")
    razorpay_key_secret: str = os.getenv("RAZORPAY_KEY_SECRET", "")
    # Server-side LLM keys (optional — users normally bring their own key, which
    # is sent per-request and never stored; server keys only power schedules).
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")


settings = Settings()
