//go:build windows

package instance

import "testing"

func TestTryLockExclusive(t *testing.T) {
	lock, ok, err := TryLock()
	if err != nil {
		t.Skip("mutex unavailable:", err)
	}
	if !ok {
		t.Skip("TCG Tools already running in this session")
	}
	_, ok2, _ := TryLock()
	if ok2 {
		t.Fatal("expected second lock denied")
	}
	lock.Release()
	lock2, ok3, err := TryLock()
	if err != nil {
		t.Fatal(err)
	}
	if !ok3 {
		t.Fatal("expected lock after release")
	}
	lock2.Release()
}
