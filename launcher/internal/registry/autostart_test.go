package registry

import (
	"errors"
	"testing"
)

type memRunStore struct {
	values map[string]string
	getErr error
	setErr error
	delErr error
}

func newMemRunStore() *memRunStore {
	return &memRunStore{values: map[string]string{}}
}

func (m *memRunStore) GetRunValue(name string) (string, error) {
	if m.getErr != nil {
		return "", m.getErr
	}
	val, ok := m.values[name]
	if !ok {
		return "", errValueNotExist
	}
	return val, nil
}

func (m *memRunStore) SetRunValue(name, value string) error {
	if m.setErr != nil {
		return m.setErr
	}
	m.values[name] = value
	return nil
}

func (m *memRunStore) DeleteRunValue(name string) error {
	if m.delErr != nil {
		return m.delErr
	}
	if _, ok := m.values[name]; !ok {
		return errValueNotExist
	}
	delete(m.values, name)
	return nil
}

func TestValueName(t *testing.T) {
	if valueName != "TCGTools" {
		t.Fatalf("unexpected value name %q", valueName)
	}
}

func TestNormalizeExePath(t *testing.T) {
	a := normalizeExePath(`"C:\Program Files\TCG Tools\TCGTools.exe"`)
	b := normalizeExePath(`c:\program files\tcg tools\tcgtools.exe`)
	if a != b {
		t.Fatalf("%q != %q", a, b)
	}
}

func TestSetAutostartEnableDisable(t *testing.T) {
	store := newMemRunStore()
	exe := `C:\Program Files\TCG Tools\TCGTools.exe`

	if err := setAutostart(store, true, exe); err != nil {
		t.Fatal(err)
	}
	if store.values[valueName] != `"`+exe+`"` {
		t.Fatalf("unexpected value %q", store.values[valueName])
	}

	if err := setAutostart(store, false, exe); err != nil {
		t.Fatal(err)
	}
	if _, ok := store.values[valueName]; ok {
		t.Fatal("expected value removed")
	}
}

func TestSetAutostartDisableMissingValue(t *testing.T) {
	store := newMemRunStore()
	if err := setAutostart(store, false, `C:\foo.exe`); err != nil {
		t.Fatal(err)
	}
}

func TestAutostartRoundTrip(t *testing.T) {
	store := newMemRunStore()
	exe := `C:\Program Files\TCG Tools\TCGTools.exe`

	if err := setAutostart(store, true, exe); err != nil {
		t.Fatal(err)
	}
	enabled, err := isAutostartEnabled(store, exe)
	if err != nil {
		t.Fatal(err)
	}
	if !enabled {
		t.Fatal("expected autostart enabled")
	}
	if err := setAutostart(store, false, exe); err != nil {
		t.Fatal(err)
	}
}

func TestToggleAutostart(t *testing.T) {
	store := newMemRunStore()
	exe := `C:\Program Files\TCG Tools\TCGTools.exe`

	next, err := toggleAutostart(store, false, exe)
	if err != nil {
		t.Fatal(err)
	}
	if !next {
		t.Fatal("expected toggle to enable")
	}
	match, err := autostartMatchesExe(store, exe)
	if err != nil {
		t.Fatal(err)
	}
	if !match {
		t.Fatal("expected registry path to match exe")
	}
	_, _ = toggleAutostart(store, true, exe)
	if err := setAutostart(store, false, exe); err != nil {
		t.Fatal(err)
	}
}

func TestIsAutostartEnabledWhenMissing(t *testing.T) {
	store := newMemRunStore()
	exe := `C:\Program Files\TCG Tools\TCGTools.exe`

	enabled, err := isAutostartEnabled(store, exe)
	if err != nil {
		t.Fatal(err)
	}
	if enabled {
		t.Fatal("expected disabled")
	}
	match, err := autostartMatchesExe(store, `c:\program files\tcg tools\tcgtools.exe`)
	if err != nil {
		t.Fatal(err)
	}
	if match {
		t.Fatal("expected no match when disabled")
	}
}

func TestAutostartMatchesExeDifferentPath(t *testing.T) {
	store := newMemRunStore()
	if err := store.SetRunValue(valueName, `"D:\Other\app.exe"`); err != nil {
		t.Fatal(err)
	}
	match, err := autostartMatchesExe(store, `C:\Program Files\TCG Tools\TCGTools.exe`)
	if err != nil {
		t.Fatal(err)
	}
	if match {
		t.Fatal("expected different exe paths not to match")
	}
}

func TestReadAutostartValuePropagatesError(t *testing.T) {
	store := newMemRunStore()
	store.getErr = errors.New("boom")
	if _, err := readAutostartValue(store); err == nil {
		t.Fatal("expected error")
	}
}

func TestSetAutostartPropagatesSetError(t *testing.T) {
	store := newMemRunStore()
	store.setErr = errors.New("boom")
	if err := setAutostart(store, true, `C:\foo.exe`); err == nil {
		t.Fatal("expected error")
	}
}

func TestSetAutostartDeletePropagatesError(t *testing.T) {
	store := newMemRunStore()
	store.values[valueName] = `"C:\foo.exe"`
	store.delErr = errors.New("boom")
	if err := setAutostart(store, false, `C:\foo.exe`); err == nil {
		t.Fatal("expected error")
	}
}

func TestPublicAPIUsesDefaultStore(t *testing.T) {
	prev := defaultStore
	defaultStore = newMemRunStore()
	t.Cleanup(func() { defaultStore = prev })

	exe := `C:\Program Files\TCG Tools\TCGTools.exe`
	if err := SetAutostart(true, exe); err != nil {
		t.Fatal(err)
	}
	enabled, err := IsAutostartEnabled(exe)
	if err != nil || !enabled {
		t.Fatalf("enabled=%v err=%v", enabled, err)
	}
	match, err := AutostartMatchesExe(exe)
	if err != nil || !match {
		t.Fatalf("match=%v err=%v", match, err)
	}
	next, err := ToggleAutostart(true, exe)
	if err != nil || next {
		t.Fatalf("next=%v err=%v", next, err)
	}
	if err := SetAutostart(false, exe); err != nil {
		t.Fatal(err)
	}
}
