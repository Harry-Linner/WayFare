package main

import (
	"time"
)

// User 用户表
type User struct {
	ID        uint      `gorm:"primaryKey" json:"id"`
	Username  string    `gorm:"unique" json:"username"`
	CreatedAt time.Time `json:"createdAt"`
}

// Project 项目表（一个项目可以包含多本书）
type Project struct {
	ID        uint      `gorm:"primaryKey" json:"id"`
	UserID    uint      `json:"userId"`
	Name      string    `json:"name"`
	CreatedAt time.Time `json:"createdAt"`
}

// Document 文档表（Go 和 Python 沟通的核心）
type Document struct {
	ID          uint      `gorm:"primaryKey" json:"id"`
	ProjectID   uint      `gorm:"index" json:"projectId"`
	FileName    string    `json:"filename"`
	FileURL     string    `json:"fileUrl"`              // 前端可访问 URL
	StoragePath string    `json:"-"`                    // 本地真实存储路径
	DocHash     string    `gorm:"index" json:"docHash"` // Python 计算出的唯一哈希
	Status      string    `json:"status"`               // pending, processing, completed, failed
	CreatedAt   time.Time `json:"createdAt"`
	UpdatedAt   time.Time `json:"updatedAt"`
}

// ChatMessage 聊天记录表
type ChatMessage struct {
	ID        uint      `gorm:"primaryKey" json:"id"`
	ProjectID uint      `gorm:"index" json:"projectId"`
	DocHash   *string   `gorm:"index" json:"docHash,omitempty"`
	Role      string    `gorm:"type:varchar(20)" json:"role"` // "user" 或 "assistant"
	Content   string    `json:"content"`
	CreatedAt time.Time `json:"timestamp"`
}
