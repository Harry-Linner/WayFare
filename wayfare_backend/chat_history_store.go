package main

import "sync"

type InMemoryChatHistoryStore struct {
	mu      sync.Mutex
	limit   int
	history map[string][]map[string]string
}

func NewInMemoryChatHistoryStore(limit int) *InMemoryChatHistoryStore {
	if limit <= 0 {
		limit = 8
	}
	return &InMemoryChatHistoryStore{
		limit:   limit,
		history: map[string][]map[string]string{},
	}
}

func (store *InMemoryChatHistoryStore) Get(sessionKey string, max int) []map[string]string {
	store.mu.Lock()
	defer store.mu.Unlock()

	items := store.history[sessionKey]
	if len(items) == 0 {
		return []map[string]string{}
	}

	start := 0
	if max > 0 && len(items) > max {
		start = len(items) - max
	}

	result := make([]map[string]string, 0, len(items[start:]))
	for _, item := range items[start:] {
		copy := map[string]string{
			"role":    item["role"],
			"content": item["content"],
		}
		result = append(result, copy)
	}
	return result
}

func (store *InMemoryChatHistoryStore) Add(sessionKey, role, content string) {
	store.mu.Lock()
	defer store.mu.Unlock()

	items := append(store.history[sessionKey], map[string]string{
		"role":    role,
		"content": content,
	})
	if len(items) > store.limit {
		items = items[len(items)-store.limit:]
	}
	store.history[sessionKey] = items
}
