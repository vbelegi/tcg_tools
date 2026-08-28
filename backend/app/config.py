"""Application settings via pydantic-settings."""

from __future__ import annotations

import shutil
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from app import paths


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TCGTOOLS_", env_file=".env", extra="ignore")

    data_dir: Path = paths.default_data_dir()
    database_url: str | None = None
    presets_file: Path | None = None
    exports_dir: Path | None = None
    logs_dir: Path | None = None
    frontend_dist: Path | None = None
    public_base_url: str | None = None
    cookie_secure: bool | None = None

    @property
    def resolved_cookie_secure(self) -> bool:
        if self.cookie_secure is not None:
            return self.cookie_secure
        base = (self.public_base_url or "").strip()
        return base.lower().startswith("https://")

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        db_file = self.data_dir / "tcg_tools.db"
        return f"sqlite:///{db_file.resolve().as_posix()}"

    @property
    def resolved_presets_file(self) -> Path:
        if self.presets_file:
            return self.presets_file
        return self.data_dir / "premiacao_presets.json"

    @property
    def resolved_exports_dir(self) -> Path:
        if self.exports_dir:
            return self.exports_dir
        return self.data_dir / "exports"

    @property
    def resolved_logs_dir(self) -> Path:
        if self.logs_dir:
            return self.logs_dir
        return self.data_dir / "logs"

    @property
    def resolved_frontend_dist(self) -> Path:
        if self.frontend_dist:
            return self.frontend_dist
        return paths.default_frontend_dist()

    @property
    def resolved_media_dir(self) -> Path:
        return self.data_dir / "media"

    @property
    def resolved_avatars_dir(self) -> Path:
        return self.resolved_media_dir / "avatars"

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.resolved_exports_dir.mkdir(parents=True, exist_ok=True)
        self.resolved_logs_dir.mkdir(parents=True, exist_ok=True)
        self.resolved_avatars_dir.mkdir(parents=True, exist_ok=True)
        presets = self.resolved_presets_file
        if not presets.exists():
            bundled = paths.bundled_presets_file()
            if bundled.is_file():
                shutil.copy2(bundled, presets)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_dirs()
    return settings
