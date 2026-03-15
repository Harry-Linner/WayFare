package main

import (
	"fmt"
	"log"
	"os"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

var serverStartedAt = time.Now().UTC()

func main() {
	// 加载环境变量
	if err := godotenv.Load(); err != nil {
		log.Println("⚠️  未找到 .env 文件，使用默认配置")
	}

	// 数据库配置
	dbHost := getEnv("DB_HOST", "localhost")
	dbPort := getEnv("DB_PORT", "5432")
	dbName := getEnv("DB_NAME", "wayfare_db")
	dbUser := getEnv("DB_USER", "luckdd")
	dbPassword := getEnv("DB_PASSWORD", "123456")

	// 构建DSN
	dsn := fmt.Sprintf("postgresql://%s:%s@%s:%s/%s", dbUser, dbPassword, dbHost, dbPort, dbName)

	// 连接数据库
	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})
	if err != nil {
		log.Fatalf("❌ 数据库连接失败: %v", err)
	}

	// 自动迁移表结构
	if err := db.AutoMigrate(&User{}, &Project{}, &Document{}, &ChatMessage{}); err != nil {
		log.Fatalf("❌ 数据库迁移失败: %v", err)
	}
	log.Println("✅ 数据库表结构同步完成")

	// 插入默认数据
	var count int64
	db.Model(&Project{}).Count(&count)
	if count == 0 {
		if err := db.Create(&Project{Name: "默认测试项目", UserID: 1}).Error; err != nil {
			log.Printf("⚠️  插入默认项目失败: %v", err)
		}
	}

	// 检查Python AI服务是否可用
	log.Println("🔍 检查Python AI服务状态...")
	if err := CheckPythonAIHealth(); err != nil {
		log.Printf("⚠️  Python AI服务暂时不可用: %v", err)
		log.Println("ℹ️  服务将在Python AI可用后正常工作")
	} else {
		log.Println("✅ Python AI服务连接正常")
	}

	// 配置Gin
	gin.SetMode(gin.ReleaseMode)
	r := gin.Default()

	uploadDir := getEnv("UPLOAD_DIR", "./uploads")
	if err := os.MkdirAll(uploadDir, 0755); err != nil {
		log.Fatalf("❌ 创建上传目录失败: %v", err)
	}

	// CORS配置
	r.Use(func(c *gin.Context) {
		origin := os.Getenv("CORS_ORIGIN")
		if origin == "" {
			origin = "*"
		}
		c.Writer.Header().Set("Access-Control-Allow-Origin", origin)
		c.Writer.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		c.Writer.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")

		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}
		c.Next()
	})

	r.Static("/uploads", uploadDir)

	// 注册路由
	api := r.Group("/api")
	{
		api.POST("/upload", func(c *gin.Context) { UploadDocumentAPI(c, db) })
		api.POST("/chat", func(c *gin.Context) { ChatAPI(c, db) })
		api.GET("/chat/history", func(c *gin.Context) { ChatHistoryAPI(c, db) })
		api.GET("/documents", func(c *gin.Context) { ListDocumentsAPI(c, db) })
		api.GET("/documents/:id", func(c *gin.Context) { GetDocumentAPI(c, db) })
		api.DELETE("/documents/:id", func(c *gin.Context) { DeleteDocumentAPI(c, db) })
		api.GET("/status", func(c *gin.Context) { SystemStatusAPI(c, db) })
		api.POST("/internal/parse-status", func(c *gin.Context) { UpdateDocumentParseStatusAPI(c, db) })
	}

	// 兼容旧路由
	r.POST("/upload", func(c *gin.Context) { UploadDocumentAPI(c, db) })
	r.POST("/chat", func(c *gin.Context) { ChatAPI(c, db) })

	// 健康检查
	r.GET("/health", func(c *gin.Context) {
		HealthAPI(c, db)
	})

	// 启动服务
	port := getEnv("GO_BACKEND_PORT", "8080")
	log.Printf("🚀 Go API 网关启动中，端口: %s", port)
	if err := r.Run(":" + port); err != nil {
		log.Fatalf("❌ 服务启动失败: %v", err)
	}
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
