//go:build windows

package registry

import "testing"

func TestValueName(t *testing.T) {
	if valueName != "TCGTools" {
		t.Fatalf("unexpected value name %q", valueName)
	}
}

// Integration: SetAutostart/IsAutostartEnabled require Windows registry.
// CI runs on windows-latest; skip if OpenKey fails (non-Windows dev).
func TestAutostartRoundTrip(t *testing.T) {
	exe := `C:\Program Files\TCG Tools\TCGTools.exe`
	if err := SetAutostart(false, exe); err != nil {
		t.Skip("registry not available:", err)
	}
	if err := SetAutostart(true, exe); err != nil {
		t.Fatal(err)
	}
	enabled, err := IsAutostartEnabled(exe)
	if err != nil {
		t.Fatal(err)
	}
	if !enabled {
		t.Fatal("expected autostart enabled")
	}
	if err := SetAutostart(false, exe); err != nil {
		t.Fatal(err)
	}
}

func TestToggleAutostart(t *testing.T) {
	exe := `C:\Program Files\TCG Tools\TCGTools.exe`
	if err := SetAutostart(false, exe); err != nil {
		t.Skip("registry not available:", err)
	}
	next, err := ToggleAutostart(false, exe)
	if err != nil {
		t.Skip("registry not available:", err)
	}
	if !next {
		t.Fatal("expected toggle to enable")
	}
	_, _ = ToggleAutostart(true, exe)
	if err := SetAutostart(false, exe); err != nil {
		t.Fatal(err)
	}
}
