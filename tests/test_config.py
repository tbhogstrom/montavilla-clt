"""Tests for pipeline.config."""
from pathlib import Path
from unittest import mock

from pipeline import config


def test_paths_are_absolute_and_under_repo_root():
    assert config.REPO_ROOT.is_absolute()
    assert config.DATA_DIR == config.REPO_ROOT / "data"
    assert config.HTML_DIR == config.REPO_ROOT / "data" / "html"
    assert config.SITE_CLTS_JSON == config.REPO_ROOT / "src" / "data" / "clts.json"


def test_load_env_returns_required_vars(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("DATABASE_URL=postgres://x\nSERPAPI_KEY=abc123\n")
    monkeypatch.setattr(config, "ENV_PATH", env_file)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SERPAPI_KEY", raising=False)

    env = config.load_env()
    assert env["DATABASE_URL"] == "postgres://x"
    assert env["SERPAPI_KEY"] == "abc123"


def test_load_env_raises_when_required_missing(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("DATABASE_URL=postgres://x\n")  # SERPAPI_KEY missing
    monkeypatch.setattr(config, "ENV_PATH", env_file)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SERPAPI_KEY", raising=False)

    try:
        config.load_env()
    except RuntimeError as exc:
        assert "SERPAPI_KEY" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")


def test_load_env_process_env_wins_over_file(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("DATABASE_URL=from-file\nSERPAPI_KEY=abc123\n")
    monkeypatch.setattr(config, "ENV_PATH", env_file)
    monkeypatch.setenv("DATABASE_URL", "from-process-env")
    monkeypatch.delenv("SERPAPI_KEY", raising=False)

    env = config.load_env()
    assert env["DATABASE_URL"] == "from-process-env", "process env must win over .env file"
    assert env["SERPAPI_KEY"] == "abc123"
