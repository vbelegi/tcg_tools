package netutil

import (
	"fmt"
	"net"
)

// PrimaryIPv4 returns a non-loopback IPv4 suitable for LAN access hints.
func PrimaryIPv4() (string, error) {
	ifaces, err := net.Interfaces()
	if err != nil {
		return "", err
	}
	for _, iface := range ifaces {
		if iface.Flags&net.FlagUp == 0 || iface.Flags&net.FlagLoopback != 0 {
			continue
		}
		addrs, err := iface.Addrs()
		if err != nil {
			continue
		}
		for _, addr := range addrs {
			var ip net.IP
			switch v := addr.(type) {
			case *net.IPNet:
				ip = v.IP
			case *net.IPAddr:
				ip = v.IP
			}
			if ip == nil || ip.IsLoopback() {
				continue
			}
			ip = ip.To4()
			if ip == nil {
				continue
			}
			return ip.String(), nil
		}
	}
	return "", fmt.Errorf("nenhum IPv4 de rede local encontrado")
}

func LANURL(port int) (string, error) {
	ip, err := PrimaryIPv4()
	if err != nil {
		return "", err
	}
	return fmt.Sprintf("http://%s:%d", ip, port), nil
}
