import os
from pydantic import BaseModel


class Settings(BaseModel):
    app_title: str = "WEB API Project"
    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db")

    nats_url: str = os.getenv("NATS_URL", "nats://127.0.0.1:4222")
    nats_subject: str = os.getenv("NATS_SUBJECT", "items.updates")

    background_period_seconds: int = int(os.getenv("BACKGROUND_PERIOD_SECONDS", "300"))


settings = Settings()
