package process

import (
	"context"
	"testing"
)

func TestServerStopNoProcess(t *testing.T) {
	s := New("C:\\missing", 8000, t.TempDir())
	if err := s.Stop(); err != nil {
		t.Fatal(err)
	}
}

func TestServerStartMissingPython(t *testing.T) {
	dir := t.TempDir()
	s := New(dir, 18000, t.TempDir())
	ctx := context.Background()
	err := s.Start(ctx)
	if err == nil {
		t.Fatal("expected error for missing python")
		s.Stop()
	}
}

func TestCheckPortAvailableInvalid(t *testing.T) {
	ln, err := netListenLocal()
	if err != nil {
		t.Skip(err)
	}
	port := lnPort(ln)
	_ = ln.Close()
	ln2, err := netListenOn(port)
	if err != nil {
		t.Skip(err)
	}
	defer ln2.Close()
	if err := CheckPortAvailable("127.0.0.1", port); err == nil {
		t.Fatal("expected port busy")
	}
}

func TestServerStartPortBusy(t *testing.T) {
	ln, err := netListenLocal()
	if err != nil {
		t.Skip(err)
	}
	port := lnPort(ln)
	defer ln.Close()
	s := New(t.TempDir(), port, t.TempDir())
	err = s.Start(context.Background())
	if err == nil {
		s.Stop()
		t.Fatal("expected port busy error")
	}
}
