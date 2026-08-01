package process

import (
	"fmt"
	"net"
)

func netListenLocal() (net.Listener, error) {
	return net.Listen("tcp", "127.0.0.1:0")
}

func lnPort(ln net.Listener) int {
	addr := ln.Addr().(*net.TCPAddr)
	return addr.Port
}

func netListenOn(port int) (net.Listener, error) {
	return net.Listen("tcp", fmt.Sprintf("127.0.0.1:%d", port))
}
