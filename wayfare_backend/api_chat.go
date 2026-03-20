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
	DisplayMessage  string `json:"displayMessage"`
	RequestType     string `json:"requestType"`
	Action          string `json:"action"`
	SelectedText    string `json:"selectedText"`
	Page            int    `json:"page"`
	DocumentName    string `json:"documentName"`
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

func resolveChatContext(req ChatRequest) string {
	if selected := strings.TrimSpace(req.SelectedText); selected != "" {
		return selected
	}
	return strings.TrimSpace(req.Context)
}

func resolveHistoryUserMessage(req ChatRequest) string {
	if display := strings.TrimSpace(req.DisplayMessage); display != "" {
		return display
	}
	if selected := strings.TrimSpace(req.SelectedText); selected != "" {
		return selected
	}
	return strings.TrimSpace(req.Context)
}

func normalizeSelectionAction(action string) string {
	switch strings.ToLower(strings.TrimSpace(action)) {
	case "summary":
		return "summary"
	case "ask":
		return "ask"
	default:
		return "explanation"
	}
}

func resolvePreferredResponseLanguage(req ChatRequest) string {
	combined := strings.ToLower(strings.TrimSpace(resolveHistoryUserMessage(req) + " " + resolveChatContext(req)))

	if strings.Contains(combined, "please answer in english") ||
		strings.Contains(combined, "answer in english") ||
		strings.Contains(combined, "respond in english") ||
		strings.Contains(combined, "用英文") ||
		strings.Contains(combined, "英文回答") {
		return "English"
	}

	return "简体中文"
}

func ChatAPI(c *gin.Context, db *gorm.DB) {
	var req ChatRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid request payload"})
		return
	}

	chatContext := resolveChatContext(req)
	if chatContext == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "message content is required"})
		return
	}
	if looksEncodingCorrupted(chatContext) {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "input appears to be mis-encoded as question marks; please resend using UTF-8",
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

	userMessageForHistory := resolveHistoryUserMessage(req)
	db.Create(&ChatMessage{ProjectID: req.ProjectID, Role: "user", Content: userMessageForHistory})

	annotateType := "explanation"
	meta := map[string]interface{}{}
	if strings.EqualFold(strings.TrimSpace(req.RequestType), "selection_action") {
		annotateType = normalizeSelectionAction(req.Action)
		if req.Page > 0 {
			meta["page"] = req.Page
		}
		if docName := strings.TrimSpace(req.DocumentName); docName != "" {
			meta["documentName"] = docName
		}
	}

	resp, err := CallPython("annotate", map[string]interface{}{
		"docHashes":        docHashes,
		"type":             annotateType,
		"context":          chatContext,
		"history":          history,
		"meta":             meta,
		"responseLanguage": resolvePreferredResponseLanguage(req),
	})
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "AI request failed: " + err.Error()})
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
