"""Caminhos ancorados na raiz do projeto."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
EXPORTS_DIR = PROJECT_ROOT / "exports"
SETTINGS_FILE = CONFIG_DIR / "settings.json"
