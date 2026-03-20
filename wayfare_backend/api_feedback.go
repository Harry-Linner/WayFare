package main

import (
	"net/http"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

type FeedbackPayload struct {
	Category          string                 `json:"category"`
	Sentiment         string                 `json:"sentiment"`
	Message           string                 `json:"message"`
	Contact           string                 `json:"contact"`
	Page              string                 `json:"page"`
	Scope             string                 `json:"scope"`
	RecentAction      string                 `json:"recentAction"`
	RecentActionAt    string                 `json:"recentActionAt"`
	KnowledgeBaseID   string                 `json:"knowledgeBaseId"`
	KnowledgeBaseName string                 `json:"knowledgeBaseName"`
	DocumentID        string                 `json:"documentId"`
	DocumentName      string                 `json:"documentName"`
	Metadata          map[string]interface{} `json:"metadata"`
}

func RegisterFeedbackRoutes(router gin.IRouter, store *JSONFeedbackStore) {
	if store == nil {
		return
	}

	router.POST("/feedback", func(c *gin.Context) {
		SubmitFeedbackAPI(c, store)
	})
}

func normalizeFeedbackValue(raw string, fallback string) string {
	value := strings.TrimSpace(raw)
	if value == "" {
		return fallback
	}
	return value
}

func SubmitFeedbackAPI(c *gin.Context, store *JSONFeedbackStore) {
	var payload FeedbackPayload
	if err := c.ShouldBindJSON(&payload); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid request payload"})
		return
	}

	message := strings.TrimSpace(payload.Message)
	if message == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "message is required"})
		return
	}

	entry := FeedbackEntry{
		ID:                uuid.NewString(),
		BetaUser:          betaUserForLog(c),
		BetaUserHash:      hashForLog(betaUserForLog(c)),
		Category:          normalizeFeedbackValue(payload.Category, "suggestion"),
		Sentiment:         normalizeFeedbackValue(payload.Sentiment, "neutral"),
		Message:           message,
		Contact:           strings.TrimSpace(payload.Contact),
		Page:              normalizeFeedbackValue(payload.Page, "unknown"),
		Scope:             normalizeFeedbackValue(payload.Scope, "general"),
		RecentAction:      strings.TrimSpace(payload.RecentAction),
		RecentActionAt:    strings.TrimSpace(payload.RecentActionAt),
		KnowledgeBaseID:   strings.TrimSpace(payload.KnowledgeBaseID),
		KnowledgeBaseName: strings.TrimSpace(payload.KnowledgeBaseName),
		DocumentID:        strings.TrimSpace(payload.DocumentID),
		DocumentName:      strings.TrimSpace(payload.DocumentName),
		UserAgent:         strings.TrimSpace(c.Request.UserAgent()),
		RemoteAddr:        strings.TrimSpace(c.ClientIP()),
		CreatedAt:         time.Now().UTC().Format(time.RFC3339),
		Metadata:          payload.Metadata,
	}

	if err := store.Append(entry); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to save feedback"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"ok":      true,
		"id":      entry.ID,
		"savedAt": entry.CreatedAt,
	})
}
