package process

import (
	"bytes"
	"context"
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"time"
)

const (
	HealthPath     = "/api/v1/health"
	DefaultTimeout = 30 * time.Second
	PollInterval   = 300 * time.Millisecond
)

type Server struct {
	installDir string
	port       int
	cmd        *exec.Cmd
	dataDir    string
	exitCh     chan error
	stderr     bytes.Buffer
}

func New(installDir string, port int, dataDir string) *Server {
	return &Server{installDir: installDir, port: port, dataDir: dataDir}
}

func (s *Server) PythonExe() string {
	return filepath.Join(s.installDir, "runtime", "python", "python.exe")
}

func (s *Server) BackendDir() string {
	return filepath.Join(s.installDir, "backend")
}

func (s *Server) BaseURL() string {
	return fmt.Sprintf("http://127.0.0.1:%d", s.port)
}

func (s *Server) HealthURL() string {
	return s.BaseURL() + HealthPath
}

func (s *Server) Start(ctx context.Context) error {
	if err := CheckPortAvailable("127.0.0.1", s.port); err != nil {
		return err
	}

	python := s.PythonExe()
	if _, err := os.Stat(python); err != nil {
		return fmt.Errorf("python embeddable nao encontrado: %s", python)
	}

	s.stderr.Reset()
	s.cmd = exec.CommandContext(
		ctx,
		python,
		"-m", "uvicorn", "app.main:app",
		"--host", "127.0.0.1",
		"--port", fmt.Sprintf("%d", s.port),
	)
	s.cmd.Dir = s.BackendDir()
	s.cmd.Env = append(os.Environ(),
		"TCGTOOLS_DATA_DIR="+s.dataDir,
		fmt.Sprintf("TCGTOOLS_PORT=%d", s.port),
	)
	s.cmd.Stderr = &s.stderr
	applyWindowsNoWindow(s.cmd)

	if err := assignToJobObject(s.cmd); err != nil {
		return err
	}
	if err := s.cmd.Start(); err != nil {
		return err
	}
	if err := assignProcessToJob(s.cmd); err != nil {
		_ = s.cmd.Process.Kill()
		_, _ = s.cmd.Process.Wait()
		s.cmd = nil
		return err
	}

	s.exitCh = make(chan error, 1)
	go func() {
		s.exitCh <- s.cmd.Wait()
	}()

	if err := WaitForHealth(s.HealthURL(), DefaultTimeout, s.exitCh); err != nil {
		detail := s.stderr.String()
		_ = s.Stop()
		if detail != "" {
			return fmt.Errorf("%w: %s", err, detail)
		}
		return err
	}
	return nil
}

func (s *Server) Stop() error {
	if s.cmd == nil || s.cmd.Process == nil {
		return nil
	}
	proc := s.cmd.Process
	_ = proc.Kill()
	_, _ = proc.Wait()
	s.cmd = nil
	s.exitCh = nil
	return nil
}

func WaitForHealth(healthURL string, timeout time.Duration, exitCh <-chan error) error {
	deadline := time.Now().Add(timeout)
	client := &http.Client{Timeout: 2 * time.Second}
	for time.Now().Before(deadline) {
		if exitCh != nil {
			select {
			case err := <-exitCh:
				if err == nil {
					return fmt.Errorf("servidor encerrou antes do health check")
				}
				return fmt.Errorf("servidor encerrou antes do health check: %w", err)
			default:
			}
		}
		if fetchHealthOK(client, healthURL) {
			return nil
		}
		time.Sleep(PollInterval)
	}
	return fmt.Errorf("timeout aguardando servidor em %s", healthURL)
}
