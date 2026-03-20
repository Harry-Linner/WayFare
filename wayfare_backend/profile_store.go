package main

import (
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"
)

type PromptProfile struct {
	Scope           string `json:"scope"`
	KnowledgeBaseID string `json:"knowledgeBaseId,omitempty"`
	Content         string `json:"content"`
	Exists          bool   `json:"exists"`
	UpdatedAt       string `json:"updatedAt,omitempty"`
}

type ProfileStore struct {
	baseDir string
	mu      sync.Mutex
}

func NewProfileStore(baseDir string) *ProfileStore {
	return &ProfileStore{baseDir: baseDir}
}

func sanitizeProfileFileName(id string) string {
	replacer := strings.NewReplacer("/", "_", "\\", "_", ":", "_", "..", "_")
	return replacer.Replace(strings.TrimSpace(id))
}

func (store *ProfileStore) globalProfilePath() string {
	return filepath.Join(store.baseDir, "global_profile.md")
}

func (store *ProfileStore) knowledgeBaseProfilePath(id string) string {
	return filepath.Join(store.baseDir, "kb", sanitizeProfileFileName(id)+".md")
}

func buildPromptProfile(scope string, knowledgeBaseID string, content string, info os.FileInfo) PromptProfile {
	profile := PromptProfile{
		Scope:           scope,
		KnowledgeBaseID: knowledgeBaseID,
		Content:         content,
		Exists:          info != nil,
	}

	if info != nil {
		profile.UpdatedAt = info.ModTime().UTC().Format(time.RFC3339)
	}

	return profile
}

func (store *ProfileStore) read(path string, scope string, knowledgeBaseID string) (PromptProfile, error) {
	store.mu.Lock()
	defer store.mu.Unlock()

	if err := os.MkdirAll(filepath.Dir(path), os.ModePerm); err != nil {
		return PromptProfile{}, err
	}

	info, err := os.Stat(path)
	if err != nil {
		if os.IsNotExist(err) {
			return buildPromptProfile(scope, knowledgeBaseID, "", nil), nil
		}
		return PromptProfile{}, err
	}

	bytes, err := os.ReadFile(path)
	if err != nil {
		return PromptProfile{}, err
	}

	return buildPromptProfile(scope, knowledgeBaseID, string(bytes), info), nil
}

func (store *ProfileStore) write(path string, scope string, knowledgeBaseID string, content string) (PromptProfile, error) {
	store.mu.Lock()
	defer store.mu.Unlock()

	if err := os.MkdirAll(filepath.Dir(path), os.ModePerm); err != nil {
		return PromptProfile{}, err
	}

	normalized := strings.TrimSpace(content)
	if normalized != "" && !strings.HasSuffix(normalized, "\n") {
		normalized += "\n"
	}

	if err := os.WriteFile(path, []byte(normalized), 0o666); err != nil {
		return PromptProfile{}, err
	}

	info, err := os.Stat(path)
	if err != nil {
		return PromptProfile{}, err
	}

	return buildPromptProfile(scope, knowledgeBaseID, normalized, info), nil
}

func (store *ProfileStore) GetGlobalProfile() (PromptProfile, error) {
	return store.read(store.globalProfilePath(), "global", "")
}

func (store *ProfileStore) SaveGlobalProfile(content string) (PromptProfile, error) {
	return store.write(store.globalProfilePath(), "global", "", content)
}

func (store *ProfileStore) GetKnowledgeBaseProfile(id string) (PromptProfile, error) {
	return store.read(store.knowledgeBaseProfilePath(id), "knowledge-base", id)
}

func (store *ProfileStore) SaveKnowledgeBaseProfile(id string, content string) (PromptProfile, error) {
	return store.write(store.knowledgeBaseProfilePath(id), "knowledge-base", id, content)
}
