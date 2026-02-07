from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _default_db_path() -> Path:
    return Path(os.environ.get("YFINANCE_DB_PATH", Path.home() / ".yfinance-db" / "yfinance.db"))


@dataclass
class Config:
    db_path: Path = field(default_factory=_default_db_path)
    rate_limit: float = 2.0  # requests per second (Yahoo is stricter than SEC)
    timeout: float = 30.0
    max_retries: int = 3

    def ensure_db_dir(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
