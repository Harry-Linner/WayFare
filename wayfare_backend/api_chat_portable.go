package main

import (
	"fmt"
	"net/http"
	"strings"

	"github.com/gin-gonic/gin"
)

func buildPortableChatSessionKey(req ChatRequest) string {
	kbID := strings.TrimSpace(req.KnowledgeBaseID)
	if kbID == "" {
		return fmt.Sprintf("project:%d", req.ProjectID)
	}
	return fmt.Sprintf("project:%d:kb:%s", req.ProjectID, kbID)
}

func PortableChatAPI(c *gin.Context, store PortableKnowledgeBaseStore, historyStore *InMemoryChatHistoryStore, profileStore *ProfileStore) {
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

	var docs []PortableDocument
	var kb *KnowledgeBase
	var err error
	kbID := strings.TrimSpace(req.KnowledgeBaseID)
	if kbID != "" {
		kb, err = store.GetKnowledgeBase(kbID)
		if err != nil {
			if err == ErrKnowledgeBaseNotFound {
				c.JSON(http.StatusNotFound, gin.H{"error": "knowledge base not found"})
				return
			}
			c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to load knowledge base"})
			return
		}
		docs, err = store.ListDocuments(kbID)
	} else {
		docs, err = store.ListDocuments("")
	}
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to load knowledge base documents"})
		return
	}

	docHashes := make([]string, 0, len(docs))
	for _, doc := range docs {
		if strings.TrimSpace(doc.DocHash) != "" {
			docHashes = append(docHashes, doc.DocHash)
		}
	}

	sessionKey := buildPortableChatSessionKey(req)
	history := historyStore.Get(sessionKey, 4)
	userMessageForHistory := resolveHistoryUserMessage(req)
	if shouldKeepHistoryMessage(userMessageForHistory) {
		historyStore.Add(sessionKey, "user", userMessageForHistory)
	}

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
	if kb != nil {
		if kb.Name != "" {
			meta["knowledgeBaseName"] = kb.Name
		}
		if kb.Description != "" {
			meta["knowledgeBaseDescription"] = kb.Description
		}
		if kb.Purpose != "" {
			meta["knowledgeBasePurpose"] = kb.Purpose
		}
		if kb.LearningGoals != "" {
			meta["knowledgeBaseLearningGoals"] = kb.LearningGoals
		}
	}

	globalProfileContent := ""
	knowledgeBaseProfileContent := ""
	if profileStore != nil {
		if profile, profileErr := profileStore.GetGlobalProfile(); profileErr == nil {
			globalProfileContent = strings.TrimSpace(profile.Content)
		}
		if kbID != "" {
			if profile, profileErr := profileStore.GetKnowledgeBaseProfile(kbID); profileErr == nil {
				knowledgeBaseProfileContent = strings.TrimSpace(profile.Content)
			}
		}
	}

	resp, err := CallPython("annotate", map[string]interface{}{
		"docHashes":            docHashes,
		"type":                 annotateType,
		"context":              chatContext,
		"history":              history,
		"meta":                 meta,
		"globalProfile":        globalProfileContent,
		"knowledgeBaseProfile": knowledgeBaseProfileContent,
		"responseLanguage":     resolvePreferredResponseLanguage(req),
	})
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "AI request failed: " + err.Error()})
		return
	}

	var aiContent, knowledgePoint string
	if resp.Data != nil {
		if value, ok := resp.Data["content"].(string); ok {
			aiContent = value
		}
		if value, ok := resp.Data["knowledge_point"].(string); ok {
			knowledgePoint = value
		}
	}

	if shouldKeepHistoryMessage(aiContent) {
		historyStore.Add(sessionKey, "assistant", aiContent)
	}

	c.JSON(http.StatusOK, gin.H{
		"knowledgePoint": knowledgePoint,
		"content":        aiContent,
	})
}
