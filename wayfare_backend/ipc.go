package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"sync"
	"time"

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
	pythonCmd    *exec.Cmd
)

func InitPythonSidecar() {
	// 获取Python解释器路径
	pythonExe := getPythonExecutable()
	if pythonExe == "" {
		log.Fatal("❌ 未找到Python解释器")
	}

	// 获取Python脚本路径
	scriptPath := getPythonScriptPath()
	if _, err := os.Stat(scriptPath); os.IsNotExist(err) {
		log.Fatalf("❌ Python脚本不存在: %s", scriptPath)
	}

	// 获取工作目录
	workDir := filepath.Dir(scriptPath)

	log.Printf("🐍 启动Python侧车进程...")
	log.Printf("   Python: %s", pythonExe)
	log.Printf("   脚本: %s", scriptPath)
	log.Printf("   工作目录: %s", workDir)

	cmd := exec.Command(pythonExe, scriptPath)
	cmd.Dir = workDir
	cmd.Env = append(os.Environ(),
		"PYTHONUNBUFFERED=1",
		"PYTHONIOENCODING=utf-8",
	)

	stdin, err := cmd.StdinPipe()
	if err != nil {
		log.Fatalf("❌ 无法连接Python stdin: %v", err)
	}

	stdout, err := cmd.StdoutPipe()
	if err != nil {
		log.Fatalf("❌ 无法连接Python stdout: %v", err)
	}

	stderr, err := cmd.StderrPipe()
	if err != nil {
		log.Fatalf("❌ 无法连接Python stderr: %v", err)
	}

	pythonStdin = stdin
	pythonCmd = cmd

	if err := cmd.Start(); err != nil {
		log.Fatalf("❌ 无法启动Python进程: %v", err)
	}

	log.Println("✅ Python AI侧车进程启动成功")

	// 监听标准输出
	go handlePythonStdout(stdout)

	// 监听错误输出
	go handlePythonStderr(stderr)

	// 监控进程状态
	go monitorPythonProcess()
}

func handlePythonStdout(stdout io.Reader) {
	scanner := bufio.NewScanner(stdout)
	for scanner.Scan() {
		line := scanner.Text()
		if line == "" {
			continue
		}

		var resp IpcResponse
		if err := json.Unmarshal([]byte(line), &resp); err == nil {
			if resp.Type == "notification" {
				log.Printf("🔔 Python通知: %v", resp.Data)
				// TODO: 处理通知，如parse_completed
				continue
			}

			if ch, ok := responseChan.Load(resp.ID); ok {
				select {
				case ch.(chan IpcResponse) <- resp:
					responseChan.Delete(resp.ID)
				case <-time.After(30 * time.Second):
					log.Printf("⚠️ 响应超时: %s", resp.ID)
					responseChan.Delete(resp.ID)
				}
			}
		} else {
			log.Printf("⚠️ 无法解析Python输出: %s", line)
		}
	}

	if err := scanner.Err(); err != nil {
		log.Printf("❌ Python stdout扫描错误: %v", err)
	}
}

func handlePythonStderr(stderr io.Reader) {
	scanner := bufio.NewScanner(stderr)
	for scanner.Scan() {
		line := scanner.Text()
		if line != "" {
			log.Printf("🐍 Python日志: %s", line)
		}
	}
}

func monitorPythonProcess() {
	if pythonCmd == nil {
		return
	}

	err := pythonCmd.Wait()
	if err != nil {
		log.Printf("❌ Python进程异常退出: %v", err)
		// 不再尝试重启进程，因为现在我们使用网络调用
		log.Println("ℹ️  Python进程异常退出，但服务将继续使用网络调用")
	} else {
		log.Println("ℹ️ Python进程正常退出")
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

	ch := make(chan IpcResponse, 1)
	responseChan.Store(reqID, ch)

	reqBytes, err := json.Marshal(req)
	if err != nil {
		responseChan.Delete(reqID)
		return IpcResponse{}, fmt.Errorf("请求序列化失败: %w", err)
	}

	if _, err := pythonStdin.Write(append(reqBytes, '\n')); err != nil {
		responseChan.Delete(reqID)
		return IpcResponse{}, fmt.Errorf("写入请求失败: %w", err)
	}

	select {
	case resp := <-ch:
		if !resp.Success {
			return resp, fmt.Errorf("AI错误: %s", resp.Error)
		}
		return resp, nil
	case <-time.After(60 * time.Second):
		responseChan.Delete(reqID)
		return IpcResponse{}, fmt.Errorf("请求超时: %s", reqID)
	}
}

func getPythonExecutable() string {
	// 检查环境变量
	if pythonPath := os.Getenv("PYTHON_EXECUTABLE"); pythonPath != "" {
		if _, err := os.Stat(pythonPath); err == nil {
			return pythonPath
		}
	}

	// 常见路径检查
	candidates := []string{
		"python3",
		"python",
		"/usr/bin/python3",
		"/usr/local/bin/python3",
		"C:\\Python39\\python.exe",
		"C:\\Python310\\python.exe",
		"C:\\Python311\\python.exe",
		"C:\\Users\\%USERNAME%\\AppData\\Local\\Programs\\Python\\Python39\\python.exe",
		"C:\\Users\\%USERNAME%\\AppData\\Local\\Programs\\Python\\Python310\\python.exe",
		"C:\\Users\\%USERNAME%\\AppData\\Local\\Programs\\Python\\Python311\\python.exe",
	}

	for _, candidate := range candidates {
		if _, err := exec.LookPath(candidate); err == nil {
			return candidate
		}
	}

	return ""
}

func getPythonScriptPath() string {
	// 检查环境变量
	if scriptPath := os.Getenv("PYTHON_SCRIPT_PATH"); scriptPath != "" {
		return scriptPath
	}

	// 相对路径检查
	candidates := []string{
		"wayfare_ai_backend/ipc_main.py",
		"../wayfare_ai_backend/ipc_main.py",
		"./wayfare_ai_backend/ipc_main.py",
		"C:/Users/fjt/Desktop/wayfare/wayfare_ai_backend/ipc_main.py",
	}

	for _, candidate := range candidates {
		if _, err := os.Stat(candidate); err == nil {
			return candidate
		}
	}

	return "wayfare_ai_backend/ipc_main.py"
}
