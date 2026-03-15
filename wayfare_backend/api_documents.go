package main

import (
	"errors"
	"net/http"
	"os"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
)

type ParseStatusUpdateRequest struct {
	DocHash      string `json:"docHash"`
	Status       string `json:"status"`
	SegmentCount int    `json:"segmentCount"`
	Error        string `json:"error"`
}

func ListDocumentsAPI(c *gin.Context, db *gorm.DB) {
	projectID := parseProjectID(c.Query("projectId"))
	docHash := c.Query("docHash")

	query := db.Model(&Document{})
	if projectID != 0 {
		query = query.Where("project_id = ?", projectID)
	}
	if docHash != "" {
		query = query.Where("doc_hash = ?", docHash)
	}

	var documents []Document
	if err := query.Order("created_at desc").Find(&documents).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "获取文档列表失败"})
		return
	}

	c.JSON(http.StatusOK, documents)
}

func GetDocumentAPI(c *gin.Context, db *gorm.DB) {
	documentID, err := strconv.ParseUint(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "文档 ID 无效"})
		return
	}

	var document Document
	if err := db.First(&document, uint(documentID)).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			c.JSON(http.StatusNotFound, gin.H{"error": "文档不存在"})
			return
		}

		c.JSON(http.StatusInternalServerError, gin.H{"error": "获取文档失败"})
		return
	}

	c.JSON(http.StatusOK, document)
}

func DeleteDocumentAPI(c *gin.Context, db *gorm.DB) {
	documentID, err := strconv.ParseUint(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "文档 ID 无效"})
		return
	}

	var document Document
	if err := db.First(&document, uint(documentID)).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			c.JSON(http.StatusNotFound, gin.H{"error": "文档不存在"})
			return
		}

		c.JSON(http.StatusInternalServerError, gin.H{"error": "查询文档失败"})
		return
	}

	if document.StoragePath != "" {
		_ = os.Remove(document.StoragePath)
	}

	if err := db.Where("doc_hash = ?", document.DocHash).Delete(&ChatMessage{}).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "删除聊天记录失败"})
		return
	}

	if err := db.Delete(&document).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "删除文档失败"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "文档已删除"})
}

func ChatHistoryAPI(c *gin.Context, db *gorm.DB) {
	projectID := parseProjectID(c.Query("projectId"))
	docHash := c.Query("docHash")

	query := db.Model(&ChatMessage{})
	if projectID != 0 {
		query = query.Where("project_id = ?", projectID)
	}
	if docHash != "" {
		query = query.Where("doc_hash = ?", docHash)
	}

	var messages []ChatMessage
	if err := query.Order("created_at asc").Find(&messages).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "获取聊天记录失败"})
		return
	}

	c.JSON(http.StatusOK, messages)
}

func UpdateDocumentParseStatusAPI(c *gin.Context, db *gorm.DB) {
	var req ParseStatusUpdateRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "状态更新参数错误"})
		return
	}

	if req.DocHash == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "docHash 不能为空"})
		return
	}

	status := normalizeDocumentStatus(req.Status)
	if status == "" {
		status = "failed"
	}

	updates := map[string]interface{}{
		"status":     status,
		"updated_at": time.Now().UTC(),
	}

	if err := db.Model(&Document{}).Where("doc_hash = ?", req.DocHash).Updates(updates).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "更新文档状态失败"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message":      "文档状态已更新",
		"docHash":      req.DocHash,
		"status":       status,
		"segmentCount": req.SegmentCount,
		"error":        req.Error,
	})
}
