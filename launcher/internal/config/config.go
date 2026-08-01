package config

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
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
}

func DefaultConfig() Config {
	return Config{Port: DefaultPort, StartWithWindows: false}
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
		return cfg, err
	}
	if err := cfg.Validate(); err != nil {
		return DefaultConfig(), err
	}
	return cfg, nil
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
	return os.WriteFile(ConfigPath(), data, 0o644)
}

func ReadVersion(installDir string) string {
	data, err := os.ReadFile(VersionPath(installDir))
	if err != nil {
		return "desconhecida"
	}
	return string(data)
}

func AppendLog(message string) {
	f, err := os.OpenFile(LogPath(), os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0o644)
	if err != nil {
		return
	}
	defer f.Close()
	fmt.Fprintf(f, "%s\n", message)
}
