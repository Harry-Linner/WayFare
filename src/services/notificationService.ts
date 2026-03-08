/**
 * 通知 API 服务层
 * 负责前端与后端的通信
 * 通过 Tauri 命令进行安全通信
 */

import { invoke } from '@tauri-apps/api/core';
import type {
  Notification,
  NotificationBatch,
  FetchNotificationsRequest,
  MarkNotificationReadRequest,
  DismissNotificationRequest,
  BatchDismissNotificationsRequest,
  NotificationPreferences,
} from '../types/notifications';

class NotificationService {
  /**
   * 获取通知列表
   * 对应 Tauri 命令: fetch_notifications
   */
  async fetchNotifications(
    request: FetchNotificationsRequest
  ): Promise<NotificationBatch> {
    try {
      const result = await invoke<NotificationBatch>('fetch_notifications', {
        user_id: request.userId,
        project_id: request.projectId ?? null,
        limit: request.limit ?? 20,
        offset: request.offset ?? 0,
        types: request.types ?? [],
        unread_only: request.unreadOnly ?? false,
        sort_by: request.sortBy ?? 'recent',
      });

      return result;
    } catch (error) {
      console.error('Error fetching notifications:', error);
      throw error;
    }
  }

  /**
   * 标记单个通知为已读
   * 对应 Tauri 命令: mark_notification_as_read
   */
  async markAsRead(request: MarkNotificationReadRequest): Promise<Notification> {
    try {
      const result = await invoke<Notification>('mark_notification_as_read', {
        notification_id: request.notificationId,
        user_id: request.userId,
      });
      return result;
    } catch (error) {
      console.error('Error marking notification as read:', error);
      throw error;
    }
  }

  /**
   * 关闭/删除单个通知
   * 对应 Tauri 命令: dismiss_notification
   */
  async dismissNotification(request: DismissNotificationRequest): Promise<boolean> {
    try {
      const result = await invoke<{ dismissed: boolean }>('dismiss_notification', {
        notification_id: request.notificationId,
        user_id: request.userId,
      });
      return result.dismissed;
    } catch (error) {
      console.error('Error dismissing notification:', error);
      throw error;
    }
  }

  /**
   * 批量关闭通知
   * 对应 Tauri 命令: batch_dismiss_notifications
   */
  async batchDismissNotifications(
    request: BatchDismissNotificationsRequest
  ): Promise<boolean> {
    try {
      const result = await invoke<{ status: string }>('batch_dismiss_notifications', {
        notification_ids: request.notificationIds,
        user_id: request.userId,
      });
      return result.status === 'success';
    } catch (error) {
      console.error('Error batch dismissing notifications:', error);
      throw error;
    }
  }

  /**
   * 获取通知偏好设置
   * 对应 Tauri 命令: get_notification_preferences
   */
  async getPreferences(userId: string): Promise<NotificationPreferences> {
    try {
      const result = await invoke<NotificationPreferences>('get_notification_preferences', {
        user_id: userId,
      });
      return result;
    } catch (error) {
      console.error('Error fetching notification preferences:', error);
      throw error;
    }
  }

  /**
   * 更新通知偏好设置
   * 对应 Tauri 命令: update_notification_preferences
   */
  async updatePreferences(preferences: NotificationPreferences): Promise<boolean> {
    try {
      const result = await invoke<{ status: string }>('update_notification_preferences', {
        preferences,
      });
      return result.status === 'success';
    } catch (error) {
      console.error('Error updating notification preferences:', error);
      throw error;
    }
  }

  /**
   * 刷新用户的实时通知通道
   * 对应 Tauri 命令: refresh_notification_stream
   */
  async refreshNotificationStream(userId: string): Promise<boolean> {
    try {
      const result = await invoke<{ success: boolean }>('refresh_notification_stream', {
        user_id: userId,
      });
      return result.success;
    } catch (error) {
      console.error('Error refreshing notification stream:', error);
      throw error;
    }
  }
}

// 导出单例服务
export const notificationService = new NotificationService();
