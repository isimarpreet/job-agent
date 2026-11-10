"""Loads config.toml into a typed object, like @ConfigurationProperties in Spring."""

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Settings:
    keywords: list[str]
    greenhouse_boards: list[str]
    lever_boards: list[str]


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

    return Settings(
        keywords=_text_list(data, "keywords"),
        greenhouse_boards=_text_list(data, "greenhouse_boards"),
        lever_boards=_text_list(data, "lever_boards"),
    )
