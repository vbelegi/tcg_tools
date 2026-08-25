package config

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"time"
)

const (
	ConfigFileName = "launcher_config.json"
	DefaultPort    = 8000
	MinPort        = 1024
	MaxPort        = 65535
	AppDataFolder  = "TCGTools"
)

type Config struct {
	Port             int  `json:"port"`
	StartWithWindows bool `json:"start_with_windows"`
	LanAccess        bool `json:"lan_access"`
}

func DefaultConfig() Config {
	return Config{Port: DefaultPort, StartWithWindows: false, LanAccess: false}
}

func DataDir() string {
	appData := os.Getenv("APPDATA")
	if appData == "" {
		home, err := os.UserHomeDir()
		if err != nil {
			return AppDataFolder
		}
		return filepath.Join(home, AppDataFolder)
	}
	return filepath.Join(appData, AppDataFolder)
}

func ConfigPath() string {
	return filepath.Join(DataDir(), ConfigFileName)
}

func InstallDir() string {
	exe, err := os.Executable()
	if err != nil {
		return "."
	}
	return filepath.Dir(exe)
}

func VersionPath(installDir string) string {
	return filepath.Join(installDir, "VERSION.txt")
}

func LogPath() string {
	return filepath.Join(DataDir(), "launcher.log")
}

func ExportsDir() string {
	return filepath.Join(DataDir(), "exports")
}

func LogsDir() string {
	return filepath.Join(DataDir(), "logs")
}

func (c Config) BaseURL() string {
	return fmt.Sprintf("http://127.0.0.1:%d", c.Port)
}

func (c Config) BindHost() string {
	if c.LanAccess {
		return "0.0.0.0"
	}
	return "127.0.0.1"
}

func (c Config) Validate() error {
	if c.Port < MinPort || c.Port > MaxPort {
		return fmt.Errorf("porta invalida: %d (use %d-%d)", c.Port, MinPort, MaxPort)
	}
	return nil
}

func Load() (Config, error) {
	cfg := DefaultConfig()
	path := ConfigPath()
	data, err := os.ReadFile(path)
	if err != nil {
		if errors.Is(err, os.ErrNotExist) {
			if mkErr := os.MkdirAll(DataDir(), 0o755); mkErr != nil {
				return cfg, mkErr
			}
			return cfg, Save(cfg)
		}
		return cfg, err
	}
	if err := json.Unmarshal(data, &cfg); err != nil {
		backupCorruptConfig(path, data)
		AppendLog(fmt.Sprintf("config invalido restaurado para padrao: %v", err))
		return resetConfigFile(path)
	}
	if err := cfg.Validate(); err != nil {
		backupCorruptConfig(path, data)
		AppendLog(fmt.Sprintf("config invalido restaurado para padrao: %v", err))
		return resetConfigFile(path)
	}
	return cfg, nil
}

func resetConfigFile(path string) (Config, error) {
	cfg := DefaultConfig()
	if err := os.MkdirAll(DataDir(), 0o755); err != nil {
		return cfg, err
	}
	if err := Save(cfg); err != nil {
		return cfg, err
	}
	_ = path
	return cfg, nil
}

func backupCorruptConfig(path string, data []byte) {
	backup := path + ".bak"
	_ = os.WriteFile(backup, data, 0o644)
}

func Save(cfg Config) error {
	if err := cfg.Validate(); err != nil {
		return err
	}
	if err := os.MkdirAll(DataDir(), 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(cfg, "", "  ")
	if err != nil {
		return err
	}
	tmp := ConfigPath() + ".tmp"
	if err := os.WriteFile(tmp, data, 0o644); err != nil {
		return err
	}
	return os.Rename(tmp, ConfigPath())
}

func ReadVersion(installDir string) string {
	data, err := os.ReadFile(VersionPath(installDir))
	if err != nil {
		return "desconhecida"
	}
	return string(data)
}

func AppendLog(message string) {
	if err := os.MkdirAll(DataDir(), 0o755); err != nil {
		return
	}
	f, err := os.OpenFile(LogPath(), os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0o644)
	if err != nil {
		return
	}
	defer f.Close()
	ts := time.Now().Format("2006-01-02 15:04:05")
	fmt.Fprintf(f, "%s %s\n", ts, message)
}
