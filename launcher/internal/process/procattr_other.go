//go:build !windows

package process

import "os/exec"

func applyWindowsNoWindow(cmd *exec.Cmd) {}
