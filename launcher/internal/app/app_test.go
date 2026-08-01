package app

import (
	"testing"

	"github.com/vbelegi/tcg_tools/launcher/internal/config"
	"github.com/vbelegi/tcg_tools/launcher/internal/tray"
)

func TestApplicationAutostartState(t *testing.T) {
	app := New(config.Config{Port: 9000, StartWithWindows: true})
	if !app.autostart {
		t.Fatal("expected autostart enabled")
	}
	if got := tray.AutostartMenuTitle(app.autostart); got != "Desativar inicio com Windows" {
		t.Fatalf("got %q", got)
	}
	app.autostart = false
	if got := tray.AutostartMenuTitle(app.autostart); got != "Ativar inicio com Windows" {
		t.Fatalf("got %q", got)
	}
}

func TestTrayIconFallback(t *testing.T) {
	if len(embeddedIcon) == 0 {
		if trayIcon() != nil {
			t.Fatal("expected nil icon when embed empty")
		}
		return
	}
	if len(trayIcon()) == 0 {
		t.Fatal("expected embedded icon bytes")
	}
}
