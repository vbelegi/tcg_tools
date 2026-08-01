package config

import (
	"os"
	"path/filepath"
	"testing"
)

func TestDataDirFallbackWithoutAppData(t *testing.T) {
	t.Setenv("APPDATA", "")
	got := DataDir()
	if got == "" {
		t.Fatal("expected non-empty data dir")
	}
}

func TestPathHelpers(t *testing.T) {
	dir := t.TempDir()
	t.Setenv("APPDATA", dir)
	base := filepath.Join(dir, AppDataFolder)
	if DataDir() != base {
		t.Fatalf("DataDir got %q", DataDir())
	}
	if ExportsDir() != filepath.Join(base, "exports") {
		t.Fatal("ExportsDir")
	}
	if LogsDir() != filepath.Join(base, "logs") {
		t.Fatal("LogsDir")
	}
	if ConfigPath() != filepath.Join(base, ConfigFileName) {
		t.Fatal("ConfigPath")
	}
}

func TestInstallDirFromExecutable(t *testing.T) {
	dir := InstallDir()
	if dir == "" {
		t.Fatal("expected install dir")
	}
	if _, err := os.Stat(dir); err != nil {
		t.Fatalf("install dir missing: %v", err)
	}
}

func TestResetConfigFile(t *testing.T) {
	dir := t.TempDir()
	t.Setenv("APPDATA", dir)
	path := ConfigPath()
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatal(err)
	}
	cfg, err := resetConfigFile(path)
	if err != nil {
		t.Fatal(err)
	}
	if cfg.Port != DefaultPort {
		t.Fatal(cfg)
	}
	if _, err := os.Stat(path); err != nil {
		t.Fatal("config not written")
	}
}

func TestVersionPathJoin(t *testing.T) {
	got := VersionPath(`C:\TCG Tools`)
	if got != `C:\TCG Tools\VERSION.txt` {
		t.Fatal(got)
	}
}

func TestSaveInvalidPort(t *testing.T) {
	if err := Save(Config{Port: 22}); err == nil {
		t.Fatal("expected validation error")
	}
}

func TestLoadReadError(t *testing.T) {
	dir := t.TempDir()
	t.Setenv("APPDATA", dir)
	if err := os.MkdirAll(DataDir(), 0o755); err != nil {
		t.Fatal(err)
	}
	// ConfigPath as directory causes read error.
	if err := os.Mkdir(ConfigPath(), 0o755); err != nil {
		t.Fatal(err)
	}
	_, err := Load()
	if err == nil {
		t.Fatal("expected read error")
	}
}
