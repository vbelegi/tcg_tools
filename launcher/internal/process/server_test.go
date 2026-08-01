package process

import (
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestWaitForHealthSuccess(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"status":"ok","app":"tcg_tools"}`))
	}))
	defer srv.Close()

	if err := WaitForHealth(srv.URL, 2*time.Second, nil); err != nil {
		t.Fatal(err)
	}
}

func TestWaitForHealthTimeout(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusServiceUnavailable)
	}))
	defer srv.Close()

	err := WaitForHealth(srv.URL, 500*time.Millisecond, nil)
	if err == nil {
		t.Fatal("expected timeout error")
	}
}

func TestWaitForHealthRejectsWrongApp(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"status":"ok","app":"other"}`))
	}))
	defer srv.Close()

	err := WaitForHealth(srv.URL, 500*time.Millisecond, nil)
	if err == nil {
		t.Fatal("expected timeout when app id mismatches")
	}
}

func TestServerURLs(t *testing.T) {
	s := New(`C:\TCG`, 8080, `C:\data`)
	if s.BaseURL() != "http://127.0.0.1:8080" {
		t.Fatal(s.BaseURL())
	}
	if s.HealthURL() != "http://127.0.0.1:8080/api/v1/health" {
		t.Fatal(s.HealthURL())
	}
}

func TestCheckPortAvailable(t *testing.T) {
	ln, err := netListenLocal()
	if err != nil {
		t.Skip("cannot bind ephemeral port")
	}
	port := lnPort(ln)
	_ = ln.Close()

	if err := CheckPortAvailable("127.0.0.1", port); err != nil {
		t.Fatalf("expected free port: %v", err)
	}

	ln2, err := netListenOn(port)
	if err != nil {
		t.Skip("cannot rebind port")
	}
	defer ln2.Close()

	if err := CheckPortAvailable("127.0.0.1", port); err == nil {
		t.Fatal("expected port in use error")
	}
}
