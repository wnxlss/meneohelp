import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# ЗАГРУЖАЕМ .env файл
load_dotenv()

def _parse_admin_ids(value: str) -> List[int]:
    if not value:
        return []
    return [int(item.strip()) for item in value.split(",") if item.strip()]


@dataclass(slots=True)
class Settings:
    bot_token: str = field(default_factory=lambda: os.getenv("BOT_TOKEN", ""))
    support_group_id: int = field(default_factory=lambda: int(os.getenv("SUPPORT_GROUP_ID", "0")))
    admin_ids: List[int] = field(default_factory=lambda: _parse_admin_ids(os.getenv("ADMIN_IDS", "")))
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/app.db"))
    redis_dsn: str = field(default_factory=lambda: os.getenv("REDIS_DSN", "redis://redis:6379/0"))
    log_dir: Path = field(default_factory=lambda: Path(os.getenv("LOG_DIR", "logs")))
    faq_markdown_v2: str = field(default_factory=lambda: os.getenv("FAQ_DEFAULT", "*FAQ пока пуст*"))
    flood_interval_seconds: float = field(default_factory=lambda: float(os.getenv("FLOOD_INTERVAL_SECONDS", "2")))
    max_open_tickets_per_user: int = field(default_factory=lambda: int(os.getenv("MAX_OPEN_TICKETS_PER_USER", "5")))

    def validate(self) -> None:
        if not self.bot_token:
            raise ValueError("BOT_TOKEN is required")
        if not self.support_group_id:
            raise ValueError("SUPPORT_GROUP_ID is required")


settings = Settings()