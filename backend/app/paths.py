"""Path resolution for TCG Tools."""

from __future__ import annotations

from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_REPO_ROOT = _BACKEND_ROOT.parent


def backend_root() -> Path:
    return _BACKEND_ROOT


def repo_root() -> Path:
    return _REPO_ROOT


def default_data_dir() -> Path:
    return Path("./data")


def bundled_presets_file() -> Path:
    """Shipped defaults (read-only in Program Files installs)."""
    return backend_root() / "config" / "premiacao_presets.json"


def default_presets_file() -> Path:
    return default_data_dir() / "premiacao_presets.json"


def default_exports_dir() -> Path:
    return default_data_dir() / "exports"


def default_logs_dir() -> Path:
    return default_data_dir() / "logs"


def default_frontend_dist() -> Path:
    return repo_root() / "frontend" / "dist"


def legacy_settings_file() -> Path:
    return repo_root() / "config" / "settings.json"
