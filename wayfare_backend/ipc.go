package main

import (
	"bufio"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"github.com/google/uuid"
	"gorm.io/gorm"
)

type IpcRequest struct {
	ID     string                 `json:"id"`
	Seq    int                    `json:"seq"`
	Method string                 `json:"method"`
	Params map[string]interface{} `json:"params"`
}

type IpcResponse struct {
	ID      string                 `json:"id"`
	Success bool                   `json:"success"`
	Data    map[string]interface{} `json:"data"`
	Error   string                 `json:"error"`
	Type    string                 `json:"type"`
}

var (
	pythonStdin          io.WriteCloser
	pythonCmd            *exec.Cmd
	responseChan         sync.Map
	ipcMu                sync.Mutex
	sidecarReady         bool
	appDB                *gorm.DB
	notificationDocStore PortableKnowledgeBaseStore
)

type lookPathFunc func(string) (string, error)
type pathExistsFunc func(string) bool

func isCommandCandidate(candidate string) bool {
	return candidate != "" && !strings.ContainsAny(candidate, `/\`)
}

func resolvePythonExecutableWith(sidecarDir string, lookPath lookPathFunc, pathExists pathExistsFunc) (string, error) {
	candidates := []string{}
	if envPath := strings.TrimSpace(os.Getenv("WAYFARE_PYTHON")); envPath != "" {
		candidates = append(candidates, envPath)
	}

	if strings.TrimSpace(sidecarDir) != "" {
		candidates = append(candidates,
			filepath.Join(sidecarDir, ".venv", "Scripts", "python.exe"),
			filepath.Join(sidecarDir, ".venv", "bin", "python"),
		)
	}

	candidates = append(candidates, "python", "python3")

	seen := map[string]struct{}{}
	for _, candidate := range candidates {
		candidate = strings.TrimSpace(candidate)
		if candidate == "" {
			continue
		}
		if _, ok := seen[candidate]; ok {
			continue
		}
		seen[candidate] = struct{}{}

		if isCommandCandidate(candidate) {
			if resolved, err := lookPath(candidate); err == nil {
				return resolved, nil
			}
			continue
		}

		if pathExists(candidate) {
			if absolute, absErr := filepath.Abs(candidate); absErr == nil {
				return absolute, nil
			}
			return candidate, nil
		}
	}

	return "", errors.New("python executable for the WayFare sidecar was not found; set WAYFARE_PYTHON or create the sidecar .venv first")
}

func resolvePythonExecutable(sidecarDir string) (string, error) {
	return resolvePythonExecutableWith(sidecarDir, exec.LookPath, func(path string) bool {
		_, err := os.Stat(path)
		return err == nil
	})
}

func resolveSidecarScript() (string, string, error) {
	candidates := []string{
		filepath.Clean(filepath.Join("wayfare_ai_backend", "ipc_main.py")),
		filepath.Clean(filepath.Join("..", "wayfare_ai_backend", "ipc_main.py")),
	}

	for _, scriptPath := range candidates {
		if _, err := os.Stat(scriptPath); err == nil {
			absoluteScriptPath, absErr := filepath.Abs(scriptPath)
			if absErr != nil {
				return filepath.Dir(scriptPath), scriptPath, nil
			}
			return filepath.Dir(absoluteScriptPath), absoluteScriptPath, nil
		}
	}

	return "", "", fmt.Errorf("python sidecar script was not found in bundled or repo-relative locations")
}

func InitPythonSidecar(db *gorm.DB, store PortableKnowledgeBaseStore) error {
	ipcMu.Lock()
	defer ipcMu.Unlock()

	appDB = db
	notificationDocStore = store
	if sidecarReady && pythonStdin != nil {
		return nil
	}

	sidecarDir, scriptPath, err := resolveSidecarScript()
	if err != nil {
		return err
	}

	pythonExe, err := resolvePythonExecutable(sidecarDir)
	if err != nil {
		return err
	}

	cmd := exec.Command(pythonExe, scriptPath)
	cmd.Dir = sidecarDir

	stdin, err := cmd.StdinPipe()
	if err != nil {
		return fmt.Errorf("failed to connect Python stdin: %w", err)
	}

	stdout, err := cmd.StdoutPipe()
	if err != nil {
		return fmt.Errorf("failed to connect Python stdout: %w", err)
	}

	cmd.Stderr = os.Stderr

	if err := cmd.Start(); err != nil {
		return fmt.Errorf("failed to start Python sidecar: %w", err)
	}

	pythonCmd = cmd
	pythonStdin = stdin
	sidecarReady = true

	go func() {
		scanner := bufio.NewScanner(stdout)
		for scanner.Scan() {
			line := scanner.Text()
			var resp IpcResponse
			if err := json.Unmarshal([]byte(line), &resp); err != nil {
				continue
			}

			if resp.Type == "notification" {
				handlePythonNotification(resp.Data)
				continue
			}

			if ch, ok := responseChan.Load(resp.ID); ok {
				ch.(chan IpcResponse) <- resp
				responseChan.Delete(resp.ID)
			}
		}

		ipcMu.Lock()
		sidecarReady = false
		pythonStdin = nil
		ipcMu.Unlock()
	}()

	return nil
}

func handlePythonNotification(data map[string]interface{}) {
	if appDB == nil && notificationDocStore == nil {
		return
	}

	eventType, _ := data["type"].(string)
	docHash, _ := data["docHash"].(string)
	if docHash == "" {
		return
	}

	if appDB != nil {
		switch eventType {
		case "parse_completed":
			appDB.Model(&Document{}).Where("doc_hash = ?", docHash).Update("status", "completed")
		case "parse_failed":
			appDB.Model(&Document{}).Where("doc_hash = ?", docHash).Update("status", "failed")
		}
	}

	if notificationDocStore != nil {
		switch eventType {
		case "parse_completed":
			_, _ = notificationDocStore.UpdateDocumentStatusByDocHash(docHash, "completed")
		case "parse_failed":
			_, _ = notificationDocStore.UpdateDocumentStatusByDocHash(docHash, "failed")
		}
	}
}

func CallPython(method string, params map[string]interface{}) (IpcResponse, error) {
	ipcMu.Lock()
	ready := sidecarReady && pythonStdin != nil
	stdin := pythonStdin
	ipcMu.Unlock()

	if !ready || stdin == nil {
		return IpcResponse{}, errors.New("python sidecar is not running")
	}

	reqID := uuid.New().String()
	req := IpcRequest{
		ID:     reqID,
		Seq:    1,
		Method: method,
		Params: params,
	}

	ch := make(chan IpcResponse, 1)
	responseChan.Store(reqID, ch)

	reqBytes, err := json.Marshal(req)
	if err != nil {
		responseChan.Delete(reqID)
		return IpcResponse{}, err
	}

	if _, err := stdin.Write(append(reqBytes, '\n')); err != nil {
		responseChan.Delete(reqID)
		return IpcResponse{}, fmt.Errorf("failed to send request to Python sidecar: %w", err)
	}

	select {
	case resp := <-ch:
		if !resp.Success {
			return resp, fmt.Errorf("AI Error: %s", resp.Error)
		}
		return resp, nil
	case <-time.After(3 * time.Minute):
		responseChan.Delete(reqID)
		return IpcResponse{}, errors.New("python sidecar request timed out")
	}
}
