package process

import (
	"strings"
	"testing"
)

func TestHealthResponseOK(t *testing.T) {
	body := strings.NewReader(`{"status":"ok","app":"tcg_tools"}`)
	if !healthResponseOK(body) {
		t.Fatal("expected valid health payload")
	}
}

func TestHealthResponseRejectsForeignApp(t *testing.T) {
	body := strings.NewReader(`{"status":"ok","app":"other"}`)
	if healthResponseOK(body) {
		t.Fatal("expected rejection")
	}
}

func TestHealthResponseRejectsStatusOnly(t *testing.T) {
	body := strings.NewReader(`{"status":"ok"}`)
	if healthResponseOK(body) {
		t.Fatal("expected rejection without app id")
	}
}
