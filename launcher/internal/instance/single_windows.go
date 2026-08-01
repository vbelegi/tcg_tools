//go:build windows

package instance

import (
	"syscall"
	"unsafe"

	"golang.org/x/sys/windows"
)

const mutexName = "Global\\TCGTools_SingleInstance"

type Lock struct {
	handle windows.Handle
}

func TryLock() (*Lock, bool, error) {
	name, err := syscall.UTF16PtrFromString(mutexName)
	if err != nil {
		return nil, false, err
	}
	handle, err := windows.CreateMutex(nil, false, name)
	if err != nil {
		return nil, false, err
	}
	lastErr := windows.GetLastError()
	if lastErr == windows.ERROR_ALREADY_EXISTS {
		windows.CloseHandle(handle)
		return nil, false, nil
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
	user32 := windows.NewLazySystemDLL("user32.dll")
	messageBox := user32.NewProc("MessageBoxW")
	tPtr, _ := syscall.UTF16PtrFromString(title)
	mPtr, _ := syscall.UTF16PtrFromString(message)
	_, _, _ = messageBox.Call(0, uintptr(unsafe.Pointer(mPtr)), uintptr(unsafe.Pointer(tPtr)), 0x00000040)
}
