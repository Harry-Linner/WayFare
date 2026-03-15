package main

import (
	"net/http"
	"os"
	"time"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
)

func HealthAPI(c *gin.Context, db *gorm.DB) {
	pythonHealthy := CheckPythonAIHealth() == nil

	status := "ok"
	if !isDatabaseHealthy(db) {
		status = "degraded"
	}

	c.JSON(http.StatusOK, gin.H{
		"status":    status,
		"service":   "go-backend",
		"timestamp": time.Now().UTC().Format(time.RFC3339),
		"pythonAI":  pythonHealthy,
	})
}

func SystemStatusAPI(c *gin.Context, db *gorm.DB) {
	pythonHealthy := CheckPythonAIHealth() == nil
	databaseHealthy := isDatabaseHealthy(db)

	c.JSON(http.StatusOK, gin.H{
		"services": gin.H{
			"database":    databaseHealthy,
			"redis":       false,
			"python_ai":   pythonHealthy,
			"cpp_sandbox": false,
		},
		"uptime":    int(time.Since(serverStartedAt).Seconds()),
		"version":   valueOrDefault(os.Getenv("WAYFARE_VERSION"), "0.1.0"),
		"timestamp": time.Now().UTC().Format(time.RFC3339),
	})
}

func isDatabaseHealthy(db *gorm.DB) bool {
	if db == nil {
		return false
	}

	sqlDB, err := db.DB()
	if err != nil {
		return false
	}

	return sqlDB.Ping() == nil
}

func valueOrDefault(value, defaultValue string) string {
	if value != "" {
		return value
	}

	return defaultValue
}
