/// 通知系统 - Tauri 命令处理器
/// 
/// 实现前端与 Python 后端的通知系统通信

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use reqwest::Client;
use tauri::State;

// ============= 数据结构 =============

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Notification {
    pub id: String,
    #[serde(rename = "userId")]
    pub user_id: String,
    #[serde(rename = "type")]
    pub notification_type: String,
    pub title: String,
    pub message: String,
    pub priority: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub icon: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none", rename = "actionUrl")]
    pub action_url: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none", rename = "actionLabel")]
    pub action_label: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none", rename = "actionType")]
    pub action_type: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none", rename = "actionPayload")]
    pub action_payload: Option<HashMap<String, serde_json::Value>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub metadata: Option<HashMap<String, serde_json::Value>>,
    #[serde(rename = "createdAt")]
    pub created_at: i64,
    #[serde(skip_serializing_if = "Option::is_none", rename = "scheduledAt")]
    pub scheduled_at: Option<i64>,
    #[serde(skip_serializing_if = "Option::is_none", rename = "expiresAt")]
    pub expires_at: Option<i64>,
    #[serde(rename = "isRead")]
    pub is_read: bool,
    #[serde(skip_serializing_if = "Option::is_none", rename = "readAt")]
    pub read_at: Option<i64>,
    #[serde(skip_serializing_if = "Option::is_none", rename = "isDismissed")]
    pub is_dismissed: Option<bool>,
    #[serde(skip_serializing_if = "Option::is_none", rename = "dismissedAt")]
    pub dismissed_at: Option<i64>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct NotificationBatch {
    pub notifications: Vec<Notification>,
    #[serde(rename = "totalCount")]
    pub total_count: i32,
    #[serde(rename = "unreadCount")]
    pub unread_count: i32,
    #[serde(rename = "hasMore")]
    pub has_more: bool,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct NotificationPreferences {
    #[serde(rename = "userId")]
    pub user_id: String,
    #[serde(rename = "enabledTypes")]
    pub enabled_types: Vec<String>,
    #[serde(rename = "enableBrowserNotifications")]
    pub enable_browser_notifications: bool,
    #[serde(rename = "enableInAppNotifications")]
    pub enable_in_app_notifications: bool,
    #[serde(rename = "enableEmailNotifications")]
    pub enable_email_notifications: bool,
    #[serde(rename = "minPriorityLevel")]
    pub min_priority_level: String,
    #[serde(skip_serializing_if = "Option::is_none", rename = "quietHours")]
    pub quiet_hours: Option<QuietHours>,
    #[serde(skip_serializing_if = "Option::is_none", rename = "maxNotificationsPerHour")]
    pub max_notifications_per_hour: Option<i32>,
    #[serde(rename = "updatedAt")]
    pub updated_at: i64,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct QuietHours {
    pub enabled: bool,
    pub from: String,
    pub to: String,
}

pub struct AppState {
    pub http_client: Client,
    pub backend_url: String,
}

// ============= Tauri 命令 =============

#[tauri::command]
pub async fn fetch_notifications(
    state: State<'_, AppState>,
    user_id: String,
    project_id: Option<String>,
    limit: u32,
    offset: u32,
    types: Vec<String>,
    unread_only: bool,
    sort_by: String,
) -> Result<NotificationBatch, String> {
    let url = format!("{}/api/notifications/fetch", state.backend_url);
    
    let body = serde_json::json!({
        "user_id": user_id,
        "project_id": project_id,
        "limit": limit,
        "offset": offset,
        "types": types,
        "unread_only": unread_only,
        "sort_by": sort_by,
    });
    
    let response = state.http_client
        .post(&url)
        .json(&body)
        .send()
        .await
        .map_err(|e| format!("NETWORK_ERROR: {}", e))?;
    
    if !response.status().is_success() {
        return Err(format!("SERVER_ERROR: {}", response.status()));
    }
    
    response.json::<NotificationBatch>()
        .await
        .map_err(|e| format!("INVALID_RESPONSE: {}", e))
}

#[tauri::command]
pub async fn mark_notification_as_read(
    state: State<'_, AppState>,
    notification_id: String,
    user_id: String,
) -> Result<Notification, String> {
    let url = format!("{}/api/notifications/{}/read", state.backend_url, notification_id);
    
    let body = serde_json::json!({
        "user_id": user_id,
    });
    
    let response = state.http_client
        .post(&url)
        .json(&body)
        .send()
        .await
        .map_err(|e| format!("NETWORK_ERROR: {}", e))?;
    
    if response.status() == 404 {
        return Err("NOT_FOUND: Notification not found".to_string());
    }
    
    if !response.status().is_success() {
        return Err(format!("SERVER_ERROR: {}", response.status()));
    }
    
    response.json::<Notification>()
        .await
        .map_err(|e| format!("INVALID_RESPONSE: {}", e))
}

#[tauri::command]
pub async fn dismiss_notification(
    state: State<'_, AppState>,
    notification_id: String,
    user_id: String,
) -> Result<serde_json::Value, String> {
    let url = format!("{}/api/notifications/{}", state.backend_url, notification_id);
    
    let response = state.http_client
        .delete(&url)
        .query(&[("user_id", user_id)])
        .send()
        .await
        .map_err(|e| format!("NETWORK_ERROR: {}", e))?;
    
    if !response.status().is_success() {
        return Err(format!("SERVER_ERROR: {}", response.status()));
    }
    
    response.json()
        .await
        .map_err(|e| format!("INVALID_RESPONSE: {}", e))
}

#[tauri::command]
pub async fn batch_dismiss_notifications(
    state: State<'_, AppState>,
    notification_ids: Vec<String>,
    user_id: String,
) -> Result<serde_json::Value, String> {
    let url = format!("{}/api/notifications/batch-dismiss", state.backend_url);
    
    let body = serde_json::json!({
        "notification_ids": notification_ids,
        "user_id": user_id,
    });
    
    let response = state.http_client
        .post(&url)
        .json(&body)
        .send()
        .await
        .map_err(|e| format!("NETWORK_ERROR: {}", e))?;
    
    if !response.status().is_success() {
        return Err(format!("SERVER_ERROR: {}", response.status()));
    }
    
    response.json()
        .await
        .map_err(|e| format!("INVALID_RESPONSE: {}", e))
}

#[tauri::command]
pub async fn get_notification_preferences(
    state: State<'_, AppState>,
    user_id: String,
) -> Result<NotificationPreferences, String> {
    let url = format!("{}/api/notifications/preferences", state.backend_url);
    
    let response = state.http_client
        .get(&url)
        .query(&[("user_id", user_id)])
        .send()
        .await
        .map_err(|e| format!("NETWORK_ERROR: {}", e))?;
    
    if !response.status().is_success() {
        return Err(format!("SERVER_ERROR: {}", response.status()));
    }
    
    response.json::<NotificationPreferences>()
        .await
        .map_err(|e| format!("INVALID_RESPONSE: {}", e))
}

#[tauri::command]
pub async fn update_notification_preferences(
    state: State<'_, AppState>,
    preferences: NotificationPreferences,
) -> Result<serde_json::Value, String> {
    let url = format!("{}/api/notifications/preferences", state.backend_url);
    
    let response = state.http_client
        .put(&url)
        .json(&preferences)
        .send()
        .await
        .map_err(|e| format!("NETWORK_ERROR: {}", e))?;
    
    if !response.status().is_success() {
        return Err(format!("SERVER_ERROR: {}", response.status()));
    }
    
    response.json()
        .await
        .map_err(|e| format!("INVALID_RESPONSE: {}", e))
}

#[tauri::command]
pub async fn refresh_notification_stream(
    state: State<'_, AppState>,
    user_id: String,
) -> Result<serde_json::Value, String> {
    // 刷新通知流 - 简单实现为重新获取通知
    let url = format!("{}/api/notifications/fetch", state.backend_url);
    
    let body = serde_json::json!({
        "user_id": user_id,
        "limit": 20,
        "offset": 0,
        "types": [],
        "unread_only": false,
        "sort_by": "recent",
    });
    
    let response = state.http_client
        .post(&url)
        .json(&body)
        .send()
        .await
        .map_err(|e| format!("NETWORK_ERROR: {}", e))?;
    
    if !response.status().is_success() {
        return Err(format!("SERVER_ERROR: {}", response.status()));
    }
    
    Ok(serde_json::json!({"success": true}))
}

#[tauri::command]
pub async fn send_test_notification(
    state: State<'_, AppState>,
    user_id: String,
    notification_type: String,
) -> Result<Notification, String> {
    let url = format!("{}/api/notifications/test", state.backend_url);
    
    let body = serde_json::json!({
        "user_id": user_id,
        "notification_type": notification_type,
    });
    
    let response = state.http_client
        .post(&url)
        .json(&body)
        .send()
        .await
        .map_err(|e| format!("NETWORK_ERROR: {}", e))?;
    
    if response.status() == 403 {
        return Err("FORBIDDEN: Test notifications disabled".to_string());
    }
    
    if !response.status().is_success() {
        return Err(format!("SERVER_ERROR: {}", response.status()));
    }
    
    response.json::<Notification>()
        .await
        .map_err(|e| format!("INVALID_RESPONSE: {}", e))
}
