package main

import (
	"crypto/md5"
	"encoding/hex"
	"net/http"
	"os"
	"path/filepath"
	"strings"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

func RegisterPortableUnifiedAPIRoutes(router gin.IRouter, store PortableKnowledgeBaseStore, uploadsDir string, historyStore *InMemoryChatHistoryStore, profileStore *ProfileStore) {
	router.POST("/upload", func(c *gin.Context) { UploadUnifiedDocumentAPI(c, store, uploadsDir) })
	router.GET("/documents", func(c *gin.Context) { ListUnifiedDocumentsAPI(c, store) })
	router.POST("/chat", func(c *gin.Context) { PortableChatAPI(c, store, historyStore, profileStore) })
}

func fallbackDocHash(value string) string {
	sum := md5.Sum([]byte(strings.TrimSpace(value)))
	return hex.EncodeToString(sum[:])
}

func UploadUnifiedDocumentAPI(c *gin.Context, store PortableKnowledgeBaseStore, uploadsDir string) {
	file, err := c.FormFile("file")
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "file is required"})
		return
	}

	kbID := strings.TrimSpace(c.PostForm("kbId"))
	if kbID == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "kbId is required"})
		return
	}

	if _, err := store.GetKnowledgeBase(kbID); err != nil {
		if err == ErrKnowledgeBaseNotFound {
			c.JSON(http.StatusNotFound, gin.H{"error": "knowledge base not found"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to load knowledge base"})
		return
	}

	relativePath := strings.TrimSpace(c.PostForm("relativePath"))
	displayName := file.Filename
	if relativePath != "" {
		displayName = relativePath
	}

	extension := strings.ToLower(filepath.Ext(file.Filename))
	safeDir := filepath.Join(uploadsDir, kbID)
	if err := os.MkdirAll(safeDir, os.ModePerm); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to prepare upload directory"})
		return
	}

	storedName := uuid.NewString() + extension
	savePath := filepath.Join(safeDir, storedName)
	if err := c.SaveUploadedFile(file, savePath); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to save uploaded file"})
		return
	}

	absPath, _ := filepath.Abs(savePath)
	fileType := strings.TrimPrefix(extension, ".")
	docStatus := "completed"
	pageCount := 1
	docHash := fallbackDocHash(absPath)
	message := "upload completed"

	if fileType == "pdf" {
		docStatus = "processing"
		pageCount = 0
		message = "uploaded, AI parsing started"

		resp, parseErr := CallPython("parse", map[string]interface{}{
			"path": absPath,
		})
		if parseErr != nil {
			docStatus = "failed"
			message = "uploaded, but AI parsing failed to start"
		} else {
			if value, ok := resp.Data["docHash"].(string); ok && strings.TrimSpace(value) != "" {
				docHash = strings.TrimSpace(value)
			}
			if raw, ok := resp.Data["pageCount"]; ok {
				switch value := raw.(type) {
				case float64:
					pageCount = int(value)
				case int:
					pageCount = value
				}
			}
		}
	}

	doc := PortableDocument{
		KnowledgeBaseID: kbID,
		FileName:        displayName,
		StoredName:      storedName,
		FileType:        fileType,
		SizeBytes:       file.Size,
		PageCount:       pageCount,
		DocHash:         docHash,
		Status:          docStatus,
	}

	if err := store.CreateDocument(&doc); err != nil {
		_ = os.Remove(savePath)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to save document metadata"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message":    message,
		"docHash":    doc.DocHash,
		"documentId": doc.ID,
		"pageCount":  doc.PageCount,
		"status":     doc.Status,
	})
}

func ListUnifiedDocumentsAPI(c *gin.Context, store PortableKnowledgeBaseStore) {
	kbID := strings.TrimSpace(c.Query("kbId"))

	docs, err := store.ListDocuments(kbID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to load documents"})
		return
	}

	result := make([]PortableDocumentResponse, 0, len(docs))
	for _, doc := range docs {
		result = append(result, mapPortableDocumentResponse(doc))
	}

	c.JSON(http.StatusOK, gin.H{"documents": result})
}
