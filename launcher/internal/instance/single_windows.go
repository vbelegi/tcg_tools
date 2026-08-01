//go:build windows

package instance

import (
	"syscall"

	"golang.org/x/sys/windows"
)

type Lock struct {
	handle windows.Handle
}

func TryLock() (*Lock, bool, error) {
	name, err := syscall.UTF16PtrFromString(MutexName)
	if err != nil {
		return nil, false, err
	}
	handle, err := windows.CreateMutex(nil, true, name)
	if handle == 0 {
		return nil, false, err
	}
	lastErr := windows.GetLastError()
	if lastErr == windows.ERROR_ALREADY_EXISTS {
		windows.CloseHandle(handle)
		return nil, false, nil
	}
	if err != nil {
		windows.CloseHandle(handle)
		return nil, false, err
	}
	return &Lock{handle: handle}, true, nil
}

func (l *Lock) Release() {
	if l != nil && l.handle != 0 {
		windows.CloseHandle(l.handle)
		l.handle = 0
	}
}

func NotifyAlreadyRunning(title, message string) {
	notifyBox(title, message, mbIconInformation)
}
