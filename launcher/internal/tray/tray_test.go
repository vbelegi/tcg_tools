package tray

import "testing"

func TestQuitNoPanic(t *testing.T) {
	// Quit before Run is safe (no-op if systray not started).
	Quit()
}
