"""Config: paths and environment loading for the CLT inventory pipeline."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = REPO_ROOT / ".env"
DATA_DIR = REPO_ROOT / "data"
HTML_DIR = DATA_DIR / "html"
SITE_CLTS_JSON = REPO_ROOT / "src" / "data" / "clts.json"

REQUIRED_ENV = ("DATABASE_URL", "SERPAPI_KEY")

USER_AGENT = (
    "MontavillaCLT-Inventory/1.0 "
    "(research; tfalcon@sfwconstruction.com)"
)
HTTP_TIMEOUT = 20  # seconds, connect/read
PER_DOMAIN_DELAY = 1.5  # seconds between requests to the same host
MAX_CONTACT_LINKS = 8


def load_env() -> dict[str, str]:
    """Read .env and the process environment; return required vars or raise."""
    file_env = dotenv_values(ENV_PATH) if ENV_PATH.exists() else {}
    merged = {**file_env, **{k: os.environ[k] for k in os.environ if k in REQUIRED_ENV}}
    missing = [k for k in REQUIRED_ENV if not merged.get(k)]
    if missing:
        raise RuntimeError(f"Missing required env vars: {', '.join(missing)}")
    return {k: merged[k] for k in REQUIRED_ENV}
