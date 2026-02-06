from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _default_db_path() -> Path:
    return Path(os.environ.get("EDGAR_DB_PATH", Path.home() / ".edgar-db" / "edgar.db"))


def _default_user_agent() -> str:
    ua = os.environ.get("EDGAR_USER_AGENT", "")
    if not ua:
        raise ValueError(
            "EDGAR_USER_AGENT must be set (e.g. 'MyApp you@example.com'). "
            "SEC requires a User-Agent identifying your application."
        )
    return ua


@dataclass
class Config:
    user_agent: str = field(default_factory=_default_user_agent)
    db_path: Path = field(default_factory=_default_db_path)
    rate_limit: float = 10.0  # requests per second
    timeout: float = 30.0
    max_retries: int = 3

    def ensure_db_dir(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
