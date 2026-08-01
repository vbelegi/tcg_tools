//go:build windows

package process

import (
	"fmt"
	"os/exec"
	"sync"
	"unsafe"

	"golang.org/x/sys/windows"
)

var (
	jobOnce    sync.Once
	jobHandle  windows.Handle
	jobInitErr error
)

func ensureJobObject() error {
	jobOnce.Do(func() {
		handle, err := windows.CreateJobObject(nil, nil)
		if err != nil {
			jobInitErr = fmt.Errorf("CreateJobObject: %w", err)
			return
		}

		info := windows.JOBOBJECT_EXTENDED_LIMIT_INFORMATION{}
		info.BasicLimitInformation.LimitFlags = windows.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
		if _, err := windows.SetInformationJobObject(
			handle,
			windows.JobObjectExtendedLimitInformation,
			uintptr(unsafe.Pointer(&info)),
			uint32(unsafe.Sizeof(info)),
		); err != nil {
			windows.CloseHandle(handle)
			jobInitErr = fmt.Errorf("SetInformationJobObject: %w", err)
			return
		}
		jobHandle = handle
	})
	return jobInitErr
}

func assignToJobObject(cmd *exec.Cmd) error {
	return ensureJobObject()
}

func assignProcessToJob(cmd *exec.Cmd) error {
	if cmd == nil || cmd.Process == nil {
		return fmt.Errorf("processo nao iniciado")
	}
	if err := ensureJobObject(); err != nil {
		return err
	}

	handle, err := windows.OpenProcess(windows.PROCESS_SET_QUOTA|windows.PROCESS_TERMINATE, false, uint32(cmd.Process.Pid))
	if err != nil {
		return fmt.Errorf("OpenProcess: %w", err)
	}
	defer windows.CloseHandle(handle)

	if err := windows.AssignProcessToJobObject(jobHandle, handle); err != nil {
		return fmt.Errorf("AssignProcessToJobObject: %w", err)
	}
	return nil
}
