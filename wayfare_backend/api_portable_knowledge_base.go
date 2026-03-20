package main

import (
	"errors"
	"mime"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

type KnowledgeBasePayload struct {
	Name           string `json:"name"`
	Description    string `json:"description"`
	Purpose        string `json:"purpose"`
	Subject        string `json:"subject"`
	LearningGoals  string `json:"learningGoals"`
	StudyTime      string `json:"studyTime"`
	CreationMethod string `json:"creationMethod"`
	FolderName     string `json:"folderName"`
}

type KnowledgeBaseResponse struct {
	ID                     string `json:"id"`
	Name                   string `json:"name"`
	Description            string `json:"description"`
	Purpose                string `json:"purpose,omitempty"`
	Subject                string `json:"subject,omitempty"`
	LearningGoals          string `json:"learningGoals,omitempty"`
	StudyTime              string `json:"studyTime,omitempty"`
	CreationMethod         string `json:"creationMethod,omitempty"`
	FolderName             string `json:"folderName,omitempty"`
	DocumentCount          int    `json:"documentCount"`
	ReadyDocumentCount     int    `json:"readyDocumentCount"`
	ProcessingDocumentCount int   `json:"processingDocumentCount"`
	FailedDocumentCount    int    `json:"failedDocumentCount"`
	Progress               int    `json:"progress"`
	CreatedAt              string `json:"createdAt"`
	UpdatedAt              string `json:"updatedAt"`
}

type PortableDocumentResponse struct {
	ID              string `json:"id"`
	KnowledgeBaseID string `json:"knowledgeBaseId"`
	FileName        string `json:"fileName"`
	FileType        string `json:"fileType"`
	SizeBytes       int64  `json:"sizeBytes"`
	PageCount       int    `json:"pageCount"`
	DocHash         string `json:"docHash"`
	Status          string `json:"status"`
	CreatedAt       string `json:"createdAt"`
	FileURL         string `json:"fileUrl"`
}

func RegisterPortableKnowledgeBaseRoutes(router gin.IRouter, store PortableKnowledgeBaseStore, uploadsDir string) {
	router.GET("/knowledge-bases", func(c *gin.Context) { ListKnowledgeBasesAPI(c, store) })
	router.GET("/knowledge-bases/:id", func(c *gin.Context) { GetKnowledgeBaseAPI(c, store) })
	router.POST("/knowledge-bases", func(c *gin.Context) { CreateKnowledgeBaseAPI(c, store) })
	router.DELETE("/knowledge-bases/:id", func(c *gin.Context) { DeleteKnowledgeBaseAPI(c, store, uploadsDir) })
	router.GET("/knowledge-bases/:id/documents", func(c *gin.Context) { ListPortableDocumentsAPI(c, store) })
	router.POST("/knowledge-bases/:id/documents", func(c *gin.Context) { UploadPortableDocumentAPI(c, store, uploadsDir) })
	router.DELETE("/documents/:id", func(c *gin.Context) { DeletePortableDocumentAPI(c, store, uploadsDir) })
	router.GET("/documents/:id/file", func(c *gin.Context) { ServePortableDocumentAPI(c, store, uploadsDir) })
}

func buildKnowledgeBaseDocumentStats(docs []PortableDocument) map[string]struct {
	total      int
	ready      int
	processing int
	failed     int
} {
	stats := make(map[string]struct {
		total      int
		ready      int
		processing int
		failed     int
	})

	for _, doc := range docs {
		current := stats[doc.KnowledgeBaseID]
		current.total++
		switch strings.ToLower(strings.TrimSpace(doc.Status)) {
		case "completed":
			current.ready++
		case "failed":
			current.failed++
		default:
			current.processing++
		}
		stats[doc.KnowledgeBaseID] = current
	}

	return stats
}

func mapKnowledgeBaseResponse(kb KnowledgeBase, docStats struct {
	total      int
	ready      int
	processing int
	failed     int
}) KnowledgeBaseResponse {
	progress := 0
	if docStats.total > 0 {
		progress = int(float64(docStats.ready) / float64(docStats.total) * 100)
	}

	return KnowledgeBaseResponse{
		ID:                      kb.ID,
		Name:                    kb.Name,
		Description:             kb.Description,
		Purpose:                 kb.Purpose,
		Subject:                 kb.Subject,
		LearningGoals:           kb.LearningGoals,
		StudyTime:               kb.StudyTime,
		CreationMethod:          kb.CreationMethod,
		FolderName:              kb.FolderName,
		DocumentCount:           docStats.total,
		ReadyDocumentCount:      docStats.ready,
		ProcessingDocumentCount: docStats.processing,
		FailedDocumentCount:     docStats.failed,
		Progress:                progress,
		CreatedAt:               kb.CreatedAt.UTC().Format(time.RFC3339),
		UpdatedAt:               kb.UpdatedAt.UTC().Format(time.RFC3339),
	}
}

func mapPortableDocumentResponse(doc PortableDocument) PortableDocumentResponse {
	return PortableDocumentResponse{
		ID:              doc.ID,
		KnowledgeBaseID: doc.KnowledgeBaseID,
		FileName:        doc.FileName,
		FileType:        doc.FileType,
		SizeBytes:       doc.SizeBytes,
		PageCount:       doc.PageCount,
		DocHash:         doc.DocHash,
		Status:          doc.Status,
		CreatedAt:       doc.CreatedAt.UTC().Format("2006-01-02 15:04"),
		FileURL:         "/documents/" + doc.ID + "/file",
	}
}

func ListKnowledgeBasesAPI(c *gin.Context, store PortableKnowledgeBaseStore) {
	kbs, err := store.ListKnowledgeBases()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to load knowledge bases"})
		return
	}

	docs, err := store.ListDocuments("")
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to load document metadata"})
		return
	}

	stats := buildKnowledgeBaseDocumentStats(docs)
	result := make([]KnowledgeBaseResponse, 0, len(kbs))
	for _, kb := range kbs {
		result = append(result, mapKnowledgeBaseResponse(kb, stats[kb.ID]))
	}

	c.JSON(http.StatusOK, gin.H{"knowledgeBases": result})
}

func GetKnowledgeBaseAPI(c *gin.Context, store PortableKnowledgeBaseStore) {
	id := strings.TrimSpace(c.Param("id"))
	if id == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid knowledge base id"})
		return
	}

	kb, err := store.GetKnowledgeBase(id)
	if err != nil {
		if errors.Is(err, ErrKnowledgeBaseNotFound) {
			c.JSON(http.StatusNotFound, gin.H{"error": "knowledge base not found"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to load knowledge base"})
		return
	}

	docs, err := store.ListDocuments(id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to load knowledge base documents"})
		return
	}

	stats := buildKnowledgeBaseDocumentStats(docs)
	c.JSON(http.StatusOK, gin.H{"knowledgeBase": mapKnowledgeBaseResponse(*kb, stats[id])})
}

func CreateKnowledgeBaseAPI(c *gin.Context, store PortableKnowledgeBaseStore) {
	var payload KnowledgeBasePayload
	if err := c.ShouldBindJSON(&payload); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid request payload"})
		return
	}

	name := strings.TrimSpace(payload.Name)
	if name == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "knowledge base name is required"})
		return
	}

	entry := KnowledgeBase{
		Name:           name,
		Description:    strings.TrimSpace(payload.Description),
		Purpose:        strings.TrimSpace(payload.Purpose),
		Subject:        strings.TrimSpace(payload.Subject),
		LearningGoals:  strings.TrimSpace(payload.LearningGoals),
		StudyTime:      strings.TrimSpace(payload.StudyTime),
		CreationMethod: strings.TrimSpace(payload.CreationMethod),
		FolderName:     strings.TrimSpace(payload.FolderName),
	}
	if err := store.CreateKnowledgeBase(&entry); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to create knowledge base"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"knowledgeBase": mapKnowledgeBaseResponse(entry, struct {
		total      int
		ready      int
		processing int
		failed     int
	}{})})
}

func DeleteKnowledgeBaseAPI(c *gin.Context, store PortableKnowledgeBaseStore, uploadsDir string) {
	id := strings.TrimSpace(c.Param("id"))
	if id == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid knowledge base id"})
		return
	}

	removedDocs, err := store.DeleteKnowledgeBase(id)
	if err != nil {
		if errors.Is(err, ErrKnowledgeBaseNotFound) {
			c.JSON(http.StatusNotFound, gin.H{"error": "knowledge base not found"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to delete knowledge base"})
		return
	}

	for _, doc := range removedDocs {
		_ = os.Remove(filepath.Join(uploadsDir, doc.KnowledgeBaseID, doc.StoredName))
	}
	_ = os.RemoveAll(filepath.Join(uploadsDir, id))

	c.JSON(http.StatusOK, gin.H{"deleted": true, "id": id})
}

func ListPortableDocumentsAPI(c *gin.Context, store PortableKnowledgeBaseStore) {
	kbID := strings.TrimSpace(c.Param("id"))
	if kbID == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid knowledge base id"})
		return
	}

	if _, err := store.GetKnowledgeBase(kbID); err != nil {
		if errors.Is(err, ErrKnowledgeBaseNotFound) {
			c.JSON(http.StatusNotFound, gin.H{"error": "knowledge base not found"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to load knowledge base"})
		return
	}

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

func UploadPortableDocumentAPI(c *gin.Context, store PortableKnowledgeBaseStore, uploadsDir string) {
	kbID := strings.TrimSpace(c.Param("id"))
	if kbID == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid knowledge base id"})
		return
	}

	if _, err := store.GetKnowledgeBase(kbID); err != nil {
		if errors.Is(err, ErrKnowledgeBaseNotFound) {
			c.JSON(http.StatusNotFound, gin.H{"error": "knowledge base not found"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to load knowledge base"})
		return
	}

	file, err := c.FormFile("file")
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "file is required"})
		return
	}

	safeDir := filepath.Join(uploadsDir, kbID)
	if err := os.MkdirAll(safeDir, os.ModePerm); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to prepare upload directory"})
		return
	}

	extension := strings.ToLower(filepath.Ext(file.Filename))
	storedName := uuid.NewString() + extension
	savePath := filepath.Join(safeDir, storedName)
	if err := c.SaveUploadedFile(file, savePath); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to save uploaded file"})
		return
	}

	doc := PortableDocument{
		KnowledgeBaseID: kbID,
		FileName:        file.Filename,
		StoredName:      storedName,
		FileType:        strings.TrimPrefix(extension, "."),
		SizeBytes:       file.Size,
		Status:          "completed",
	}

	if err := store.CreateDocument(&doc); err != nil {
		_ = os.Remove(savePath)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to save document metadata"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"document": mapPortableDocumentResponse(doc)})
}

func DeletePortableDocumentAPI(c *gin.Context, store PortableKnowledgeBaseStore, uploadsDir string) {
	id := strings.TrimSpace(c.Param("id"))
	if id == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid document id"})
		return
	}

	doc, err := store.DeleteDocument(id)
	if err != nil {
		if errors.Is(err, ErrPortableDocumentNotFound) {
			c.JSON(http.StatusNotFound, gin.H{"error": "document not found"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to delete document"})
		return
	}

	_ = os.Remove(filepath.Join(uploadsDir, doc.KnowledgeBaseID, doc.StoredName))

	c.JSON(http.StatusOK, gin.H{"deleted": true, "id": id})
}

func ServePortableDocumentAPI(c *gin.Context, store PortableKnowledgeBaseStore, uploadsDir string) {
	id := strings.TrimSpace(c.Param("id"))
	if id == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid document id"})
		return
	}

	doc, err := store.GetDocument(id)
	if err != nil {
		if errors.Is(err, ErrPortableDocumentNotFound) {
			c.JSON(http.StatusNotFound, gin.H{"error": "document not found"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to load document"})
		return
	}

	fullPath := filepath.Join(uploadsDir, doc.KnowledgeBaseID, doc.StoredName)
	if _, err := os.Stat(fullPath); err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "document file is missing"})
		return
	}

	if mimeType := mime.TypeByExtension("." + doc.FileType); mimeType != "" {
		c.Header("Content-Type", mimeType)
	}
	c.Header("Content-Disposition", "inline; filename=\""+sanitizeInlineFilename(doc.FileName)+"\"")
	c.File(fullPath)
}

func sanitizeInlineFilename(name string) string {
	replacer := strings.NewReplacer("\"", "", "\r", "", "\n", "")
	return replacer.Replace(name)
}
