package app

import (
	"testing"

	"github.com/vbelegi/tcg_tools/launcher/internal/config"
)

func TestNewApplication(t *testing.T) {
	a := New(config.Config{Port: 7000, StartWithWindows: true})
	if a.cfg.Port != 7000 || !a.autostart {
		t.Fatalf("unexpected app: %+v", a)
	}
	if a.installDir == "" {
		t.Fatal("install dir empty")
	}
}

func TestExePathNonEmpty(t *testing.T) {
	if exePath() == "" {
		t.Fatal("exe path empty")
	}
}
