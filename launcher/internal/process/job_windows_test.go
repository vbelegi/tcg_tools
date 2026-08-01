//go:build windows

package process

import (
	"os/exec"
	"testing"
)

func TestJobObjectAssignProcess(t *testing.T) {
	cmd := exec.Command("cmd", "/c", "exit", "0")
	if err := assignToJobObject(cmd); err != nil {
		t.Fatal(err)
	}
	if err := cmd.Start(); err != nil {
		t.Fatal(err)
	}
	if err := assignProcessToJob(cmd); err != nil {
		t.Fatalf("assignProcessToJob: %v", err)
	}
	_, _ = cmd.Process.Wait()
}
