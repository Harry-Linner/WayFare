package main

import (
	"fmt"

	"github.com/gin-gonic/gin"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

func main() {
	// 1. 连接与 Python 共用的 PostgreSQL 数据库
	// 请确保这里的账号密码和 Python .env 里的一致
	dsn := "postgresql://luckdd:123456@localhost:5432/wayfare_db"
	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})
	if err != nil {
		panic("无法连接数据库: " + err.Error())
	}

	// 自动建表！(如果表不存在，GORM 会自动创建这4张业务表)
	db.AutoMigrate(&User{}, &Project{}, &Document{}, &ChatMessage{})
	fmt.Println("✅ 业务数据库表结构同步完成")

	// 插入一条默认的项目测试数据 (如果不存在的话)
	var count int64
	db.Model(&Project{}).Count(&count)
	if count == 0 {
		db.Create(&Project{Name: "默认测试项目", UserID: 1})
	}

	// 2. 挂载启动 Python 侧车进程
	InitPythonSidecar()

	// 3. 启动 Gin Web 框架
	r := gin.Default()

	// 跨域处理 (方便 React 联调)
	r.Use(func(c *gin.Context) {
		c.Writer.Header().Set("Access-Control-Allow-Origin", "*")
		c.Writer.Header().Set("Access-Control-Allow-Headers", "Content-Type")
		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}
		c.Next()
	})

	// 注册路由
	r.POST("/upload", func(c *gin.Context) { UploadDocumentAPI(c, db) })
	r.POST("/chat", func(c *gin.Context) { ChatAPI(c, db) })

	// 4. 监听 8080 端口，开始服务
	fmt.Println("⚡ Go API 网关已启动: http://localhost:8080")
	r.Run(":8080")
}
