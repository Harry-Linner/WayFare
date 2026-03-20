package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"sync"
)

type FeedbackEntry struct {
	ID                string                 `json:"id"`
	BetaUser          string                 `json:"betaUser,omitempty"`
	BetaUserHash      string                 `json:"betaUserHash,omitempty"`
	Category          string                 `json:"category"`
	Sentiment         string                 `json:"sentiment"`
	Message           string                 `json:"message"`
	Contact           string                 `json:"contact,omitempty"`
	Page              string                 `json:"page,omitempty"`
	Scope             string                 `json:"scope,omitempty"`
	RecentAction      string                 `json:"recentAction,omitempty"`
	RecentActionAt    string                 `json:"recentActionAt,omitempty"`
	KnowledgeBaseID   string                 `json:"knowledgeBaseId,omitempty"`
	KnowledgeBaseName string                 `json:"knowledgeBaseName,omitempty"`
	DocumentID        string                 `json:"documentId,omitempty"`
	DocumentName      string                 `json:"documentName,omitempty"`
	UserAgent         string                 `json:"userAgent,omitempty"`
	RemoteAddr        string                 `json:"remoteAddr,omitempty"`
	CreatedAt         string                 `json:"createdAt"`
	Metadata          map[string]interface{} `json:"metadata,omitempty"`
}

type JSONFeedbackStore struct {
	path string
	mu   sync.Mutex
}

func NewJSONFeedbackStore(path string) *JSONFeedbackStore {
	return &JSONFeedbackStore{path: path}
}

func (store *JSONFeedbackStore) Append(entry FeedbackEntry) error {
	store.mu.Lock()
	defer store.mu.Unlock()

	if err := os.MkdirAll(filepath.Dir(store.path), os.ModePerm); err != nil {
		return err
	}

	file, err := os.OpenFile(store.path, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o666)
	if err != nil {
		return err
	}
	defer file.Close()

	bytes, err := json.Marshal(entry)
	if err != nil {
		return err
	}

	if _, err := file.Write(append(bytes, '\n')); err != nil {
		return err
	}

	return nil
}
