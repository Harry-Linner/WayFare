package main

import (
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"gorm.io/gorm"
)

const defaultProjectID uint = 1

func UploadDocumentAPI(c *gin.Context, db *gorm.DB) {
	file, err := c.FormFile("file")
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "请上传文件"})
		return
	}

	const maxFileSize = 50 * 1024 * 1024
	if file.Size > maxFileSize {
		c.JSON(http.StatusBadRequest, gin.H{"error": "文件大小超过 50MB 限制"})
		return
	}

	projectID := parseProjectID(c.PostForm("projectId"))
	uploadDir := getEnv("UPLOAD_DIR", "./uploads")

	if err := os.MkdirAll(uploadDir, 0755); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "创建上传目录失败"})
		return
	}

	ext := filepath.Ext(file.Filename)
	safeFilename := uuid.New().String() + ext
	savePath := filepath.Join(uploadDir, safeFilename)

	if err := c.SaveUploadedFile(file, savePath); err != nil {
		log.Printf("❌ 文件保存失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "文件保存失败"})
		return
	}

	absPath, err := filepath.Abs(savePath)
	if err != nil {
		log.Printf("❌ 获取绝对路径失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "路径处理失败"})
		return
	}

	resp, err := CallPythonViaNetwork("parse", map[string]interface{}{
		"path":     absPath,
		"filename": file.Filename,
		"size":     file.Size,
	})
	if err != nil {
		log.Printf("❌ Python 解析失败: %v", err)
		c.JSON(http.StatusBadGateway, gin.H{"error": "AI 解析失败: " + err.Error()})
		return
	}

	docHash, ok := resp.Data["docHash"].(string)
	if !ok || docHash == "" {
		log.Printf("❌ 无效的 docHash 响应: %+v", resp.Data)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "AI 响应格式错误"})
		return
	}

	status := normalizeDocumentStatus(valueAsString(resp.Data["status"]))
	if status == "" {
		status = "processing"
	}

	document := Document{
		ProjectID:   projectID,
		FileName:    file.Filename,
		FileURL:     "/uploads/" + safeFilename,
		StoragePath: absPath,
		DocHash:     docHash,
		Status:      status,
		CreatedAt:   time.Now().UTC(),
		UpdatedAt:   time.Now().UTC(),
	}

	if err := db.Create(&document).Error; err != nil {
		log.Printf("❌ 数据库写入失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "数据库操作失败"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"id":        document.ID,
		"projectId": document.ProjectID,
		"filename":  document.FileName,
		"fileUrl":   document.FileURL,
		"docHash":   document.DocHash,
		"status":    document.Status,
		"createdAt": document.CreatedAt,
		"updatedAt": document.UpdatedAt,
		"message":   "文件上传成功，Python 正在解析",
	})
}

func normalizeDocumentStatus(status string) string {
	switch status {
	case "pending", "processing", "completed", "failed":
		return status
	default:
		return ""
	}
}

func parseProjectID(raw string) uint {
	if raw == "" {
		return defaultProjectID
	}

	parsed, err := strconv.ParseUint(raw, 10, 64)
	if err != nil || parsed == 0 {
		return defaultProjectID
	}

	return uint(parsed)
}

func valueAsString(value interface{}) string {
	stringValue, _ := value.(string)
	return stringValue
}
