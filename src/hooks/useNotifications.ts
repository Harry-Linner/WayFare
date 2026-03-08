/**
 * 通知相关的 React Hooks
 * 管理通知的获取、状态和交互
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import type {
  Notification,
  NotificationPreferences,
} from '../types/notifications';
import { notificationService } from '../services/notificationService';
import { useAppStore } from '../store/appStore';

interface UseNotificationsOptions {
  autoFetch?: boolean;          // 自动获取，默认 true
  autoRefreshInterval?: number; // 自动刷新间隔（毫秒），默认 30000（30秒）
  unreadOnly?: boolean;
}

/**
 * 通知列表管理 Hook
 */
export function useNotifications(options: UseNotificationsOptions = {}) {
  const {
    autoFetch = true,
    autoRefreshInterval = 30000,
    unreadOnly = false,
  } = options;

  const { currentUserId: userId, currentProjectId: projectId } = useAppStore();

  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [hasMore, setHasMore] = useState(false);

  const refreshIntervalRef = useRef<number | null>(null);

  // 获取通知列表
  const fetchNotifications = useCallback(
    async (limit = 20, offset = 0) => {
      if (!userId) {
        setError(new Error('User ID not available'));
        return;
      }

      setLoading(true);
      setError(null);
      try {
        const batch = await notificationService.fetchNotifications({
          userId,
          projectId: projectId ?? undefined,
          limit,
          offset,
          unreadOnly,
          sortBy: 'recent',
        });

        setNotifications(batch.notifications);
        setUnreadCount(batch.unreadCount);
        setTotalCount(batch.totalCount);
        setHasMore(batch.hasMore);
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);
        console.error('Failed to fetch notifications:', error);
      } finally {
        setLoading(false);
      }
    },
    [userId, projectId, unreadOnly]
  );

  // 标记为已读
  const markAsRead = useCallback(
    async (notificationId: string) => {
      if (!userId) {
        throw new Error('User ID not available');
      }

      try {
        await notificationService.markAsRead({
          notificationId,
          userId,
        });

        // 更新本地状态
        setNotifications((prev) =>
          prev.map((n) =>
            n.id === notificationId
              ? { ...n, isRead: true, readAt: Date.now() }
              : n
          )
        );
        setUnreadCount((prev) => Math.max(0, prev - 1));
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        console.error('Failed to mark notification as read:', error);
        throw error;
      }
    },
    [userId]
  );

  // 关闭通知
  const dismissNotification = useCallback(
    async (notificationId: string) => {
      if (!userId) {
        throw new Error('User ID not available');
      }

      try {
        await notificationService.dismissNotification({
          notificationId,
          userId,
        });

        // 从列表中移除
        setNotifications((prev) =>
          prev.filter((n) => n.id !== notificationId)
        );
        setTotalCount((prev) => Math.max(0, prev - 1));
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        console.error('Failed to dismiss notification:', error);
        throw error;
      }
    },
    [userId]
  );

  // 批量关闭
  const batchDismiss = useCallback(
    async (notificationIds: string[]) => {
      if (!userId) {
        throw new Error('User ID not available');
      }

      try {
        await notificationService.batchDismissNotifications({
          notificationIds,
          userId,
        });

        setNotifications((prev) =>
          prev.filter((n) => !notificationIds.includes(n.id))
        );
        setTotalCount((prev) => Math.max(0, prev - notificationIds.length));
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        console.error('Failed to batch dismiss notifications:', error);
        throw error;
      }
    },
    [userId]
  );

  // 刷新
  const refresh = useCallback(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  // 自动刷新
  useEffect(() => {
    if (!autoFetch) return;

    // 首次加载
    fetchNotifications();

    // 设置自动刷新
    refreshIntervalRef.current = setInterval(
      () => fetchNotifications(),
      autoRefreshInterval
    );

    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, [autoFetch, autoRefreshInterval, fetchNotifications]);

  return {
    notifications,
    unreadCount,
    totalCount,
    loading,
    error,
    hasMore,
    markAsRead,
    dismissNotification,
    batchDismiss,
    refresh,
  };
}

/**
 * 通知偏好设置 Hook
 */
export function useNotificationPreferences() {
  const { currentUserId: userId } = useAppStore();

  const [preferences, setPreferences] = useState<NotificationPreferences | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  // 获取偏好设置
  const fetchPreferences = useCallback(async () => {
    if (!userId) {
      setError(new Error('User ID not available'));
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const prefs = await notificationService.getPreferences(userId);
      setPreferences(prefs);
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      console.error('Failed to fetch preferences:', error);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  // 更新偏好设置
  const updatePreferences = useCallback(
    async (newPreferences: Partial<NotificationPreferences>) => {
      if (!preferences) return;

      setLoading(true);
      setError(null);
      try {
        const updated = {
          ...preferences,
          ...newPreferences,
          updatedAt: Date.now(),
        };
        await notificationService.updatePreferences(updated);
        setPreferences(updated);
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);
        console.error('Failed to update preferences:', error);
        throw error;
      } finally {
        setLoading(false);
      }
    },
    [preferences]
  );

  // 初始化加载
  useEffect(() => {
    fetchPreferences();
  }, [fetchPreferences]);

  return {
    preferences,
    loading,
    error,
    updatePreferences,
  };
}

/**
 * 单个通知读取状态管理 Hook
 */
export function useNotificationRead(notificationId: string, isReadInitial: boolean) {
  const { currentUserId: userId } = useAppStore();

  const [isRead, setIsRead] = useState(isReadInitial);

  const markAsRead = useCallback(async () => {
    if (isRead) return; // 已经是已读状态
    if (!userId) {
      throw new Error('User ID not available');
    }

    try {
      await notificationService.markAsRead({
        notificationId,
        userId,
      });
      setIsRead(true);
    } catch (error) {
      console.error('Failed to mark as read:', error);
      throw error;
    }
  }, [notificationId, userId, isRead]);

  return {
    isRead,
    markAsRead,
  };
}

/**
 * 通知计数 Hook（仅用于获取未读数）
 */
export function useUnreadNotificationCount() {
  const { currentUserId: userId } = useAppStore();

  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);

  const fetchUnreadCount = useCallback(async () => {
    if (!userId) {
      console.warn('User ID not available for fetching unread count');
      return;
    }

    setLoading(true);
    try {
      const batch = await notificationService.fetchNotifications({
        userId,
        unreadOnly: true,
        limit: 1,
        offset: 0,
      });
      setUnreadCount(batch.unreadCount);
    } catch (error) {
      console.error('Failed to fetch unread count:', error);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchUnreadCount();
    // 每 10 秒更新一次
    const interval = setInterval(fetchUnreadCount, 10000);
    return () => clearInterval(interval);
  }, [fetchUnreadCount]);

  return {
    unreadCount,
    loading,
    refresh: fetchUnreadCount,
  };
}
