package main

import (
	"net/http"
	"os"
	"path/filepath"
	"strings"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"gorm.io/gorm"
)

func UploadDocumentAPI(c *gin.Context, db *gorm.DB) {
	file, err := c.FormFile("file")
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "请上传文件"})
		return
	}

	kbID := strings.TrimSpace(c.PostForm("kbId"))
	if kbID == "" {
		kbID = "default"
	}
	relativePath := strings.TrimSpace(c.PostForm("relativePath"))

	if err := os.MkdirAll("./uploads", os.ModePerm); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "无法创建上传目录"})
		return
	}

	safeFilename := uuid.New().String() + filepath.Ext(file.Filename)
	savePath := filepath.Join("./uploads", safeFilename)
	if err := c.SaveUploadedFile(file, savePath); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "文件保存失败"})
		return
	}

	absPath, _ := filepath.Abs(savePath)
	resp, err := CallPython("parse", map[string]interface{}{
		"path": absPath,
	})
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	docHash, _ := resp.Data["docHash"].(string)
	pageCount := 0
	if raw, ok := resp.Data["pageCount"]; ok {
		switch v := raw.(type) {
		case float64:
			pageCount = int(v)
		case int:
			pageCount = v
		}
	}

	displayName := file.Filename
	if relativePath != "" {
		displayName = relativePath
	}

	doc := Document{
		ProjectID:       1,
		KnowledgeBaseID: kbID,
		FileName:        displayName,
		FileURL:         absPath,
		FileType:        strings.TrimPrefix(strings.ToLower(filepath.Ext(file.Filename)), "."),
		PageCount:       pageCount,
		DocHash:         docHash,
		Status:          "processing",
	}
	if err := db.Create(&doc).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "文档记录保存失败"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message":    "上传成功，AI 正在解析",
		"docHash":    docHash,
		"documentId": doc.ID,
		"pageCount":  pageCount,
		"status":     doc.Status,
	})
}
