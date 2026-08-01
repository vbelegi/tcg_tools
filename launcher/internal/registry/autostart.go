package registry

import (
	"errors"
	"fmt"
	"strings"
)

const valueName = "TCGTools"

var errValueNotExist = errors.New("registry: value not found")

// RunStore abstracts HKCU Run key access for unit tests and platform backends.
type RunStore interface {
	GetRunValue(name string) (string, error)
	SetRunValue(name, value string) error
	DeleteRunValue(name string) error
}

var defaultStore RunStore

func normalizeExePath(path string) string {
	path = strings.TrimSpace(path)
	path = strings.Trim(path, `"`)
	return strings.ToLower(path)
}

func readAutostartValue(store RunStore) (string, error) {
	val, err := store.GetRunValue(valueName)
	if errors.Is(err, errValueNotExist) {
		return "", nil
	}
	return val, err
}

func setAutostart(store RunStore, enabled bool, exePath string) error {
	if enabled {
		return store.SetRunValue(valueName, fmt.Sprintf(`"%s"`, exePath))
	}
	err := store.DeleteRunValue(valueName)
	if errors.Is(err, errValueNotExist) {
		return nil
	}
	return err
}

func isAutostartEnabled(store RunStore, _ string) (bool, error) {
	val, err := readAutostartValue(store)
	if err != nil {
		return false, err
	}
	return val != "", nil
}

func autostartMatchesExe(store RunStore, exePath string) (bool, error) {
	val, err := readAutostartValue(store)
	if err != nil {
		return false, err
	}
	if val == "" {
		return false, nil
	}
	return normalizeExePath(val) == normalizeExePath(exePath), nil
}

func toggleAutostart(store RunStore, current bool, exePath string) (bool, error) {
	next := !current
	if err := setAutostart(store, next, exePath); err != nil {
		return current, err
	}
	return next, nil
}

func SetAutostart(enabled bool, exePath string) error {
	return setAutostart(defaultStore, enabled, exePath)
}

func IsAutostartEnabled(exePath string) (bool, error) {
	return isAutostartEnabled(defaultStore, exePath)
}

func AutostartMatchesExe(exePath string) (bool, error) {
	return autostartMatchesExe(defaultStore, exePath)
}

func ToggleAutostart(current bool, exePath string) (bool, error) {
	return toggleAutostart(defaultStore, current, exePath)
}
