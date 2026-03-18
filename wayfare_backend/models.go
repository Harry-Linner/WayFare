package main

import "time"

type User struct {
	ID        uint   `gorm:"primaryKey"`
	Username  string `gorm:"unique"`
	CreatedAt time.Time
}

type Project struct {
	ID        uint   `gorm:"primaryKey"`
	UserID    uint
	Name      string
	CreatedAt time.Time
}

type Document struct {
	ID              uint   `gorm:"primaryKey"`
	ProjectID       uint   `gorm:"index"`
	KnowledgeBaseID string `gorm:"index"`
	FileName        string
	FileURL         string
	FileType        string
	PageCount       int
	DocHash         string `gorm:"index"`
	Status          string
	CreatedAt       time.Time
}

type ChatMessage struct {
	ID        uint   `gorm:"primaryKey"`
	ProjectID uint   `gorm:"index"`
	Role      string `gorm:"type:varchar(20)"`
	Content   string
	CreatedAt time.Time
}
