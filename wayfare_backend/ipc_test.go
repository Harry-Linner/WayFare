package main

import (
	"errors"
	"path/filepath"
	"testing"
)

func mustAbs(t *testing.T, path string) string {
	t.Helper()

	absolute, err := filepath.Abs(path)
	if err != nil {
		t.Fatalf("failed to resolve absolute path for %q: %v", path, err)
	}

	return absolute
}

func TestResolvePythonExecutableUsesSidecarVenvBinPath(t *testing.T) {
	t.Setenv("WAYFARE_PYTHON", "")

	sidecarDir := mustAbs(t, filepath.Join("opt", "wayfare", "wayfare_ai_backend"))
	expected := filepath.Join(sidecarDir, ".venv", "bin", "python")

	result, err := resolvePythonExecutableWith(
		sidecarDir,
		func(command string) (string, error) {
			return "", errors.New("not found")
		},
		func(path string) bool {
			return path == expected
		},
	)
	if err != nil {
		t.Fatalf("expected no error, got %v", err)
	}
	if result != expected {
		t.Fatalf("expected %q, got %q", expected, result)
	}
}

func TestResolvePythonExecutableSupportsCommandFromEnv(t *testing.T) {
	t.Setenv("WAYFARE_PYTHON", "python3")

	expected := mustAbs(t, filepath.Join("usr", "bin", "python3"))

	result, err := resolvePythonExecutableWith(
		mustAbs(t, filepath.Join("opt", "wayfare", "wayfare_ai_backend")),
		func(command string) (string, error) {
			if command == "python3" {
				return expected, nil
			}
			return "", errors.New("not found")
		},
		func(path string) bool {
			return false
		},
	)
	if err != nil {
		t.Fatalf("expected no error, got %v", err)
	}
	if result != expected {
		t.Fatalf("expected %q, got %q", expected, result)
	}
}
