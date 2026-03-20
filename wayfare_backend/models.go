package main

import "time"

type User struct {
	ID        uint   `gorm:"primaryKey"`
	Username  string `gorm:"unique"`
	CreatedAt time.Time
}

type Project struct {
	ID        uint `gorm:"primaryKey"`
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

type Schedule struct {
	ID                    uint   `gorm:"primaryKey"`
	ProjectID             uint   `gorm:"index"`
	Title                 string `gorm:"size:255"`
	Description           string `gorm:"type:text"`
	ScheduledFor          time.Time
	ReminderOffsetMinutes int
	RepeatRule            string `gorm:"type:varchar(32);default:'none'"`
	Status                string `gorm:"type:varchar(32);default:'pending';index"`
	SnoozedUntil          *time.Time
	LastNotifiedAt        *time.Time
	LastCompletedAt       *time.Time
	CreatedAt             time.Time
	UpdatedAt             time.Time
}
