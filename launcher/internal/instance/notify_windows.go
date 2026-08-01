//go:build windows

package instance

import (
	"syscall"
	"unsafe"

	"golang.org/x/sys/windows"
)

const (
	mbIconError       = 0x00000010
	mbIconInformation = 0x00000040
)

func notifyBox(title, message string, icon uintptr) {
	user32 := windows.NewLazySystemDLL("user32.dll")
	messageBox := user32.NewProc("MessageBoxW")
	tPtr, _ := syscall.UTF16PtrFromString(title)
	mPtr, _ := syscall.UTF16PtrFromString(message)
	_, _, _ = messageBox.Call(0, uintptr(unsafe.Pointer(mPtr)), uintptr(unsafe.Pointer(tPtr)), icon)
}

func NotifyError(title, message string) {
	notifyBox(title, message, mbIconError)
}
