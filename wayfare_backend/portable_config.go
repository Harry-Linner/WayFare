package main

import (
	"io"
	"log"
	"os"
	"path/filepath"
	"strconv"
	"strings"

	"github.com/gin-gonic/gin"
)

type AppConfig struct {
	FullMode      bool
	BaseDir       string
	DataDir       string
	LogDir        string
	Host          string
	PreferredPort int
	OpenBrowser   bool
}

func isGoRunExecutable(execPath string) bool {
	cleanPath := strings.ToLower(filepath.Clean(execPath))
	return strings.Contains(cleanPath, string(filepath.Separator)+"go-build")
}

func LoadAppConfig() (AppConfig, error) {
	execPath, err := os.Executable()
	if err != nil {
		return AppConfig{}, err
	}

	cwd, err := os.Getwd()
	if err != nil {
		return AppConfig{}, err
	}

	goRunMode := isGoRunExecutable(execPath)

	baseDir := strings.TrimSpace(os.Getenv("WAYFARE_BASE_DIR"))
	if baseDir == "" {
		if goRunMode {
			baseDir = cwd
		} else {
			baseDir = filepath.Dir(execPath)
		}
	}

	port := 37880
	if goRunMode {
		port = 8080
	}
	if rawPort := strings.TrimSpace(os.Getenv("WAYFARE_PORT")); rawPort != "" {
		if parsed, err := strconv.Atoi(rawPort); err == nil && parsed > 0 {
			port = parsed
		}
	}

	config := AppConfig{
		FullMode:      strings.TrimSpace(os.Getenv("WAYFARE_FULL_MODE")) == "1",
		BaseDir:       baseDir,
		DataDir:       filepath.Join(baseDir, "data"),
		LogDir:        filepath.Join(baseDir, "logs"),
		Host:          "127.0.0.1",
		PreferredPort: port,
		OpenBrowser:   !goRunMode,
	}

	if rawOpenBrowser := strings.TrimSpace(os.Getenv("WAYFARE_OPEN_BROWSER")); rawOpenBrowser != "" {
		config.OpenBrowser = rawOpenBrowser != "0"
	}

	for _, dir := range []string{config.DataDir, config.LogDir} {
		if err := os.MkdirAll(dir, os.ModePerm); err != nil {
			return AppConfig{}, err
		}
	}

	return config, nil
}

func SetupLogging(config AppConfig) (*os.File, error) {
	logFilePath := filepath.Join(config.LogDir, "app.log")
	logFile, err := os.OpenFile(logFilePath, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o666)
	if err != nil {
		return nil, err
	}

	writer := io.MultiWriter(os.Stdout, logFile)
	log.SetOutput(writer)
	log.SetFlags(log.LstdFlags | log.Lmicroseconds)
	gin.DefaultWriter = writer
	gin.DefaultErrorWriter = writer

	return logFile, nil
}
