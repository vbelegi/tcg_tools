package instance

import "testing"

func TestMutexNameIsPerUserSession(t *testing.T) {
	if MutexName != `Local\TCGTools_SingleInstance` {
		t.Fatalf("unexpected mutex name: %q", MutexName)
	}
}
