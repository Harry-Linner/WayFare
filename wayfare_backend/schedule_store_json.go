package main

import (
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"sync"
	"time"
)

var ErrScheduleNotFound = errors.New("schedule not found")

type ScheduleStore interface {
	List(projectID uint) ([]Schedule, error)
	Get(id uint) (*Schedule, error)
	Upsert(schedule *Schedule) error
	Delete(id uint) error
}

type scheduleFileData struct {
	NextID    uint       `json:"nextId"`
	Schedules []Schedule `json:"schedules"`
}

type JSONScheduleStore struct {
	path string
	mu   sync.Mutex
}

func NewJSONScheduleStore(path string) *JSONScheduleStore {
	return &JSONScheduleStore{path: path}
}

func (store *JSONScheduleStore) List(projectID uint) ([]Schedule, error) {
	store.mu.Lock()
	defer store.mu.Unlock()

	data, err := store.loadLocked()
	if err != nil {
		return nil, err
	}

	result := make([]Schedule, 0, len(data.Schedules))
	for _, schedule := range data.Schedules {
		if projectID == 0 || schedule.ProjectID == projectID || schedule.ProjectID == 0 {
			if schedule.ProjectID == 0 {
				schedule.ProjectID = defaultProjectID
			}
			result = append(result, schedule)
		}
	}

	return result, nil
}

func (store *JSONScheduleStore) Get(id uint) (*Schedule, error) {
	store.mu.Lock()
	defer store.mu.Unlock()

	data, err := store.loadLocked()
	if err != nil {
		return nil, err
	}

	for _, schedule := range data.Schedules {
		if schedule.ID == id {
			copy := schedule
			if copy.ProjectID == 0 {
				copy.ProjectID = defaultProjectID
			}
			return &copy, nil
		}
	}

	return nil, ErrScheduleNotFound
}

func (store *JSONScheduleStore) Upsert(schedule *Schedule) error {
	if schedule == nil {
		return errors.New("schedule is nil")
	}

	store.mu.Lock()
	defer store.mu.Unlock()

	data, err := store.loadLocked()
	if err != nil {
		return err
	}

	now := time.Now().UTC()
	if schedule.ProjectID == 0 {
		schedule.ProjectID = defaultProjectID
	}
	if schedule.Status == "" {
		schedule.Status = statusPending
	}
	if schedule.RepeatRule == "" {
		schedule.RepeatRule = repeatNone
	}

	if schedule.ID == 0 {
		if data.NextID == 0 {
			data.NextID = 1
		}
		schedule.ID = data.NextID
		data.NextID++
		if schedule.CreatedAt.IsZero() {
			schedule.CreatedAt = now
		}
		schedule.UpdatedAt = now
		data.Schedules = append(data.Schedules, *schedule)
		return store.saveLocked(data)
	}

	for index, existing := range data.Schedules {
		if existing.ID == schedule.ID {
			if schedule.CreatedAt.IsZero() {
				schedule.CreatedAt = existing.CreatedAt
			}
			schedule.UpdatedAt = now
			data.Schedules[index] = *schedule
			return store.saveLocked(data)
		}
	}

	if data.NextID <= schedule.ID {
		data.NextID = schedule.ID + 1
	}
	if schedule.CreatedAt.IsZero() {
		schedule.CreatedAt = now
	}
	schedule.UpdatedAt = now
	data.Schedules = append(data.Schedules, *schedule)
	return store.saveLocked(data)
}

func (store *JSONScheduleStore) Delete(id uint) error {
	store.mu.Lock()
	defer store.mu.Unlock()

	data, err := store.loadLocked()
	if err != nil {
		return err
	}

	filtered := data.Schedules[:0]
	found := false
	for _, schedule := range data.Schedules {
		if schedule.ID == id {
			found = true
			continue
		}
		filtered = append(filtered, schedule)
	}

	if !found {
		return ErrScheduleNotFound
	}

	data.Schedules = filtered
	return store.saveLocked(data)
}

func (store *JSONScheduleStore) loadLocked() (scheduleFileData, error) {
	if err := os.MkdirAll(filepath.Dir(store.path), os.ModePerm); err != nil {
		return scheduleFileData{}, err
	}

	if _, err := os.Stat(store.path); errors.Is(err, os.ErrNotExist) {
		initial := scheduleFileData{
			NextID:    1,
			Schedules: []Schedule{},
		}
		if err := store.saveLocked(initial); err != nil {
			return scheduleFileData{}, err
		}
		return initial, nil
	}

	bytes, err := os.ReadFile(store.path)
	if err != nil {
		return scheduleFileData{}, err
	}

	if len(bytes) == 0 {
		return scheduleFileData{NextID: 1, Schedules: []Schedule{}}, nil
	}

	var data scheduleFileData
	if err := json.Unmarshal(bytes, &data); err != nil {
		return scheduleFileData{}, err
	}

	if data.NextID == 0 {
		var maxID uint
		for _, schedule := range data.Schedules {
			if schedule.ID > maxID {
				maxID = schedule.ID
			}
		}
		data.NextID = maxID + 1
	}

	return data, nil
}

func (store *JSONScheduleStore) saveLocked(data scheduleFileData) error {
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
