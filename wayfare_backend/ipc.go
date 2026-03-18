package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"io"
	"os/exec"
	"sync"

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
	pythonStdin  io.WriteCloser
	responseChan sync.Map
	appDB        *gorm.DB
)

func InitPythonSidecar(db *gorm.DB) {
	appDB = db

	pythonExe := `..\wayfare_ai_backend\.venv\Scripts\python.exe`
	scriptPath := `..\wayfare_ai_backend\ipc_main.py`
	cmd := exec.Command(pythonExe, scriptPath)
	cmd.Dir = `..\wayfare_ai_backend`

	stdin, err := cmd.StdinPipe()
	if err != nil {
		panic("无法连接 Python stdin: " + err.Error())
	}

	stdout, err := cmd.StdoutPipe()
	if err != nil {
		panic("无法连接 Python stdout: " + err.Error())
	}

	pythonStdin = stdin
	if err := cmd.Start(); err != nil {
		panic("无法启动 Python 进程: " + err.Error())
	}

	fmt.Println("Python AI sidecar 已启动")

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
	}()
}

func handlePythonNotification(data map[string]interface{}) {
	fmt.Println("收到 Python 通知:", data)
	if appDB == nil {
		return
	}

	eventType, _ := data["type"].(string)
	docHash, _ := data["docHash"].(string)
	if docHash == "" {
		return
	}

	switch eventType {
	case "parse_completed":
		appDB.Model(&Document{}).Where("doc_hash = ?", docHash).Update("status", "completed")
	case "parse_failed":
		appDB.Model(&Document{}).Where("doc_hash = ?", docHash).Update("status", "failed")
	}
}

func CallPython(method string, params map[string]interface{}) (IpcResponse, error) {
	reqID := uuid.New().String()
	req := IpcRequest{
		ID:     reqID,
		Seq:    1,
		Method: method,
		Params: params,
	}

	ch := make(chan IpcResponse)
	responseChan.Store(reqID, ch)

	reqBytes, _ := json.Marshal(req)
	pythonStdin.Write(append(reqBytes, '\n'))

	resp := <-ch
	if !resp.Success {
		return resp, fmt.Errorf("AI Error: %s", resp.Error)
	}
	return resp, nil
}
