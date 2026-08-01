//go:build !windows

package instance

type Lock struct{}

func TryLock() (*Lock, bool, error) {
	return &Lock{}, true, nil
}

func (l *Lock) Release() {}

func NotifyAlreadyRunning(title, message string) {}
