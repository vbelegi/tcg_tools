package app

import (
	"context"
	_ "embed"
	"fmt"
	"os"
	"os/exec"
	"runtime"

	"github.com/vbelegi/tcg_tools/launcher/internal/browser"
	"github.com/vbelegi/tcg_tools/launcher/internal/config"
	"github.com/vbelegi/tcg_tools/launcher/internal/instance"
	"github.com/vbelegi/tcg_tools/launcher/internal/process"
	"github.com/vbelegi/tcg_tools/launcher/internal/registry"
	"github.com/vbelegi/tcg_tools/launcher/internal/tray"
)

//go:embed assets/icon.ico
var embeddedIcon []byte

type Application struct {
	cfg        config.Config
	installDir string
	server     *process.Server
	autostart  bool
}

func New(cfg config.Config) *Application {
	return &Application{
		cfg:        cfg,
		installDir: config.InstallDir(),
		autostart:  cfg.StartWithWindows,
	}
}

func (a *Application) Run(ctx context.Context) error {
	if runtime.GOOS == "windows" {
		lock, ok, err := instance.TryLock()
		if err != nil {
			return err
		}
		if !ok {
			_ = browser.Open(a.cfg.BaseURL())
			instance.NotifyAlreadyRunning("TCG Tools", instance.FormatRunningMessage(a.cfg.Port))
			return nil
		}
		defer lock.Release()
	}

	a.server = process.New(a.installDir, a.cfg.Port, config.DataDir())
	if err := a.server.Start(ctx); err != nil {
		config.AppendLog(fmt.Sprintf("erro ao iniciar servidor: %v", err))
		if runtime.GOOS == "windows" {
			instance.NotifyError("TCG Tools", fmt.Sprintf("Nao foi possivel iniciar o servidor:\n\n%v", err))
		}
		return err
	}
	defer a.server.Stop()

	if err := a.syncAutostart(exePath()); err != nil {
		config.AppendLog(fmt.Sprintf("aviso autostart: %v", err))
	}

	_ = browser.Open(a.cfg.BaseURL())

	tray.Run(trayIcon(), "TCG Tools", tray.Actions{
		OnOpen: func() { _ = browser.Open(a.cfg.BaseURL()) },
		OnQuit: func() {
			_ = a.server.Stop()
		},
		OnAbout: func() {
			version := config.ReadVersion(a.installDir)
			instance.NotifyAlreadyRunning("TCG Tools", fmt.Sprintf("Versao %s", version))
		},
		OnDataDir: func() { openFolder(config.DataDir()) },
		OnExports: func() { openFolder(config.ExportsDir()) },
		OnLogs:    func() { openFolder(config.LogsDir()) },
		AutostartEnabled: func() bool {
			return a.autostart
		},
		OnToggleAutostart: func() {
			next, err := registry.ToggleAutostart(a.autostart, exePath())
			if err != nil {
				config.AppendLog(fmt.Sprintf("erro autostart: %v", err))
				if runtime.GOOS == "windows" {
					instance.NotifyError("TCG Tools", fmt.Sprintf("Falha ao alterar autostart:\n\n%v", err))
				}
				return
			}
			a.autostart = next
			a.cfg.StartWithWindows = next
			_ = config.Save(a.cfg)
		},
	})
	return nil
}

func (a *Application) syncAutostart(exe string) error {
	if a.cfg.StartWithWindows {
		if match, _ := registry.AutostartMatchesExe(exe); !match {
			return registry.SetAutostart(true, exe)
		}
		return nil
	}
	enabled, err := registry.IsAutostartEnabled(exe)
	if err != nil {
		return err
	}
	if enabled {
		return registry.SetAutostart(false, exe)
	}
	return nil
}

func exePath() string {
	p, err := os.Executable()
	if err != nil {
		return config.InstallDir()
	}
	return p
}

func openFolder(path string) {
	_ = os.MkdirAll(path, 0o755)
	if runtime.GOOS == "windows" {
		_ = exec.Command("explorer", path).Start()
	}
}

func trayIcon() []byte {
	if len(embeddedIcon) > 0 {
		return embeddedIcon
	}
	return nil
}
