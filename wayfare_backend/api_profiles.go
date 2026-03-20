package main

import (
	"net/http"
	"strings"

	"github.com/gin-gonic/gin"
)

type ProfilePayload struct {
	Content string `json:"content"`
}

func RegisterProfileRoutes(router gin.IRouter, profileStore *ProfileStore, kbStore PortableKnowledgeBaseStore) {
	if profileStore == nil {
		return
	}

	router.GET("/profiles/global", func(c *gin.Context) {
		GetGlobalProfileAPI(c, profileStore)
	})
	router.PUT("/profiles/global", func(c *gin.Context) {
		UpdateGlobalProfileAPI(c, profileStore)
	})
	router.GET("/knowledge-bases/:id/profile", func(c *gin.Context) {
		GetKnowledgeBaseProfileAPI(c, profileStore, kbStore)
	})
	router.PUT("/knowledge-bases/:id/profile", func(c *gin.Context) {
		UpdateKnowledgeBaseProfileAPI(c, profileStore, kbStore)
	})
}

func GetGlobalProfileAPI(c *gin.Context, store *ProfileStore) {
	profile, err := store.GetGlobalProfile()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to load global profile"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"profile": profile})
}

func UpdateGlobalProfileAPI(c *gin.Context, store *ProfileStore) {
	var payload ProfilePayload
	if err := c.ShouldBindJSON(&payload); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid request payload"})
		return
	}

	profile, err := store.SaveGlobalProfile(payload.Content)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to save global profile"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"profile": profile})
}

func validateKnowledgeBaseProfileTarget(id string, kbStore PortableKnowledgeBaseStore) error {
	if kbStore == nil {
		return nil
	}
	_, err := kbStore.GetKnowledgeBase(id)
	return err
}

func GetKnowledgeBaseProfileAPI(c *gin.Context, store *ProfileStore, kbStore PortableKnowledgeBaseStore) {
	id := strings.TrimSpace(c.Param("id"))
	if id == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid knowledge base id"})
		return
	}

	if err := validateKnowledgeBaseProfileTarget(id, kbStore); err != nil {
		if err == ErrKnowledgeBaseNotFound {
			c.JSON(http.StatusNotFound, gin.H{"error": "knowledge base not found"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to validate knowledge base"})
		return
	}

	profile, err := store.GetKnowledgeBaseProfile(id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to load knowledge base profile"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"profile": profile})
}

func UpdateKnowledgeBaseProfileAPI(c *gin.Context, store *ProfileStore, kbStore PortableKnowledgeBaseStore) {
	id := strings.TrimSpace(c.Param("id"))
	if id == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid knowledge base id"})
		return
	}

	if err := validateKnowledgeBaseProfileTarget(id, kbStore); err != nil {
		if err == ErrKnowledgeBaseNotFound {
			c.JSON(http.StatusNotFound, gin.H{"error": "knowledge base not found"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to validate knowledge base"})
		return
	}

	var payload ProfilePayload
	if err := c.ShouldBindJSON(&payload); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid request payload"})
		return
	}

	profile, err := store.SaveKnowledgeBaseProfile(id, payload.Content)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to save knowledge base profile"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"profile": profile})
}
