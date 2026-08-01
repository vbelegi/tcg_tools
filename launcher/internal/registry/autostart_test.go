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
	match, err := AutostartMatchesExe(exe)
	if err != nil {
		t.Fatal(err)
	}
	if !match {
		t.Fatal("expected registry path to match exe")
	}
	_, _ = ToggleAutostart(true, exe)
	if err := SetAutostart(false, exe); err != nil {
		t.Fatal(err)
	}
}

func TestNormalizeExePath(t *testing.T) {
	a := normalizeExePath(`"C:\Program Files\TCG Tools\TCGTools.exe"`)
	b := normalizeExePath(`c:\program files\tcg tools\tcgtools.exe`)
	if a != b {
		t.Fatalf("%q != %q", a, b)
	}
}

func TestIsAutostartEnabledWhenMissing(t *testing.T) {
	exe := `C:\Program Files\TCG Tools\TCGTools.exe`
	if err := SetAutostart(false, exe); err != nil {
		t.Skip("registry not available:", err)
	}
	enabled, err := IsAutostartEnabled(exe)
	if err != nil {
		t.Fatal(err)
	}
	if enabled {
		t.Fatal("expected disabled")
	}
	match, err := AutostartMatchesExe(`c:\program files\tcg tools\tcgtools.exe`)
	if err != nil {
		t.Fatal(err)
	}
	if match {
		t.Fatal("expected no match when disabled")
	}
}
