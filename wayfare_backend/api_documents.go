package main

import (
	"net/http"
	"os"
	"strconv"
	"strings"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
)

type DocumentResponse struct {
	ID              uint   `json:"id"`
	KnowledgeBaseID string `json:"knowledgeBaseId"`
	FileName        string `json:"fileName"`
	FileType        string `json:"fileType"`
	PageCount       int    `json:"pageCount"`
	Status          string `json:"status"`
	DocHash         string `json:"docHash"`
	CreatedAt       string `json:"createdAt"`
	FileURL         string `json:"fileUrl"`
}

func mapDocumentResponse(doc Document) DocumentResponse {
	return DocumentResponse{
		ID:              doc.ID,
		KnowledgeBaseID: doc.KnowledgeBaseID,
		FileName:        doc.FileName,
		FileType:        doc.FileType,
		PageCount:       doc.PageCount,
		Status:          doc.Status,
		DocHash:         doc.DocHash,
		CreatedAt:       doc.CreatedAt.Format("2006-01-02 15:04"),
		FileURL:         "/documents/" + strconv.FormatUint(uint64(doc.ID), 10) + "/file",
	}
}

func ListDocumentsAPI(c *gin.Context, db *gorm.DB) {
	kbID := strings.TrimSpace(c.Query("kbId"))
	if kbID == "" {
		kbID = "default"
	}

	var docs []Document
	query := db.Order("created_at desc")
	if kbID == "default" {
		query = query.Where("knowledge_base_id = ? OR knowledge_base_id = '' OR knowledge_base_id IS NULL", kbID)
	} else {
		query = query.Where("knowledge_base_id = ?", kbID)
	}

	if err := query.Find(&docs).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "获取文档列表失败"})
		return
	}

	result := make([]DocumentResponse, 0, len(docs))
	for _, doc := range docs {
		result = append(result, mapDocumentResponse(doc))
	}

	c.JSON(http.StatusOK, gin.H{"documents": result})
}

func DeleteDocumentAPI(c *gin.Context, db *gorm.DB) {
	id, err := strconv.Atoi(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的文档 ID"})
		return
	}

	var doc Document
	if err := db.First(&doc, id).Error; err != nil {
		if err == gorm.ErrRecordNotFound {
			c.JSON(http.StatusNotFound, gin.H{"error": "文档不存在"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": "查询文档失败"})
		return
	}

	if doc.FileURL != "" {
		_ = os.Remove(doc.FileURL)
	}

	if err := db.Delete(&doc).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "删除文档失败"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"deleted": true, "id": doc.ID})
}

func ServeDocumentFileAPI(c *gin.Context, db *gorm.DB) {
	id, err := strconv.Atoi(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的文档 ID"})
		return
	}

	var doc Document
	if err := db.First(&doc, id).Error; err != nil {
		if err == gorm.ErrRecordNotFound {
			c.JSON(http.StatusNotFound, gin.H{"error": "文档不存在"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": "查询文档失败"})
		return
	}

	if _, err := os.Stat(doc.FileURL); err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "文件不存在"})
		return
	}

	c.File(doc.FileURL)
}
