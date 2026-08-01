package tray

import "testing"

func TestAutostartMenuTitle(t *testing.T) {
	if got := AutostartMenuTitle(true); got != "Desativar inicio com Windows" {
		t.Fatalf("got %q", got)
	}
	if got := AutostartMenuTitle(false); got != "Ativar inicio com Windows" {
		t.Fatalf("got %q", got)
	}
}
