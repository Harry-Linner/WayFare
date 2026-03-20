package main

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
)

type BetaAuthConfig struct {
	Enabled        bool
	Configured     bool
	CookieName     string
	Secret         string
	AllowedUsers   map[string]string
	AllowedOrigins map[string]struct{}
}

func parseAllowedUsers(raw string) map[string]string {
	users := map[string]string{}
	for _, entry := range strings.Split(raw, ",") {
		trimmed := strings.TrimSpace(entry)
		if trimmed == "" {
			continue
		}
		parts := strings.SplitN(trimmed, ":", 2)
		if len(parts) != 2 {
			continue
		}
		username := strings.TrimSpace(parts[0])
		password := strings.TrimSpace(parts[1])
		if username == "" || password == "" {
			continue
		}
		users[username] = password
	}
	return users
}

func parseAllowedOrigins(raw string) map[string]struct{} {
	origins := map[string]struct{}{}
	defaults := []string{
		"http://127.0.0.1:4321",
		"http://localhost:4321",
	}

	entries := defaults
	if strings.TrimSpace(raw) != "" {
		entries = strings.Split(raw, ",")
	}

	for _, origin := range entries {
		trimmed := strings.TrimSpace(origin)
		if trimmed == "" {
			continue
		}
		origins[trimmed] = struct{}{}
	}

	return origins
}

func LoadBetaAuthConfig() BetaAuthConfig {
	enabled := strings.TrimSpace(os.Getenv("BETA_AUTH_ENABLED")) == "1"
	secret := strings.TrimSpace(os.Getenv("BETA_AUTH_SECRET"))
	allowedUsers := parseAllowedUsers(os.Getenv("BETA_ALLOWED_USERS"))

	return BetaAuthConfig{
		Enabled:        enabled,
		Configured:     !enabled || (secret != "" && len(allowedUsers) > 0),
		CookieName:     strings.TrimSpace(firstNonEmpty(os.Getenv("BETA_AUTH_COOKIE_NAME"), "wayfare_beta_auth")),
		Secret:         secret,
		AllowedUsers:   allowedUsers,
		AllowedOrigins: parseAllowedOrigins(os.Getenv("WAYFARE_ALLOWED_ORIGINS")),
	}
}

func firstNonEmpty(values ...string) string {
	for _, value := range values {
		if strings.TrimSpace(value) != "" {
			return value
		}
	}
	return ""
}

func base64URLDecodeString(input string) (string, error) {
	bytes, err := base64.RawURLEncoding.DecodeString(input)
	if err != nil {
		return "", err
	}
	return string(bytes), nil
}

func signBetaPayload(secret string, payload string) string {
	mac := hmac.New(sha256.New, []byte(secret))
	mac.Write([]byte(payload))
	return base64.RawURLEncoding.EncodeToString(mac.Sum(nil))
}

func verifyBetaSessionToken(config BetaAuthConfig, token string) (string, bool) {
	if !config.Enabled {
		return "anonymous", true
	}
	if !config.Configured || strings.TrimSpace(token) == "" {
		return "", false
	}

	parts := strings.Split(token, ".")
	if len(parts) != 3 {
		return "", false
	}

	payload := parts[0] + "." + parts[1]
	expected := signBetaPayload(config.Secret, payload)
	if !hmac.Equal([]byte(expected), []byte(parts[2])) {
		return "", false
	}

	expiresAt, err := strconv.ParseInt(parts[1], 10, 64)
	if err != nil || expiresAt <= time.Now().Unix() {
		return "", false
	}

	username, err := base64URLDecodeString(parts[0])
	if err != nil {
		return "", false
	}

	if _, ok := config.AllowedUsers[username]; !ok {
		return "", false
	}

	return username, true
}

func isPublicAPIRoute(path string) bool {
	switch path {
	case "/healthz":
		return true
	default:
		return false
	}
}

func applyCORSHeaders(c *gin.Context, config BetaAuthConfig) {
	origin := strings.TrimSpace(c.GetHeader("Origin"))
	if origin != "" {
		if _, ok := config.AllowedOrigins[origin]; ok {
			c.Writer.Header().Set("Access-Control-Allow-Origin", origin)
			c.Writer.Header().Set("Vary", "Origin")
			c.Writer.Header().Set("Access-Control-Allow-Credentials", "true")
		}
	}

	c.Writer.Header().Set("Access-Control-Allow-Headers", "Content-Type")
	c.Writer.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
}

func BetaAuthMiddleware(config BetaAuthConfig) gin.HandlerFunc {
	return func(c *gin.Context) {
		applyCORSHeaders(c, config)

		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}

		if !config.Enabled || isPublicAPIRoute(c.Request.URL.Path) {
			c.Next()
			return
		}

		if !config.Configured {
			c.AbortWithStatusJSON(503, gin.H{"error": "beta auth is enabled but not configured"})
			return
		}

		token, err := c.Cookie(config.CookieName)
		if err != nil {
			c.AbortWithStatusJSON(401, gin.H{"error": "beta auth required"})
			return
		}

		username, ok := verifyBetaSessionToken(config, token)
		if !ok {
			c.AbortWithStatusJSON(401, gin.H{"error": "beta session is invalid or expired"})
			return
		}

		c.Set("betaUser", username)
		c.Next()
	}
}

func betaUserForLog(c *gin.Context) string {
	if value, exists := c.Get("betaUser"); exists {
		if username, ok := value.(string); ok {
			return username
		}
	}
	return ""
}

func hashForLog(value string) string {
	trimmed := strings.TrimSpace(value)
	if trimmed == "" {
		return ""
	}
	sum := sha256.Sum256([]byte(trimmed))
	return hex.EncodeToString(sum[:8])
}
