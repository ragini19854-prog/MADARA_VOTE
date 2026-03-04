from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Tuple

from dotenv import load_dotenv

load_dotenv()


@dataclass(slots=True)
class Settings:
    bot_token: str
    bot_username: str
    database_path: str
    support_link: str
    powered_by_text: str
    banner_url: str
    donate_qr: str
    owner_ids: Tuple[int, ...]
    log_level: str


def _parse_owner_ids(raw: str) -> Tuple[int, ...]:
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    if len(parts) != 6:
        raise ValueError("OWNER_IDS must contain exactly 6 Telegram user IDs")
    return tuple(int(p) for p in parts)


def load_settings() -> Settings:
    token = os.getenv("BOT_TOKEN", "").strip()
    username = os.getenv("BOT_USERNAME", "").strip().lstrip("@")
    if not token:
        raise ValueError("BOT_TOKEN is required")
    if not username:
        raise ValueError("BOT_USERNAME is required")

    owner_ids = _parse_owner_ids(os.getenv("OWNER_IDS", ""))

    return Settings(
        bot_token=token,
        bot_username=username,
        database_path=os.getenv("DATABASE_PATH", "giveaway.db"),
        support_link=os.getenv("SUPPORT_LINK", "https://t.me/example_support"),
        powered_by_text=os.getenv("POWERED_BY_TEXT", "Powered by Giveaway Management Bot"),
        banner_url=os.getenv("BANNER_URL", "https://picsum.photos/1024/512"),
        donate_qr=os.getenv("DONATE_QR", "https://picsum.photos/500/500"),
        owner_ids=owner_ids,
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
