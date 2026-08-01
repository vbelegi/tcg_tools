//go:build !windows

package registry

import "errors"

var errUnsupported = errors.New("autostart: windows only")

func SetAutostart(enabled bool, exePath string) error {
	return errUnsupported
}

func IsAutostartEnabled(exePath string) (bool, error) {
	return false, errUnsupported
}

func ToggleAutostart(current bool, exePath string) (bool, error) {
	return current, errUnsupported
}
