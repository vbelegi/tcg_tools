package process

import (
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestWaitForHealthSuccess(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))
	defer srv.Close()

	if err := WaitForHealth(srv.URL, 2*time.Second); err != nil {
		t.Fatal(err)
	}
}

func TestWaitForHealthTimeout(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusServiceUnavailable)
	}))
	defer srv.Close()

	err := WaitForHealth(srv.URL, 500*time.Millisecond)
	if err == nil {
		t.Fatal("expected timeout error")
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
