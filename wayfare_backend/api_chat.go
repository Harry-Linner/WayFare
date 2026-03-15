package main

import (
	"net/http"
	"strings"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
)

type IncomingChatMessage struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type ChatRequest struct {
	ProjectID uint                  `json:"projectId"`
	Message   string                `json:"message"`
	Context   string                `json:"context"`
	DocHash   string                `json:"docHash"`
	History   []IncomingChatMessage `json:"history"`
}

func ChatAPI(c *gin.Context, db *gorm.DB) {
	var req ChatRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "请求参数错误"})
		return
	}

	projectID := req.ProjectID
	if projectID == 0 {
		projectID = defaultProjectID
	}

	message := strings.TrimSpace(req.Message)
	if message == "" {
		message = strings.TrimSpace(req.Context)
	}

	if message == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "消息内容不能为空"})
		return
	}

	docHashes := collectDocHashes(db, projectID, req.DocHash)
	history := buildChatHistory(db, projectID, req.DocHash, req.History)

	userMessage := ChatMessage{
		ProjectID: projectID,
		Role:      "user",
		Content:   message,
	}
	if req.DocHash != "" {
		userMessage.DocHash = stringPtr(req.DocHash)
	}
	_ = db.Create(&userMessage).Error

	resp, err := CallPythonViaNetwork("annotate", map[string]interface{}{
		"docHash":   req.DocHash,
		"docHashes": docHashes,
		"type":      "explanation",
		"context":   message,
		"history":   history,
	})
	if err != nil {
		c.JSON(http.StatusBadGateway, gin.H{"error": "Python AI 调用失败: " + err.Error()})
		return
	}

	aiContent := valueAsString(resp.Data["content"])
	if aiContent == "" {
		aiContent = valueAsString(resp.Data["message"])
	}
	if aiContent == "" {
		aiContent = "暂时没有生成可用回答。"
	}

	annotationID := valueAsString(resp.Data["annotationId"])
	knowledgePoint := valueAsString(resp.Data["knowledge_point"])
	if knowledgePoint == "" {
		knowledgePoint = valueAsString(resp.Data["knowledgePoint"])
	}
	responseType := valueAsString(resp.Data["type"])

	assistantMessage := ChatMessage{
		ProjectID: projectID,
		Role:      "assistant",
		Content:   aiContent,
	}
	if req.DocHash != "" {
		assistantMessage.DocHash = stringPtr(req.DocHash)
	}
	_ = db.Create(&assistantMessage).Error

	c.JSON(http.StatusOK, gin.H{
		"message":        aiContent,
		"content":        aiContent,
		"annotationId":   annotationID,
		"knowledgePoint": knowledgePoint,
		"type":           responseType,
	})
}

func buildChatHistory(
	db *gorm.DB,
	projectID uint,
	docHash string,
	incomingHistory []IncomingChatMessage,
) []map[string]string {
	if len(incomingHistory) > 0 {
		history := make([]map[string]string, 0, len(incomingHistory))
		for _, item := range incomingHistory {
			if item.Role == "" || item.Content == "" {
				continue
			}

			history = append(history, map[string]string{
				"role":    item.Role,
				"content": item.Content,
			})
		}

		return history
	}

	query := db.Where("project_id = ?", projectID)
	if docHash != "" {
		query = query.Where("doc_hash = ?", docHash)
	}

	var messages []ChatMessage
	query.Order("created_at desc").Limit(8).Find(&messages)

	history := make([]map[string]string, 0, len(messages))
	for i := len(messages) - 1; i >= 0; i-- {
		history = append(history, map[string]string{
			"role":    messages[i].Role,
			"content": messages[i].Content,
		})
	}

	return history
}

func collectDocHashes(db *gorm.DB, projectID uint, docHash string) []string {
	if docHash != "" {
		return []string{docHash}
	}

	var documents []Document
	db.Where("project_id = ?", projectID).Find(&documents)

	hashes := make([]string, 0, len(documents))
	for _, document := range documents {
		if document.DocHash == "" {
			continue
		}
		hashes = append(hashes, document.DocHash)
	}

	return hashes
}

func stringPtr(value string) *string {
	if value == "" {
		return nil
	}

	return &value
}
