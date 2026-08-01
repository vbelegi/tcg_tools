//go:build !windows

package process

import "os/exec"

func assignToJobObject(cmd *exec.Cmd) error {
	return nil
}

func assignProcessToJob(cmd *exec.Cmd) error {
	return nil
}
