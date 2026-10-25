"""Typed configuration.

Two kinds of config, on purpose:
1. `Settings`: environment-level (env name, log level, paths). Comes from
   environment variables / `.env`, prefix `PPE_`. Changes per machine.
2. YAML files in `configs/`: experiment- and rule-level (training, zones).
   Validated with pydantic models via `load_config`. Changes per experiment.

Why validate: a typo like `conf: 5` should crash at startup with a clear
message, not silently produce nonsense in the middle of a stream.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Literal, TypeVar

import yaml
from pydantic import BaseModel, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from ppe.core.exceptions import ConfigError

T = TypeVar("T", bound=BaseModel)


class Settings(BaseSettings):
    """Environment-level settings. Override with e.g. `PPE_LOG_LEVEL=DEBUG`."""

    model_config = SettingsConfigDict(env_prefix="PPE_", env_file=".env", extra="ignore")

    env: Literal["dev", "staging", "prod"] = "dev"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_json: bool = False
    seed: int = 42
    data_dir: Path = Path("data")
    mlflow_tracking_uri: str | None = None


@lru_cache
def get_settings() -> Settings:
    """Settings are read once and shared (cached)."""
    return Settings()


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Read a YAML file that must contain a mapping."""
    p = Path(path)
    if not p.is_file():
        raise ConfigError(f"config file not found: {p}")
    with p.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ConfigError(f"{p} must contain a YAML mapping at the top level")
    return data


def load_config(model: type[T], path: str | Path) -> T:
    """Load a YAML file and validate it against a pydantic model."""
    try:
        return model.model_validate(load_yaml(path))
    except ValidationError as exc:
        raise ConfigError(f"invalid config {path}:\n{exc}") from exc
