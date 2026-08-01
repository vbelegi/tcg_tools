//go:build windows

package registry

import (
	"fmt"
	"strings"

	"golang.org/x/sys/windows/registry"
)

const runKeyPath = `Software\Microsoft\Windows\CurrentVersion\Run`
const valueName = "TCGTools"

func normalizeExePath(path string) string {
	path = strings.TrimSpace(path)
	path = strings.Trim(path, `"`)
	return strings.ToLower(path)
}

func SetAutostart(enabled bool, exePath string) error {
	k, err := registry.OpenKey(registry.CURRENT_USER, runKeyPath, registry.SET_VALUE)
	if err != nil {
		return err
	}
	defer k.Close()

	if enabled {
		return k.SetStringValue(valueName, fmt.Sprintf(`"%s"`, exePath))
	}
	err = k.DeleteValue(valueName)
	if err == registry.ErrNotExist {
		return nil
	}
	return err
}

func readAutostartValue() (string, error) {
	k, err := registry.OpenKey(registry.CURRENT_USER, runKeyPath, registry.QUERY_VALUE)
	if err != nil {
		return "", err
	}
	defer k.Close()

	val, _, err := k.GetStringValue(valueName)
	if err == registry.ErrNotExist {
		return "", nil
	}
	if err != nil {
		return "", err
	}
	return val, nil
}

func IsAutostartEnabled(exePath string) (bool, error) {
	val, err := readAutostartValue()
	if err != nil {
		return false, err
	}
	return val != "", nil
}

func AutostartMatchesExe(exePath string) (bool, error) {
	val, err := readAutostartValue()
	if err != nil {
		return false, err
	}
	if val == "" {
		return false, nil
	}
	return normalizeExePath(val) == normalizeExePath(exePath), nil
}

func ToggleAutostart(current bool, exePath string) (bool, error) {
	next := !current
	if err := SetAutostart(next, exePath); err != nil {
		return current, err
	}
	return next, nil
}
