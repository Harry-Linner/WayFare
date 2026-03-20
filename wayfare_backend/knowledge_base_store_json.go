package main

import (
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"time"

	"github.com/google/uuid"
)

var ErrKnowledgeBaseNotFound = errors.New("knowledge base not found")
var ErrPortableDocumentNotFound = errors.New("portable document not found")

type KnowledgeBase struct {
	ID             string    `json:"id"`
	Name           string    `json:"name"`
	Description    string    `json:"description"`
	Purpose        string    `json:"purpose,omitempty"`
	Subject        string    `json:"subject,omitempty"`
	LearningGoals  string    `json:"learningGoals,omitempty"`
	StudyTime      string    `json:"studyTime,omitempty"`
	CreationMethod string    `json:"creationMethod,omitempty"`
	FolderName     string    `json:"folderName,omitempty"`
	CreatedAt      time.Time `json:"createdAt"`
	UpdatedAt      time.Time `json:"updatedAt"`
}

type PortableDocument struct {
	ID              string    `json:"id"`
	KnowledgeBaseID string    `json:"knowledgeBaseId"`
	FileName        string    `json:"fileName"`
	StoredName      string    `json:"storedName"`
	FileType        string    `json:"fileType"`
	SizeBytes       int64     `json:"sizeBytes"`
	PageCount       int       `json:"pageCount"`
	DocHash         string    `json:"docHash"`
	Status          string    `json:"status"`
	CreatedAt       time.Time `json:"createdAt"`
	UpdatedAt       time.Time `json:"updatedAt"`
}

type PortableKnowledgeBaseStore interface {
	ListKnowledgeBases() ([]KnowledgeBase, error)
	GetKnowledgeBase(id string) (*KnowledgeBase, error)
	CreateKnowledgeBase(entry *KnowledgeBase) error
	DeleteKnowledgeBase(id string) ([]PortableDocument, error)
	ListDocuments(kbID string) ([]PortableDocument, error)
	GetDocument(id string) (*PortableDocument, error)
	CreateDocument(entry *PortableDocument) error
	DeleteDocument(id string) (*PortableDocument, error)
	UpdateDocumentStatusByDocHash(docHash string, status string) (*PortableDocument, error)
}

type portableKnowledgeBaseData struct {
	KnowledgeBases []KnowledgeBase    `json:"knowledgeBases"`
	Documents      []PortableDocument `json:"documents"`
}

type JSONKnowledgeBaseStore struct {
	path string
	mu   sync.Mutex
}

func NewJSONKnowledgeBaseStore(path string) *JSONKnowledgeBaseStore {
	return &JSONKnowledgeBaseStore{path: path}
}

func (store *JSONKnowledgeBaseStore) ListKnowledgeBases() ([]KnowledgeBase, error) {
	store.mu.Lock()
	defer store.mu.Unlock()

	data, err := store.loadLocked()
	if err != nil {
		return nil, err
	}

	result := make([]KnowledgeBase, len(data.KnowledgeBases))
	copy(result, data.KnowledgeBases)
	sort.Slice(result, func(i, j int) bool {
		return result[i].UpdatedAt.After(result[j].UpdatedAt)
	})
	return result, nil
}

func (store *JSONKnowledgeBaseStore) GetKnowledgeBase(id string) (*KnowledgeBase, error) {
	store.mu.Lock()
	defer store.mu.Unlock()

	data, err := store.loadLocked()
	if err != nil {
		return nil, err
	}

	for _, entry := range data.KnowledgeBases {
		if entry.ID == id {
			copy := entry
			return &copy, nil
		}
	}

	return nil, ErrKnowledgeBaseNotFound
}

func (store *JSONKnowledgeBaseStore) CreateKnowledgeBase(entry *KnowledgeBase) error {
	if entry == nil {
		return errors.New("knowledge base is nil")
	}

	store.mu.Lock()
	defer store.mu.Unlock()

	data, err := store.loadLocked()
	if err != nil {
		return err
	}

	now := time.Now().UTC()
	if entry.ID == "" {
		entry.ID = "kb-" + uuid.NewString()
	}
	if entry.CreatedAt.IsZero() {
		entry.CreatedAt = now
	}
	entry.UpdatedAt = now
	entry.Name = strings.TrimSpace(entry.Name)
	entry.Description = strings.TrimSpace(entry.Description)
	entry.Purpose = strings.TrimSpace(entry.Purpose)
	entry.Subject = strings.TrimSpace(entry.Subject)
	entry.LearningGoals = strings.TrimSpace(entry.LearningGoals)
	entry.StudyTime = strings.TrimSpace(entry.StudyTime)
	entry.CreationMethod = strings.TrimSpace(entry.CreationMethod)
	entry.FolderName = strings.TrimSpace(entry.FolderName)
	data.KnowledgeBases = append(data.KnowledgeBases, *entry)

	return store.saveLocked(data)
}

func (store *JSONKnowledgeBaseStore) DeleteKnowledgeBase(id string) ([]PortableDocument, error) {
	store.mu.Lock()
	defer store.mu.Unlock()

	data, err := store.loadLocked()
	if err != nil {
		return nil, err
	}

	found := false
	nextKBs := data.KnowledgeBases[:0]
	for _, entry := range data.KnowledgeBases {
		if entry.ID == id {
			found = true
			continue
		}
		nextKBs = append(nextKBs, entry)
	}
	if !found {
		return nil, ErrKnowledgeBaseNotFound
	}

	var removedDocs []PortableDocument
	nextDocs := data.Documents[:0]
	for _, doc := range data.Documents {
		if doc.KnowledgeBaseID == id {
			removedDocs = append(removedDocs, doc)
			continue
		}
		nextDocs = append(nextDocs, doc)
	}

	data.KnowledgeBases = nextKBs
	data.Documents = nextDocs
	if err := store.saveLocked(data); err != nil {
		return nil, err
	}

	return removedDocs, nil
}

func (store *JSONKnowledgeBaseStore) ListDocuments(kbID string) ([]PortableDocument, error) {
	store.mu.Lock()
	defer store.mu.Unlock()

	data, err := store.loadLocked()
	if err != nil {
		return nil, err
	}

	result := make([]PortableDocument, 0)
	for _, doc := range data.Documents {
		if kbID == "" || doc.KnowledgeBaseID == kbID {
			result = append(result, doc)
		}
	}

	sort.Slice(result, func(i, j int) bool {
		return result[i].CreatedAt.After(result[j].CreatedAt)
	})

	return result, nil
}

func (store *JSONKnowledgeBaseStore) GetDocument(id string) (*PortableDocument, error) {
	store.mu.Lock()
	defer store.mu.Unlock()

	data, err := store.loadLocked()
	if err != nil {
		return nil, err
	}

	for _, doc := range data.Documents {
		if doc.ID == id {
			copy := doc
			return &copy, nil
		}
	}

	return nil, ErrPortableDocumentNotFound
}

func (store *JSONKnowledgeBaseStore) CreateDocument(entry *PortableDocument) error {
	if entry == nil {
		return errors.New("document is nil")
	}

	store.mu.Lock()
	defer store.mu.Unlock()

	data, err := store.loadLocked()
	if err != nil {
		return err
	}

	if entry.ID == "" {
		entry.ID = "doc-" + uuid.NewString()
	}
	now := time.Now().UTC()
	entry.FileName = strings.TrimSpace(entry.FileName)
	entry.StoredName = strings.TrimSpace(entry.StoredName)
	entry.FileType = strings.TrimPrefix(strings.ToLower(strings.TrimSpace(entry.FileType)), ".")
	entry.DocHash = strings.TrimSpace(entry.DocHash)
	entry.Status = strings.TrimSpace(entry.Status)
	if entry.Status == "" {
		entry.Status = "completed"
	}
	if entry.CreatedAt.IsZero() {
		entry.CreatedAt = now
	}
	entry.UpdatedAt = now
	data.Documents = append(data.Documents, *entry)

	for idx, kb := range data.KnowledgeBases {
		if kb.ID == entry.KnowledgeBaseID {
			kb.UpdatedAt = now
			data.KnowledgeBases[idx] = kb
			break
		}
	}

	return store.saveLocked(data)
}

func (store *JSONKnowledgeBaseStore) DeleteDocument(id string) (*PortableDocument, error) {
	store.mu.Lock()
	defer store.mu.Unlock()

	data, err := store.loadLocked()
	if err != nil {
		return nil, err
	}

	var removed *PortableDocument
	nextDocs := data.Documents[:0]
	for _, doc := range data.Documents {
		if doc.ID == id {
			copy := doc
			removed = &copy
			continue
		}
		nextDocs = append(nextDocs, doc)
	}

	if removed == nil {
		return nil, ErrPortableDocumentNotFound
	}

	data.Documents = nextDocs
	if err := store.saveLocked(data); err != nil {
		return nil, err
	}

	return removed, nil
}

func (store *JSONKnowledgeBaseStore) UpdateDocumentStatusByDocHash(docHash string, status string) (*PortableDocument, error) {
	store.mu.Lock()
	defer store.mu.Unlock()

	data, err := store.loadLocked()
	if err != nil {
		return nil, err
	}

	docHash = strings.TrimSpace(docHash)
	status = strings.TrimSpace(status)
	if docHash == "" {
		return nil, ErrPortableDocumentNotFound
	}

	var updated *PortableDocument
	now := time.Now().UTC()
	for idx, doc := range data.Documents {
		if doc.DocHash != docHash {
			continue
		}
		doc.Status = status
		doc.UpdatedAt = now
		data.Documents[idx] = doc
		copy := doc
		updated = &copy

		for kbIdx, kb := range data.KnowledgeBases {
			if kb.ID == doc.KnowledgeBaseID {
				kb.UpdatedAt = now
				data.KnowledgeBases[kbIdx] = kb
				break
			}
		}
		break
	}

	if updated == nil {
		return nil, ErrPortableDocumentNotFound
	}

	if err := store.saveLocked(data); err != nil {
		return nil, err
	}

	return updated, nil
}

func (store *JSONKnowledgeBaseStore) loadLocked() (portableKnowledgeBaseData, error) {
	if err := os.MkdirAll(filepath.Dir(store.path), os.ModePerm); err != nil {
		return portableKnowledgeBaseData{}, err
	}

	if _, err := os.Stat(store.path); errors.Is(err, os.ErrNotExist) {
		initial := portableKnowledgeBaseData{
			KnowledgeBases: []KnowledgeBase{},
			Documents:      []PortableDocument{},
		}
		if err := store.saveLocked(initial); err != nil {
			return portableKnowledgeBaseData{}, err
		}
		return initial, nil
	}

	bytes, err := os.ReadFile(store.path)
	if err != nil {
		return portableKnowledgeBaseData{}, err
	}
	if len(bytes) == 0 {
		return portableKnowledgeBaseData{
			KnowledgeBases: []KnowledgeBase{},
			Documents:      []PortableDocument{},
		}, nil
	}

	var data portableKnowledgeBaseData
	if err := json.Unmarshal(bytes, &data); err != nil {
		return portableKnowledgeBaseData{}, err
	}
	if data.KnowledgeBases == nil {
		data.KnowledgeBases = []KnowledgeBase{}
	}
	if data.Documents == nil {
		data.Documents = []PortableDocument{}
	}
	return data, nil
}

func (store *JSONKnowledgeBaseStore) saveLocked(data portableKnowledgeBaseData) error {
	bytes, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		return err
	}

	tempPath := store.path + ".tmp"
	if err := os.WriteFile(tempPath, bytes, 0o666); err != nil {
		return err
	}
	if err := os.Remove(store.path); err != nil && !errors.Is(err, os.ErrNotExist) {
		return err
	}
	return os.Rename(tempPath, store.path)
}
