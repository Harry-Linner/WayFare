package main

import (
	"fmt"
	"net"
	"net/url"
	"os/exec"
	"runtime"
)

func FindAvailableListener(host string, preferredPort int, attempts int) (net.Listener, int, error) {
	if attempts <= 0 {
		attempts = 1
	}

	for offset := 0; offset < attempts; offset++ {
		port := preferredPort + offset
		listener, err := net.Listen("tcp", fmt.Sprintf("%s:%d", host, port))
		if err == nil {
			return listener, port, nil
		}
	}

	return nil, 0, fmt.Errorf("no available port found from %d to %d", preferredPort, preferredPort+attempts-1)
}

func OpenBrowser(rawURL string) error {
	if _, err := url.Parse(rawURL); err != nil {
		return err
	}

	var cmd *exec.Cmd
	switch runtime.GOOS {
	case "windows":
		cmd = exec.Command("rundll32", "url.dll,FileProtocolHandler", rawURL)
	case "darwin":
		cmd = exec.Command("open", rawURL)
	default:
		cmd = exec.Command("xdg-open", rawURL)
	}

	return cmd.Start()
}
