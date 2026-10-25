from pathlib import Path

import pytest
from pydantic import BaseModel, Field, ValidationError

from ppe.core.config import Settings, load_config, load_yaml
from ppe.core.exceptions import ConfigError


class DemoConfig(BaseModel):
    conf_threshold: float = Field(ge=0.0, le=1.0)
    iou_threshold: float = Field(ge=0.0, le=1.0)


def test_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ("PPE_ENV", "PPE_LOG_LEVEL", "PPE_SEED"):
        monkeypatch.delenv(key, raising=False)
    s = Settings(_env_file=None)
    assert s.env == "dev"
    assert s.log_level == "INFO"
    assert s.seed == 42


def test_settings_read_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PPE_SEED", "7")
    monkeypatch.setenv("PPE_ENV", "staging")
    s = Settings(_env_file=None)
    assert s.seed == 7
    assert s.env == "staging"


def test_settings_reject_unknown_environment_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PPE_ENV", "banana")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_load_config_valid(tmp_path: Path) -> None:
    f = tmp_path / "eval.yaml"
    f.write_text("conf_threshold: 0.25\niou_threshold: 0.5\n")
    cfg = load_config(DemoConfig, f)
    assert cfg.conf_threshold == 0.25


def test_load_config_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="not found"):
        load_config(DemoConfig, tmp_path / "nope.yaml")


def test_load_config_out_of_range_value(tmp_path: Path) -> None:
    f = tmp_path / "bad.yaml"
    f.write_text("conf_threshold: 5\niou_threshold: 0.5\n")
    with pytest.raises(ConfigError, match="invalid config"):
        load_config(DemoConfig, f)


def test_load_yaml_requires_a_mapping(tmp_path: Path) -> None:
    f = tmp_path / "list.yaml"
    f.write_text("- a\n- b\n")
    with pytest.raises(ConfigError, match="mapping"):
        load_yaml(f)


def test_load_yaml_empty_file_raises(tmp_path: Path) -> None:
    f = tmp_path / "empty.yaml"
    f.write_text("")

    with pytest.raises(ConfigError, match="mapping"):
        load_yaml(f)
