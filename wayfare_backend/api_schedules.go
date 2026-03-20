package main

import (
	"errors"
	"net/http"
	"sort"
	"strconv"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
)

const (
	defaultProjectID uint   = 1
	defaultSnoozeMin int    = 10
	maxReminderMin   int    = 24 * 60
	repeatNone       string = "none"
	repeatDaily      string = "daily"
	repeatWeekdays   string = "weekdays"
	repeatWeekly     string = "weekly"
	statusPending    string = "pending"
	statusCompleted  string = "completed"
)

type SchedulePayload struct {
	ProjectID             uint   `json:"projectId"`
	Title                 string `json:"title"`
	Description           string `json:"description"`
	ScheduledFor          string `json:"scheduledFor"`
	ReminderOffsetMinutes int    `json:"reminderOffsetMinutes"`
	RepeatRule            string `json:"repeatRule"`
}

type SnoozePayload struct {
	Minutes int `json:"minutes"`
}

type ReschedulePayload struct {
	ScheduledFor string `json:"scheduledFor"`
}

type ScheduleResponse struct {
	ID                    uint    `json:"id"`
	ProjectID             uint    `json:"projectId"`
	Title                 string  `json:"title"`
	Description           string  `json:"description"`
	ScheduledFor          string  `json:"scheduledFor"`
	ReminderOffsetMinutes int     `json:"reminderOffsetMinutes"`
	RepeatRule            string  `json:"repeatRule"`
	Status                string  `json:"status"`
	SnoozedUntil          *string `json:"snoozedUntil,omitempty"`
	LastNotifiedAt        *string `json:"lastNotifiedAt,omitempty"`
	LastCompletedAt       *string `json:"lastCompletedAt,omitempty"`
	NextTriggerAt         *string `json:"nextTriggerAt,omitempty"`
	IsRecurring           bool    `json:"isRecurring"`
}

func RegisterScheduleRoutes(router gin.IRouter, store ScheduleStore) {
	router.GET("/schedules", func(c *gin.Context) { ListSchedulesAPI(c, store) })
	router.POST("/schedules", func(c *gin.Context) { CreateScheduleAPI(c, store) })
	router.PUT("/schedules/:id", func(c *gin.Context) { UpdateScheduleAPI(c, store) })
	router.DELETE("/schedules/:id", func(c *gin.Context) { DeleteScheduleAPI(c, store) })
	router.POST("/schedules/:id/complete", func(c *gin.Context) { CompleteScheduleAPI(c, store) })
	router.POST("/schedules/:id/snooze", func(c *gin.Context) { SnoozeScheduleAPI(c, store) })
	router.POST("/schedules/:id/reschedule", func(c *gin.Context) { RescheduleScheduleAPI(c, store) })
	router.POST("/schedules/:id/acknowledge", func(c *gin.Context) { AcknowledgeScheduleAPI(c, store) })
}

func parseProjectID(raw string) (uint, error) {
	raw = strings.TrimSpace(raw)
	if raw == "" {
		return defaultProjectID, nil
	}

	value, err := strconv.ParseUint(raw, 10, 64)
	if err != nil {
		return 0, err
	}

	return uint(value), nil
}

func normalizeRepeatRule(raw string) string {
	switch strings.ToLower(strings.TrimSpace(raw)) {
	case repeatDaily:
		return repeatDaily
	case repeatWeekdays:
		return repeatWeekdays
	case repeatWeekly:
		return repeatWeekly
	default:
		return repeatNone
	}
}

func normalizeReminderOffsetMinutes(minutes int) int {
	if minutes < 0 {
		return 0
	}
	if minutes > maxReminderMin {
		return maxReminderMin
	}
	return minutes
}

func parseScheduleTime(raw string) (time.Time, error) {
	trimmed := strings.TrimSpace(raw)
	layouts := []string{
		time.RFC3339,
		"2006-01-02T15:04",
		"2006-01-02 15:04",
	}

	var parsed time.Time
	var err error
	for _, layout := range layouts {
		if layout == time.RFC3339 {
			parsed, err = time.Parse(layout, trimmed)
		} else {
			parsed, err = time.ParseInLocation(layout, trimmed, time.Local)
		}
		if err == nil {
			return parsed.UTC(), nil
		}
	}

	return time.Time{}, err
}

func formatOptionalTime(value *time.Time) *string {
	if value == nil {
		return nil
	}
	formatted := value.UTC().Format(time.RFC3339)
	return &formatted
}

func computeNextTriggerTime(schedule Schedule) *time.Time {
	if schedule.Status == statusCompleted && schedule.RepeatRule == repeatNone {
		return nil
	}

	if schedule.SnoozedUntil != nil {
		trigger := schedule.SnoozedUntil.UTC()
		return &trigger
	}

	trigger := schedule.ScheduledFor.Add(-time.Duration(schedule.ReminderOffsetMinutes) * time.Minute).UTC()
	return &trigger
}

func mapScheduleResponse(schedule Schedule) ScheduleResponse {
	return ScheduleResponse{
		ID:                    schedule.ID,
		ProjectID:             schedule.ProjectID,
		Title:                 schedule.Title,
		Description:           schedule.Description,
		ScheduledFor:          schedule.ScheduledFor.UTC().Format(time.RFC3339),
		ReminderOffsetMinutes: schedule.ReminderOffsetMinutes,
		RepeatRule:            schedule.RepeatRule,
		Status:                schedule.Status,
		SnoozedUntil:          formatOptionalTime(schedule.SnoozedUntil),
		LastNotifiedAt:        formatOptionalTime(schedule.LastNotifiedAt),
		LastCompletedAt:       formatOptionalTime(schedule.LastCompletedAt),
		NextTriggerAt:         formatOptionalTime(computeNextTriggerTime(schedule)),
		IsRecurring:           schedule.RepeatRule != repeatNone,
	}
}

func findScheduleByID(store ScheduleStore, rawID string) (*Schedule, error) {
	id, err := strconv.ParseUint(rawID, 10, 64)
	if err != nil {
		return nil, err
	}

	return store.Get(uint(id))
}

func nextWeekdayOccurrence(base time.Time) time.Time {
	next := base.AddDate(0, 0, 1)
	for next.Weekday() == time.Saturday || next.Weekday() == time.Sunday {
		next = next.AddDate(0, 0, 1)
	}
	return next
}

func advanceRecurringTime(base time.Time, rule string) time.Time {
	switch rule {
	case repeatDaily:
		return base.AddDate(0, 0, 1)
	case repeatWeekdays:
		return nextWeekdayOccurrence(base)
	case repeatWeekly:
		return base.AddDate(0, 0, 7)
	default:
		return base
	}
}

func computeNextRecurringSlot(current time.Time, rule string, reference time.Time) time.Time {
	next := current
	for !next.After(reference) {
		advanced := advanceRecurringTime(next, rule)
		if advanced.Equal(next) {
			break
		}
		next = advanced
	}
	return next
}

func ListSchedulesAPI(c *gin.Context, store ScheduleStore) {
	projectID, err := parseProjectID(c.Query("projectId"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid projectId"})
		return
	}

	schedules, err := store.List(projectID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to load schedules"})
		return
	}

	sort.Slice(schedules, func(i, j int) bool {
		leftCompleted := schedules[i].Status == statusCompleted
		rightCompleted := schedules[j].Status == statusCompleted
		if leftCompleted != rightCompleted {
			return !leftCompleted
		}
		return schedules[i].ScheduledFor.Before(schedules[j].ScheduledFor)
	})

	result := make([]ScheduleResponse, 0, len(schedules))
	for _, schedule := range schedules {
		result = append(result, mapScheduleResponse(schedule))
	}

	c.JSON(http.StatusOK, gin.H{"schedules": result})
}

func CreateScheduleAPI(c *gin.Context, store ScheduleStore) {
	var payload SchedulePayload
	if err := c.ShouldBindJSON(&payload); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid request payload"})
		return
	}

	title := strings.TrimSpace(payload.Title)
	if title == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "title is required"})
		return
	}

	scheduledFor, err := parseScheduleTime(payload.ScheduledFor)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "scheduledFor must be a valid date time"})
		return
	}

	projectID := payload.ProjectID
	if projectID == 0 {
		projectID = defaultProjectID
	}

	schedule := Schedule{
		ProjectID:             projectID,
		Title:                 title,
		Description:           strings.TrimSpace(payload.Description),
		ScheduledFor:          scheduledFor,
		ReminderOffsetMinutes: normalizeReminderOffsetMinutes(payload.ReminderOffsetMinutes),
		RepeatRule:            normalizeRepeatRule(payload.RepeatRule),
		Status:                statusPending,
	}

	if err := store.Upsert(&schedule); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to create schedule"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"schedule": mapScheduleResponse(schedule)})
}

func UpdateScheduleAPI(c *gin.Context, store ScheduleStore) {
	schedule, err := findScheduleByID(store, c.Param("id"))
	if err != nil {
		if errors.Is(err, ErrScheduleNotFound) {
			c.JSON(http.StatusNotFound, gin.H{"error": "schedule not found"})
			return
		}
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid schedule id"})
		return
	}

	var payload SchedulePayload
	if err := c.ShouldBindJSON(&payload); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid request payload"})
		return
	}

	title := strings.TrimSpace(payload.Title)
	if title == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "title is required"})
		return
	}

	scheduledFor, err := parseScheduleTime(payload.ScheduledFor)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "scheduledFor must be a valid date time"})
		return
	}

	schedule.Title = title
	schedule.Description = strings.TrimSpace(payload.Description)
	schedule.ScheduledFor = scheduledFor
	schedule.ReminderOffsetMinutes = normalizeReminderOffsetMinutes(payload.ReminderOffsetMinutes)
	schedule.RepeatRule = normalizeRepeatRule(payload.RepeatRule)
	schedule.SnoozedUntil = nil
	schedule.LastNotifiedAt = nil

	if err := store.Upsert(schedule); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to update schedule"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"schedule": mapScheduleResponse(*schedule)})
}

func DeleteScheduleAPI(c *gin.Context, store ScheduleStore) {
	schedule, err := findScheduleByID(store, c.Param("id"))
	if err != nil {
		if errors.Is(err, ErrScheduleNotFound) {
			c.JSON(http.StatusNotFound, gin.H{"error": "schedule not found"})
			return
		}
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid schedule id"})
		return
	}

	if err := store.Delete(schedule.ID); err != nil {
		if errors.Is(err, ErrScheduleNotFound) {
			c.JSON(http.StatusNotFound, gin.H{"error": "schedule not found"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to delete schedule"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"deleted": true, "id": schedule.ID})
}

func CompleteScheduleAPI(c *gin.Context, store ScheduleStore) {
	schedule, err := findScheduleByID(store, c.Param("id"))
	if err != nil {
		if errors.Is(err, ErrScheduleNotFound) {
			c.JSON(http.StatusNotFound, gin.H{"error": "schedule not found"})
			return
		}
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid schedule id"})
		return
	}

	completedAt := time.Now().UTC()
	schedule.LastCompletedAt = &completedAt
	schedule.SnoozedUntil = nil
	schedule.LastNotifiedAt = nil

	if schedule.RepeatRule == repeatNone {
		schedule.Status = statusCompleted
	} else {
		reference := completedAt
		if reference.Before(schedule.ScheduledFor) {
			reference = schedule.ScheduledFor
		}
		schedule.ScheduledFor = computeNextRecurringSlot(schedule.ScheduledFor, schedule.RepeatRule, reference)
		schedule.Status = statusPending
	}

	if err := store.Upsert(schedule); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to complete schedule"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"schedule": mapScheduleResponse(*schedule)})
}

func SnoozeScheduleAPI(c *gin.Context, store ScheduleStore) {
	schedule, err := findScheduleByID(store, c.Param("id"))
	if err != nil {
		if errors.Is(err, ErrScheduleNotFound) {
			c.JSON(http.StatusNotFound, gin.H{"error": "schedule not found"})
			return
		}
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid schedule id"})
		return
	}

	if schedule.Status == statusCompleted && schedule.RepeatRule == repeatNone {
		c.JSON(http.StatusBadRequest, gin.H{"error": "completed schedules cannot be snoozed"})
		return
	}

	var payload SnoozePayload
	if err := c.ShouldBindJSON(&payload); err != nil {
		payload.Minutes = defaultSnoozeMin
	}

	minutes := payload.Minutes
	if minutes <= 0 {
		minutes = defaultSnoozeMin
	}
	if minutes > maxReminderMin {
		minutes = maxReminderMin
	}

	snoozedUntil := time.Now().UTC().Add(time.Duration(minutes) * time.Minute)
	schedule.SnoozedUntil = &snoozedUntil
	schedule.LastNotifiedAt = nil

	if err := store.Upsert(schedule); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to snooze schedule"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"schedule": mapScheduleResponse(*schedule)})
}

func RescheduleScheduleAPI(c *gin.Context, store ScheduleStore) {
	schedule, err := findScheduleByID(store, c.Param("id"))
	if err != nil {
		if errors.Is(err, ErrScheduleNotFound) {
			c.JSON(http.StatusNotFound, gin.H{"error": "schedule not found"})
			return
		}
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid schedule id"})
		return
	}

	var payload ReschedulePayload
	if err := c.ShouldBindJSON(&payload); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid request payload"})
		return
	}

	scheduledFor, err := parseScheduleTime(payload.ScheduledFor)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "scheduledFor must be a valid date time"})
		return
	}

	schedule.ScheduledFor = scheduledFor
	schedule.SnoozedUntil = nil
	schedule.LastNotifiedAt = nil
	schedule.Status = statusPending
	schedule.LastCompletedAt = nil

	if err := store.Upsert(schedule); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to reschedule"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"schedule": mapScheduleResponse(*schedule)})
}

func AcknowledgeScheduleAPI(c *gin.Context, store ScheduleStore) {
	schedule, err := findScheduleByID(store, c.Param("id"))
	if err != nil {
		if errors.Is(err, ErrScheduleNotFound) {
			c.JSON(http.StatusNotFound, gin.H{"error": "schedule not found"})
			return
		}
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid schedule id"})
		return
	}

	nextTrigger := computeNextTriggerTime(*schedule)
	if nextTrigger == nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "schedule does not have an active reminder"})
		return
	}

	acknowledgedAt := time.Now().UTC()
	schedule.LastNotifiedAt = &acknowledgedAt

	if err := store.Upsert(schedule); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to acknowledge schedule reminder"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"schedule": mapScheduleResponse(*schedule)})
}
