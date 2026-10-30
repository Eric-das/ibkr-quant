"""读取 .env（连接参数）和 config/settings.yaml（项目设置）。"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class IBConn:
    host: str = os.getenv("IB_HOST", "127.0.0.1")
    port: int = int(os.getenv("IB_PORT", "7497"))
    client_id: int = int(os.getenv("IB_CLIENT_ID", "1"))


def load_settings() -> dict:
    base = yaml.safe_load((PROJECT_ROOT / "config" / "settings.yaml").read_text()) or {}
    local = PROJECT_ROOT / "config" / "settings.local.yaml"
    if local.exists():
        base.update(yaml.safe_load(local.read_text()) or {})
    return base


SETTINGS = load_settings()
DATA_DIR = PROJECT_ROOT / SETTINGS.get("data_dir", "data")
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
