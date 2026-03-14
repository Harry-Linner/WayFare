package main

import (
	"time"
)

// User 用户表
type User struct {
	ID        uint   `gorm:"primaryKey"`
	Username  string `gorm:"unique"`
	CreatedAt time.Time
}

// Project 项目表（一个项目可以包含多本书）
type Project struct {
	ID        uint   `gorm:"primaryKey"`
	UserID    uint
	Name      string
	CreatedAt time.Time
}

// Document 文档表（Go 和 Python 沟通的核心）
type Document struct {
	ID        uint   `gorm:"primaryKey"`
	ProjectID uint   `gorm:"index"`
	FileName  string
	FileURL   string // 本地路径或 MinIO 地址
	DocHash   string `gorm:"index"` // Python 计算出的唯一哈希
	Status    string // pending, processing, completed
	CreatedAt time.Time
}

// ChatMessage 聊天记录表
type ChatMessage struct {
	ID        uint   `gorm:"primaryKey"`
	ProjectID uint   `gorm:"index"`
	Role      string `gorm:"type:varchar(20)"` // "user" 或 "assistant"
	Content   string
	CreatedAt time.Time
}