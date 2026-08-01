package instance

import "fmt"

func FormatRunningMessage(port int) string {
	return fmt.Sprintf("TCG Tools ja esta em execucao.\nAbrindo http://127.0.0.1:%d", port)
}
