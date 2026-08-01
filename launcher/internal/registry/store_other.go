//go:build !windows

package registry

import "errors"

var errUnsupported = errors.New("autostart: windows only")

type unsupportedRunStore struct{}

func (unsupportedRunStore) GetRunValue(string) (string, error) {
	return "", errUnsupported
}

func (unsupportedRunStore) SetRunValue(string, string) error {
	return errUnsupported
}

func (unsupportedRunStore) DeleteRunValue(string) error {
	return errUnsupported
}

func init() {
	defaultStore = unsupportedRunStore{}
}
