package main

import (
	"net/http"
	"strings"
	"unicode/utf8"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
)

type ChatRequest struct {
	ProjectID       uint   `json:"projectId"`
	KnowledgeBaseID string `json:"knowledgeBaseId"`
	Context         string `json:"context"`
}

func looksEncodingCorrupted(s string) bool {
	s = strings.TrimSpace(s)
	if s == "" {
		return false
	}

	total := utf8.RuneCountInString(s)
	if total == 0 {
		return false
	}

	questionMarks := strings.Count(s, "?")
	return questionMarks > 0 && float64(questionMarks)/float64(total) >= 0.6
}

func shouldKeepHistoryMessage(content string) bool {
	content = strings.TrimSpace(content)
	if content == "" {
		return false
	}
	if looksEncodingCorrupted(content) {
		return false
	}
	if strings.Contains(content, "The model service is not available now") {
		return false
	}
	return true
}

func ChatAPI(c *gin.Context, db *gorm.DB) {
	var req ChatRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "参数错误"})
		return
	}
	if looksEncodingCorrupted(req.Context) {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "检测到输入内容疑似被错误编码成 '?'，请使用 UTF-8 重新发送请求",
		})
		return
	}

	var docs []Document
	kbID := strings.TrimSpace(req.KnowledgeBaseID)
	if kbID != "" {
		db.Where("knowledge_base_id = ?", kbID).Find(&docs)
	} else {
		db.Where("project_id = ?", req.ProjectID).Find(&docs)
	}

	docHashes := make([]string, 0, len(docs))
	for _, d := range docs {
		docHashes = append(docHashes, d.DocHash)
	}

	var messages []ChatMessage
	db.Where("project_id = ?", req.ProjectID).Order("created_at desc").Limit(4).Find(&messages)

	history := make([]map[string]string, 0, len(messages))
	skipNextAssistant := false
	for i := len(messages) - 1; i >= 0; i-- {
		msg := messages[i]
		if msg.Role == "user" {
			if !shouldKeepHistoryMessage(msg.Content) {
				skipNextAssistant = true
				continue
			}
			skipNextAssistant = false
		} else if msg.Role == "assistant" {
			if skipNextAssistant || !shouldKeepHistoryMessage(msg.Content) {
				skipNextAssistant = false
				continue
			}
		}
		history = append(history, map[string]string{
			"role":    msg.Role,
			"content": msg.Content,
		})
	}

	db.Create(&ChatMessage{ProjectID: req.ProjectID, Role: "user", Content: req.Context})

	resp, err := CallPython("annotate", map[string]interface{}{
		"docHashes": docHashes,
		"type":      "explanation",
		"context":   req.Context,
		"history":   history,
	})
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "详细报错: " + err.Error()})
		return
	}

	var aiContent, knowledgePoint string
	if resp.Data != nil {
		if val, ok := resp.Data["content"].(string); ok {
			aiContent = val
		}
		if val, ok := resp.Data["knowledge_point"].(string); ok {
			knowledgePoint = val
		}
	}

	db.Create(&ChatMessage{ProjectID: req.ProjectID, Role: "assistant", Content: aiContent})

	c.JSON(http.StatusOK, gin.H{
		"knowledgePoint": knowledgePoint,
		"content":        aiContent,
	})
}
