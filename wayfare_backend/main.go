package main

import (
	"fmt"

	"github.com/gin-gonic/gin"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

func main() {
	dsn := "postgresql://luckdd:123456@localhost:5432/wayfare_dbz"
	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})
	if err != nil {
		panic("无法连接数据库: " + err.Error())
	}

	db.AutoMigrate(&User{}, &Project{}, &Document{}, &ChatMessage{})
	fmt.Println("业务数据库表结构同步完成")

	var count int64
	db.Model(&Project{}).Count(&count)
	if count == 0 {
		db.Create(&Project{Name: "默认测试项目", UserID: 1})
	}

	InitPythonSidecar(db)

	r := gin.Default()
	r.Use(func(c *gin.Context) {
		c.Writer.Header().Set("Access-Control-Allow-Origin", "http://localhost:4321")
		c.Writer.Header().Set("Access-Control-Allow-Headers", "Content-Type")
		c.Writer.Header().Set("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}
		c.Next()
	})

	r.POST("/upload", func(c *gin.Context) { UploadDocumentAPI(c, db) })
	r.POST("/chat", func(c *gin.Context) { ChatAPI(c, db) })
	r.GET("/documents", func(c *gin.Context) { ListDocumentsAPI(c, db) })
	r.DELETE("/documents/:id", func(c *gin.Context) { DeleteDocumentAPI(c, db) })
	r.GET("/documents/:id/file", func(c *gin.Context) { ServeDocumentFileAPI(c, db) })

	fmt.Println("Go API 网关已启动: http://localhost:8080")
	r.Run(":8080")
}
