package process

import (
	"fmt"
	"net"
)

func CheckPortAvailable(host string, port int) error {
	addr := net.JoinHostPort(host, fmt.Sprintf("%d", port))
	ln, err := net.Listen("tcp", addr)
	if err != nil {
		return fmt.Errorf("porta %d indisponivel (ja em uso?): %w", port, err)
	}
	return ln.Close()
}
