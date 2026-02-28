from __future__ import annotations

from pathlib import Path


APP_DIR_NAME = ".shellsensei"
DB_FILE_NAME = "shellsensei.db"


def default_app_dir() -> Path:
    return Path.home() / APP_DIR_NAME


def default_db_path() -> Path:
    return default_app_dir() / DB_FILE_NAME
