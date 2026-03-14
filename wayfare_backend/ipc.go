package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"io"
	"os/exec"
	"sync"

	"github.com/google/uuid"
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
	Type    string                 `json:"type"` // 用于识别 notification
}

var (
	pythonStdin  io.WriteCloser
	responseChan sync.Map
)

func InitPythonSidecar() {
	pythonExe := `C:\Users\fjt\Desktop\wayfare\wayfare_ai_backend\.venv\Scripts\python.exe`
	scriptPath := `C:\Users\fjt\Desktop\wayfare\wayfare_ai_backend\ipc_main.py`

	cmd := exec.Command(pythonExe, scriptPath)

	// 🚀 【关键修复】：强行指定 Python 的工作目录！让它能找到自己的 .env 文件！
	cmd.Dir = `C:\Users\fjt\Desktop\wayfare\wayfare_ai_backend`
	stdin, err := cmd.StdinPipe()
	if err != nil {
		panic("无法连接 Python Stdin: " + err.Error())
	}
	stdout, err := cmd.StdoutPipe()
	if err != nil {
		panic("无法连接 Python Stdout: " + err.Error())
	}

	pythonStdin = stdin
	if err := cmd.Start(); err != nil {
		panic("无法启动 Python 进程: " + err.Error())
	}

	fmt.Println("🚀 Python AI 侧车已成功挂载！")

	// 持续监听 Python 的标准输出
	go func() {
		scanner := bufio.NewScanner(stdout)
		for scanner.Scan() {
			line := scanner.Text()
			var resp IpcResponse
			if err := json.Unmarshal([]byte(line), &resp); err == nil {
				if resp.Type == "notification" {
					fmt.Println("🔔 收到 Python 主动通知:", resp.Data)
					// TODO: 如果是 parse_completed，可以去更新数据库文档状态
					continue
				}
				if ch, ok := responseChan.Load(resp.ID); ok {
					ch.(chan IpcResponse) <- resp
					responseChan.Delete(resp.ID)
				}
			}
		}
	}()
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
