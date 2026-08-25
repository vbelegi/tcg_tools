package config

import (
	"os"
	"path/filepath"
	"testing"
)

func TestDefaultConfigValidate(t *testing.T) {
	cfg := DefaultConfig()
	if err := cfg.Validate(); err != nil {
		t.Fatal(err)
	}
	if cfg.BaseURL() != "http://127.0.0.1:8000" {
		t.Fatalf("unexpected base url: %s", cfg.BaseURL())
	}
	if cfg.LanAccess {
		t.Fatal("expected lan_access false by default")
	}
}

func TestBindHost(t *testing.T) {
	if got := (Config{LanAccess: false}).BindHost(); got != "127.0.0.1" {
		t.Fatalf("expected localhost bind, got %q", got)
	}
	if got := (Config{LanAccess: true}).BindHost(); got != "0.0.0.0" {
		t.Fatalf("expected LAN bind, got %q", got)
	}
}

func TestValidateRejectsInvalidPort(t *testing.T) {
	cfg := Config{Port: 80}
	if err := cfg.Validate(); err == nil {
		t.Fatal("expected error for port 80")
	}
	cfg.Port = 70000
	if err := cfg.Validate(); err == nil {
		t.Fatal("expected error for port 70000")
	}
}

func TestLoadSaveRoundTrip(t *testing.T) {
	dir := t.TempDir()
	t.Setenv("APPDATA", dir)

	cfg := Config{Port: 9000, StartWithWindows: true, LanAccess: true}
	if err := Save(cfg); err != nil {
		t.Fatal(err)
	}
	loaded, err := Load()
	if err != nil {
		t.Fatal(err)
	}
	if loaded.Port != 9000 || !loaded.StartWithWindows || !loaded.LanAccess {
		t.Fatalf("unexpected config: %+v", loaded)
	}
	if loaded.BindHost() != "0.0.0.0" {
		t.Fatalf("unexpected bind host: %s", loaded.BindHost())
	}
}

func TestLoadCreatesDefaultWhenMissing(t *testing.T) {
	dir := t.TempDir()
	t.Setenv("APPDATA", dir)

	cfg, err := Load()
	if err != nil {
		t.Fatal(err)
	}
	if cfg.Port != DefaultPort {
		t.Fatalf("expected default port, got %d", cfg.Port)
	}
	if _, err := os.Stat(ConfigPath()); err != nil {
		t.Fatal("expected config file created")
	}
}

func TestDataDirUsesAppData(t *testing.T) {
	t.Setenv("APPDATA", `C:\Users\Test\AppData\Roaming`)
	got := DataDir()
	want := filepath.Join(`C:\Users\Test\AppData\Roaming`, AppDataFolder)
	if got != want {
		t.Fatalf("got %q want %q", got, want)
	}
}

func TestReadVersionMissing(t *testing.T) {
	if got := ReadVersion(t.TempDir()); got != "desconhecida" {
		t.Fatalf("got %q", got)
	}
}

func TestReadVersionFromFile(t *testing.T) {
	dir := t.TempDir()
	if err := os.WriteFile(filepath.Join(dir, "VERSION.txt"), []byte("1.2.3"), 0o644); err != nil {
		t.Fatal(err)
	}
	if got := ReadVersion(dir); got != "1.2.3" {
		t.Fatalf("got %q", got)
	}
}

func TestLoadRecoversFromInvalidJSON(t *testing.T) {
	dir := t.TempDir()
	t.Setenv("APPDATA", dir)

	badPath := ConfigPath()
	if err := os.MkdirAll(filepath.Dir(badPath), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(badPath, []byte("{not-json"), 0o644); err != nil {
		t.Fatal(err)
	}

	cfg, err := Load()
	if err != nil {
		t.Fatal(err)
	}
	if cfg.Port != DefaultPort {
		t.Fatalf("expected default port, got %d", cfg.Port)
	}
	if _, err := os.Stat(badPath + ".bak"); err != nil {
		t.Fatal("expected backup of corrupt config")
	}
}

func TestAppendLogIncludesTimestamp(t *testing.T) {
	dir := t.TempDir()
	t.Setenv("APPDATA", dir)
	AppendLog("teste")
	data, err := os.ReadFile(LogPath())
	if err != nil {
		t.Fatal(err)
	}
	line := string(data)
	if len(line) < 20 || line[len(line)-1] != '\n' {
		t.Fatalf("unexpected log line: %q", line)
	}
}
