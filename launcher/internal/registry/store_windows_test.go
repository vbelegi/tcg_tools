//go:build windows

package registry

import (
	"errors"
	"testing"

	winreg "golang.org/x/sys/windows/registry"
)

type fakeRunKey struct {
	values map[string]string
	getErr error
	setErr error
	delErr error
	closed bool
}

func (f *fakeRunKey) GetStringValue(name string) (string, uint32, error) {
	if f.getErr != nil {
		return "", 0, f.getErr
	}
	val, ok := f.values[name]
	if !ok {
		return "", 0, winreg.ErrNotExist
	}
	return val, 0, nil
}

func (f *fakeRunKey) SetStringValue(name, value string) error {
	if f.setErr != nil {
		return f.setErr
	}
	f.values[name] = value
	return nil
}

func (f *fakeRunKey) DeleteValue(name string) error {
	if f.delErr != nil {
		return f.delErr
	}
	if _, ok := f.values[name]; !ok {
		return winreg.ErrNotExist
	}
	delete(f.values, name)
	return nil
}

func (f *fakeRunKey) Close() error {
	f.closed = true
	return nil
}

func withFakeRunKey(t *testing.T, key *fakeRunKey, fn func(store windowsRunStore)) {
	t.Helper()
	prev := openRunKey
	openRunKey = func(uint32) (runKey, error) { return key, nil }
	t.Cleanup(func() { openRunKey = prev })
	fn(windowsRunStore{})
}

func TestWindowsRunStoreGetSetDelete(t *testing.T) {
	key := &fakeRunKey{values: map[string]string{}}
	withFakeRunKey(t, key, func(store windowsRunStore) {
		if _, err := store.GetRunValue("TCGTools"); !errors.Is(err, errValueNotExist) {
			t.Fatalf("expected missing value, got %v", err)
		}
		if err := store.SetRunValue("TCGTools", `"C:\foo.exe"`); err != nil {
			t.Fatal(err)
		}
		val, err := store.GetRunValue("TCGTools")
		if err != nil {
			t.Fatal(err)
		}
		if val != `"C:\foo.exe"` {
			t.Fatalf("unexpected value %q", val)
		}
		if err := store.DeleteRunValue("TCGTools"); err != nil {
			t.Fatal(err)
		}
		if !key.closed {
			t.Fatal("expected key closed")
		}
	})
}

func TestWindowsRunStoreDeleteMissing(t *testing.T) {
	key := &fakeRunKey{values: map[string]string{}}
	withFakeRunKey(t, key, func(store windowsRunStore) {
		if err := store.DeleteRunValue("TCGTools"); !errors.Is(err, errValueNotExist) {
			t.Fatalf("expected errValueNotExist, got %v", err)
		}
	})
}

func TestWindowsRunStoreOpenKeyError(t *testing.T) {
	prev := openRunKey
	openRunKey = func(uint32) (runKey, error) { return nil, errors.New("denied") }
	t.Cleanup(func() { openRunKey = prev })

	store := windowsRunStore{}
	if _, err := store.GetRunValue("TCGTools"); err == nil {
		t.Fatal("expected open error")
	}
	if err := store.SetRunValue("TCGTools", "x"); err == nil {
		t.Fatal("expected open error")
	}
	if err := store.DeleteRunValue("TCGTools"); err == nil {
		t.Fatal("expected open error")
	}
}

func TestWindowsRunStoreGetPropagatesError(t *testing.T) {
	key := &fakeRunKey{getErr: errors.New("boom")}
	withFakeRunKey(t, key, func(store windowsRunStore) {
		if _, err := store.GetRunValue("TCGTools"); err == nil {
			t.Fatal("expected error")
		}
	})
}

func TestWindowsRunStoreSetPropagatesError(t *testing.T) {
	key := &fakeRunKey{values: map[string]string{}, setErr: errors.New("boom")}
	withFakeRunKey(t, key, func(store windowsRunStore) {
		if err := store.SetRunValue("TCGTools", "x"); err == nil {
			t.Fatal("expected error")
		}
	})
}

func TestWindowsRunStoreDeletePropagatesError(t *testing.T) {
	key := &fakeRunKey{values: map[string]string{"TCGTools": "x"}, delErr: errors.New("boom")}
	withFakeRunKey(t, key, func(store windowsRunStore) {
		if err := store.DeleteRunValue("TCGTools"); err == nil {
			t.Fatal("expected error")
		}
	})
}
