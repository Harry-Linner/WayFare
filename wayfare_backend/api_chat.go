package main

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
)

type ChatRequest struct {
	ProjectID uint   `json:"projectId"`
	Context   string `json:"context"`
}

func ChatAPI(c *gin.Context, db *gorm.DB) {
	var req ChatRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "参数错误"})
		return
	}

	var docs []Document
	db.Where("project_id = ?", req.ProjectID).Find(&docs)

	// 【防御性修复】：强行初始化为空数组，防止因为没查到数据导致传给 Python 变成 null
	docHashes := make([]string, 0)
	for _, d := range docs {
		docHashes = append(docHashes, d.DocHash)
	}

	var messages []ChatMessage
	db.Where("project_id = ?", req.ProjectID).Order("created_at desc").Limit(4).Find(&messages)

	// 【防御性修复】：强行初始化为空数组
	history := make([]map[string]string, 0)
	for i := len(messages) - 1; i >= 0; i-- {
		history = append(history, map[string]string{
			"role":    messages[i].Role,
			"content": messages[i].Content,
		})
	}

	db.Create(&ChatMessage{ProjectID: req.ProjectID, Role: "user", Content: req.Context})

	resp, err := CallPython("annotate", map[string]interface{}{
		"docHashes": docHashes,
		"type":      "explanation",
		"context":   req.Context,
		"history":   history,
	})

	// 🚀 【抓虫核心】：如果报错，把 Python 返回的真实底细全打印出来！
	if err != nil {
		c.JSON(500, gin.H{"error": "详细报错: " + err.Error()})
		return
	}

	// 提取数据（防空指针）
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
