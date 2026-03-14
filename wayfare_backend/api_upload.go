package main

import (
	"net/http"
	"os"
	"path/filepath"

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

	// 确保上传目录存在
	os.MkdirAll("./uploads", os.ModePerm)

	// 🚀 【核心修复】：生成纯英文的 UUID 作为物理文件名，彻底消灭乱码和安全隐患！
	safeFilename := uuid.New().String() + filepath.Ext(file.Filename)
	savePath := filepath.Join("./uploads", safeFilename)

	// 保存文件到本地 (此时存下的是类似 uploads/550e8400-e29b...pdf)
	if err := c.SaveUploadedFile(file, savePath); err != nil {
		c.JSON(500, gin.H{"error": "文件保存失败"})
		return
	}

	// 此时的 absPath 是绝对纯净的英文路径，Python 绝对不会报错
	absPath, _ := filepath.Abs(savePath)
	resp, err := CallPython("parse", map[string]interface{}{
		"path": absPath,
	})

	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}

	docHash := resp.Data["docHash"].(string)

	// 落盘到 Go 的业务数据库
	doc := Document{
		ProjectID: 1,
		FileName:  file.Filename, // 数据库里依然存原始中文名，等 React 前端来请求时展示用
		FileURL:   absPath,       // 物理路径是安全的 UUID 路径
		DocHash:   docHash,
		Status:    "processing",
	}
	db.Create(&doc)

	c.JSON(http.StatusOK, gin.H{
		"message": "上传成功，AI正在阅读",
		"docHash": docHash,
	})
}
