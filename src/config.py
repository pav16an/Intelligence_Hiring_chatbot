from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    openai_api_key: str | None
    openai_model: str
    min_questions: int
    max_questions: int
    exit_keywords: tuple[str, ...]


def _parse_keywords(raw: str) -> tuple[str, ...]:
    keywords = [item.strip().lower() for item in raw.split(",") if item.strip()]
    return tuple(keywords or ["exit", "quit", "bye", "goodbye", "stop", "end"])


def load_settings() -> Settings:
    root_dir = Path(__file__).resolve().parent.parent
    data_dir = Path(os.getenv("TALENTSCOUT_DATA_DIR", str(root_dir / "data")))
    exit_keywords = _parse_keywords(
        os.getenv("TALENTSCOUT_EXIT_KEYWORDS", "exit, quit, bye, goodbye, stop, end")
    )
    return Settings(
        data_dir=data_dir,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        min_questions=int(os.getenv("MIN_TECH_QUESTIONS", "3")),
        max_questions=int(os.getenv("MAX_TECH_QUESTIONS", "5")),
        exit_keywords=exit_keywords,
    )
