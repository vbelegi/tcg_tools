package instance

import "testing"

func TestFormatRunningMessage(t *testing.T) {
	msg := FormatRunningMessage(8000)
	if msg == "" {
		t.Fatal("empty message")
	}
}
