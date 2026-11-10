"""Loads config.toml into a typed object, like @ConfigurationProperties in Spring."""

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Settings:
    model: str
    min_score: int
    max_new_jobs_per_run: int
    keywords: list[str]
    greenhouse_boards: list[str]
    lever_boards: list[str]


def _whole_number(data: dict[str, Any], key: str, low: int, high: int | None = None) -> int:
    value = data.get(key)
    # bool is a kind of int in Python, so it has to be excluded explicitly.
    if not isinstance(value, int) or isinstance(value, bool) or value < low or (
        high is not None and value > high
    ):
        allowed = f"from {low} to {high}" if high is not None else f"{low} or more"
        raise ValueError(f"config.toml: {key} must be a whole number {allowed}")
    return value


def _text_list(data: dict[str, Any], key: str) -> list[str]:
    value = data.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f'config.toml: {key} must be a list like ["one", "two"]')
    return value


def load_settings() -> Settings:
    path = Path.cwd() / "config.toml"
    if not path.exists():
        raise ValueError("config.toml not found in this folder.")
    try:
        with path.open("rb") as file:  # tomllib requires binary mode.
            data = tomllib.load(file)
    except tomllib.TOMLDecodeError as error:
        raise ValueError(f"config.toml has a syntax error: {error}") from error

    model = data.get("model")
    if not isinstance(model, str) or not model.strip():
        raise ValueError("config.toml: model must be a model name in quotes")
    return Settings(
        model=model,
        min_score=_whole_number(data, "min_score", 0, 100),
        max_new_jobs_per_run=_whole_number(data, "max_new_jobs_per_run", 0),
        keywords=_text_list(data, "keywords"),
        greenhouse_boards=_text_list(data, "greenhouse_boards"),
        lever_boards=_text_list(data, "lever_boards"),
    )
