package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"time"
)

// IpcRequest 网络请求结构
type NetworkIpcRequest struct {
	Method string                 `json:"method"`
	Params map[string]interface{} `json:"params"`
}

// NetworkIpcResponse 网络响应结构
type NetworkIpcResponse struct {
	Success bool                   `json:"success"`
	Data    map[string]interface{} `json:"data"`
	Error   string                 `json:"error"`
}

// CallPythonViaNetwork 通过网络调用Python AI服务
func CallPythonViaNetwork(method string, params map[string]interface{}) (IpcResponse, error) {
	pythonAIURL := getPythonAIURL()
	if pythonAIURL == "" {
		return IpcResponse{}, fmt.Errorf("Python AI服务地址未配置")
	}

	// 构建请求
	reqData := NetworkIpcRequest{
		Method: method,
		Params: params,
	}

	jsonData, err := json.Marshal(reqData)
	if err != nil {
		return IpcResponse{}, fmt.Errorf("请求序列化失败: %w", err)
	}

	// 发送HTTP请求
	client := &http.Client{
		Timeout: 60 * time.Second,
	}

	req, err := http.NewRequest("POST", pythonAIURL+"/api/process", bytes.NewBuffer(jsonData))
	if err != nil {
		return IpcResponse{}, fmt.Errorf("创建请求失败: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")

	resp, err := client.Do(req)
	if err != nil {
		return IpcResponse{}, fmt.Errorf("请求发送失败: %w", err)
	}
	defer resp.Body.Close()

	// 读取响应
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return IpcResponse{}, fmt.Errorf("读取响应失败: %w", err)
	}

	// 解析响应
	var networkResp NetworkIpcResponse
	if err := json.Unmarshal(body, &networkResp); err != nil {
		return IpcResponse{}, fmt.Errorf("响应解析失败: %w, 原始响应: %s", err, string(body))
	}

	// 转换为内部格式
	result := IpcResponse{
		Success: networkResp.Success,
		Data:    networkResp.Data,
		Error:   networkResp.Error,
	}

	if !result.Success {
		return result, fmt.Errorf("AI服务返回错误: %s", result.Error)
	}

	return result, nil
}

// getPythonAIURL 获取Python AI服务的URL
func getPythonAIURL() string {
	// 优先检查环境变量
	if url := os.Getenv("PYTHON_AI_URL"); url != "" {
		return url
	}

	// 本地联调默认走 localhost；Docker Compose 请通过环境变量覆盖
	return "http://localhost:8001"
}

// CheckPythonAIHealth 检查Python AI服务健康状态
func CheckPythonAIHealth() error {
	pythonAIURL := getPythonAIURL()
	if pythonAIURL == "" {
		return fmt.Errorf("Python AI服务地址未配置")
	}

	client := &http.Client{
		Timeout: 5 * time.Second,
	}

	resp, err := client.Get(pythonAIURL + "/health")
	if err != nil {
		return fmt.Errorf("健康检查失败: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("服务状态异常: %d", resp.StatusCode)
	}

	return nil
}
