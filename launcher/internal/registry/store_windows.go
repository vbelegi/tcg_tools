//go:build windows

package registry

import (
	"errors"

	winreg "golang.org/x/sys/windows/registry"
)

const runKeyPath = `Software\Microsoft\Windows\CurrentVersion\Run`

type runKey interface {
	GetStringValue(name string) (string, uint32, error)
	SetStringValue(name, value string) error
	DeleteValue(name string) error
	Close() error
}

type realRunKey struct {
	key winreg.Key
}

func (k *realRunKey) GetStringValue(name string) (string, uint32, error) {
	return k.key.GetStringValue(name)
}

func (k *realRunKey) SetStringValue(name, value string) error {
	return k.key.SetStringValue(name, value)
}

func (k *realRunKey) DeleteValue(name string) error {
	return k.key.DeleteValue(name)
}

func (k *realRunKey) Close() error {
	return k.key.Close()
}

var openRunKey = func(access uint32) (runKey, error) {
	k, err := winreg.OpenKey(winreg.CURRENT_USER, runKeyPath, access)
	if err != nil {
		return nil, err
	}
	return &realRunKey{key: k}, nil
}

type windowsRunStore struct{}

func (windowsRunStore) GetRunValue(name string) (string, error) {
	k, err := openRunKey(winreg.QUERY_VALUE)
	if err != nil {
		return "", err
	}
	defer k.Close()

	val, _, err := k.GetStringValue(name)
	if errors.Is(err, winreg.ErrNotExist) {
		return "", errValueNotExist
	}
	return val, err
}

func (windowsRunStore) SetRunValue(name, value string) error {
	k, err := openRunKey(winreg.SET_VALUE)
	if err != nil {
		return err
	}
	defer k.Close()
	return k.SetStringValue(name, value)
}

func (windowsRunStore) DeleteRunValue(name string) error {
	k, err := openRunKey(winreg.SET_VALUE)
	if err != nil {
		return err
	}
	defer k.Close()

	err = k.DeleteValue(name)
	if errors.Is(err, winreg.ErrNotExist) {
		return errValueNotExist
	}
	return err
}

func init() {
	defaultStore = windowsRunStore{}
}
