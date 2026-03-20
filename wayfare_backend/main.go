package main

import (
        "encoding/base64"
        "strconv"
	"fmt"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

func main() {
	config, err := LoadAppConfig()
	if err != nil {
		log.Fatalf("failed to load config: %v", err)
	}

	logFile, err := SetupLogging(config)
	if err != nil {
		log.Fatalf("failed to setup logging: %v", err)
	}
	defer logFile.Close()

	if config.FullMode {
		if err := runFullMode(config); err != nil {
			log.Fatalf("full mode failed: %v", err)
		}
		return
	}

	if err := runPortableMode(config); err != nil {
		log.Fatalf("portable mode failed: %v", err)
	}
}

func runPortableMode(config AppConfig) error {
	store := NewJSONScheduleStore(filepath.Join(config.DataDir, "schedules.json"))
	kbStore := NewJSONKnowledgeBaseStore(filepath.Join(config.DataDir, "knowledge_bases.json"))
	chatStore := NewInMemoryChatHistoryStore(10)
	profileStore := NewProfileStore(filepath.Join(config.DataDir, "profiles"))
	feedbackStore := NewJSONFeedbackStore(filepath.Join(config.DataDir, "feedback.jsonl"))
	uploadsDir := filepath.Join(config.BaseDir, "uploads")

	if err := InitPythonSidecar(nil, kbStore); err != nil {
		return err
	}

	router := newBaseRouter()
	RegisterScheduleRoutes(router, store)
	RegisterPortableKnowledgeBaseRoutes(router, kbStore, uploadsDir)
	RegisterPortableUnifiedAPIRoutes(router, kbStore, uploadsDir, chatStore, profileStore)
	RegisterProfileRoutes(router, profileStore, kbStore)
	RegisterFeedbackRoutes(router, feedbackStore)
	router.GET("/", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status":  "ok",
			"mode":    "portable-api",
			"message": "Portable UI has been removed. Use the Astro frontend for the interface.",
		})
	})
	router.GET("/schedule-board", func(c *gin.Context) {
		c.JSON(http.StatusGone, gin.H{
			"error":   "portable schedule board UI has been removed",
			"message": "Start the Astro frontend instead of using the old embedded test UI.",
		})
	})
	router.GET("/healthz", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status": "ok",
			"mode":   "portable",
		})
	})
        router.POST("/api/login", func(c *gin.Context) {
		var req struct {
			Username string `json:"username"`
			Password string `json:"password"`
		}
		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "invalid json"})
			return
		}

		authCfg := LoadBetaAuthConfig()
		// 校验账号密码是否在 BETA_ALLOWED_USERS 里
		storedPass, ok := authCfg.AllowedUsers[req.Username]
		if !ok || storedPass != req.Password {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "invalid credentials"})
			return
		}

		// 严格按照 beta_auth.go 的签名逻辑生成 Token
		expires := time.Now().Add(7 * 24 * time.Hour).Unix()
		payload := base64.RawURLEncoding.EncodeToString([]byte(req.Username)) + "." + strconv.FormatInt(expires, 10)
		signature := signBetaPayload(authCfg.Secret, payload)
		token := payload + "." + signature

		// 设置 Cookie (注意：这里要根据你的域名调整 Secure/SameSite)
		c.SetCookie(authCfg.CookieName, token, 7*24*3600, "/", "", false, true)
		c.JSON(http.StatusOK, gin.H{
			"message": "login success",
			"user":    req.Username,
		})
	})
	return serveRouter(router, config, "portable")
}

func runFullMode(config AppConfig) error {
	dsn := strings.TrimSpace(os.Getenv("DB_DSN"))
	if dsn == "" {
		dsn = "postgresql://luckdd:123456@localhost:5432/wayfare_dbz"
	}
	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})
	if err != nil {
		return err
	}

	if err := db.AutoMigrate(&User{}, &Project{}, &Document{}, &ChatMessage{}, &Schedule{}); err != nil {
		return err
	}

	var count int64
	db.Model(&Project{}).Count(&count)
	if count == 0 {
		db.Create(&Project{Name: "WayFare Default Project", UserID: 1})
	}

	if err := InitPythonSidecar(db, nil); err != nil {
		return err
	}

	store := NewJSONScheduleStore(filepath.Join(config.DataDir, "schedules.json"))
	profileStore := NewProfileStore(filepath.Join(config.DataDir, "profiles"))
	feedbackStore := NewJSONFeedbackStore(filepath.Join(config.DataDir, "feedback.jsonl"))
	router := newBaseRouter()
	router.POST("/upload", func(c *gin.Context) { UploadDocumentAPI(c, db) })
	router.POST("/chat", func(c *gin.Context) { ChatAPI(c, db) })
	router.GET("/documents", func(c *gin.Context) { ListDocumentsAPI(c, db) })
	router.DELETE("/documents/:id", func(c *gin.Context) { DeleteDocumentAPI(c, db) })
	router.GET("/documents/:id/file", func(c *gin.Context) { ServeDocumentFileAPI(c, db) })
	RegisterScheduleRoutes(router, store)
	RegisterProfileRoutes(router, profileStore, nil)
	RegisterFeedbackRoutes(router, feedbackStore)
	router.GET("/healthz", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status": "ok",
			"mode":   "full",
		})
	})

	return serveRouter(router, config, "full")
}

func newBaseRouter() *gin.Engine {
	router := gin.Default()
	router.Use(BetaAuthMiddleware(LoadBetaAuthConfig()))
	return router
}

func serveRouter(router *gin.Engine, config AppConfig, mode string) error {
	listener, port, err := FindAvailableListener(config.Host, config.PreferredPort, 20)
	if err != nil {
		return err
	}

	url := fmt.Sprintf("http://%s:%d", config.Host, port)
	log.Printf("WayFare %s mode is running at %s", mode, url)
	log.Printf("Data directory: %s", config.DataDir)
	log.Printf("Log directory: %s", config.LogDir)

	if config.OpenBrowser {
		go func() {
			time.Sleep(750 * time.Millisecond)
			if err := OpenBrowser(url); err != nil {
				log.Printf("failed to open browser automatically: %v", err)
			}
		}()
	}

	return router.RunListener(listener)
}
