/**
 * 通知系统 - 前后端通信数据定义
 * 用于头像旁的通知面板
 */

// ============= 通知优先级与类型 =============
export const NotificationType = {
  LEARNING_PROGRESS: 'learning_progress',      // 学习进度更新
  TASK_COMPLETED: 'task_completed',            // 任务完成
  PENDING_QUESTIONS: 'pending_questions',      // 待处理问题
  LEARNING_RECOMMENDATION: 'learning_recommendation', // 学习建议
  CONFUSION_DETECTED: 'confusion_detected',    // 卡顿检测
  ACHIEVEMENT_UNLOCKED: 'achievement_unlocked', // 成就解锁
  DEADLINE_REMINDER: 'deadline_reminder',      // 截止日期提醒
  RESOURCE_AVAILABLE: 'resource_available',    // 补充资源可用
  PEER_INTERACTION: 'peer_interaction',        // 同学互动
  SYSTEM_MESSAGE: 'system_message'             // 系统消息
} as const;

export type NotificationTypeKey = typeof NotificationType[keyof typeof NotificationType];

export const NotificationPriority = {
  URGENT: 'urgent',
  HIGH: 'high',
  NORMAL: 'normal',
  LOW: 'low'
} as const;

export type NotificationPriorityType = typeof NotificationPriority[keyof typeof NotificationPriority];

// ============= 单个通知对象 =============
export interface Notification {
  id: string;
  userId: string;
  
  // 基础信息
  type: NotificationTypeKey;
  title: string;
  message: string;
  priority: NotificationPriorityType;
  
  // 样式与呈现
  icon?: string;                    // 图标名称或 emoji
  backgroundColor?: string;         // 背景颜色（可选）
  
  // 操作相关
  actionUrl?: string;              // 点击后的跳转 URL
  actionLabel?: string;            // 按钮文本
  actionType?: 'navigate' | 'open_modal' | 'trigger_task' | 'none'; // 行为类型
  actionPayload?: Record<string, unknown>; // 行为参数
  
  // 详细数据
  metadata?: {
    documentId?: string;
    annotationId?: string;
    taskId?: string;
    projectId?: string;
    relatedContent?: string;       // 相关内容摘要
    
    // 进度相关
    currentProgress?: number;      // 0-100
    targetProgress?: number;
    
    // 问题相关
    questionCount?: number;
    completedCount?: number;
    
    // 时间相关
    estimatedTimeMinutes?: number;
    dueDate?: number;
    
    [key: string]: unknown;
  };
  
  // 时间信息
  createdAt: number;
  scheduledAt?: number;            // 计划发送时间
  expiresAt?: number;              // 过期时间
  
  // 状态
  isRead: boolean;
  readAt?: number;
  isDismissed?: boolean;
  dismissedAt?: number;
}

// ============= 通知数组包装 =============
export interface NotificationBatch {
  notifications: Notification[];
  totalCount: number;
  unreadCount: number;
  hasMore: boolean;
}

// ============= 前端 → 后端：获取通知 =============
export interface FetchNotificationsRequest {
  userId: string;
  projectId?: string;
  limit?: number;              // 默认 20
  offset?: number;             // 分页偏移，默认 0
  types?: NotificationTypeKey[]; // 过滤通知类型
  unreadOnly?: boolean;         // 只返回未读，默认 false
  sortBy?: 'recent' | 'priority'; // 排序方式，默认 'recent'
}

export interface FetchNotificationsResponse {
  status: 'success' | 'error';
  data?: NotificationBatch;
  error?: {
    code: string;
    message: string;
  };
}

// ============= 前端 → 后端：标记通知为已读 =============
export interface MarkNotificationReadRequest {
  notificationId: string;
  userId: string;
}

export interface MarkNotificationReadResponse {
  status: 'success' | 'error';
  notification?: Notification;
  error?: {
    code: string;
    message: string;
  };
}

// ============= 前端 → 后端：清除通知 =============
export interface DismissNotificationRequest {
  notificationId: string;
  userId: string;
}

export interface BatchDismissNotificationsRequest {
  notificationIds: string[];
  userId: string;
}

export interface DismissNotificationResponse {
  status: 'success' | 'error';
  dismissed: boolean;
  error?: {
    code: string;
    message: string;
  };
}

// ============= 后端 → 前端：实时推送（WebSocket 或轮询） =============
/**
 * 后端通过 WebSocket 或 Server-Sent Events 推送新通知
 * Tauri 中枢应该实现监听器
 */
export interface NotificationPushEvent {
  eventType: 'new_notification' | 'notification_updated' | 'notification_dismissed';
  notification: Notification;
  timestamp: number;
}

// ============= 具体场景的通知数据示例 =============

/**
 * 学习进度通知
 */
export interface LearningProgressNotification extends Notification {
  type: 'learning_progress';
  metadata?: {
    documentId: string;
    currentProgress: number;    // 0-100
    targetProgress: number;
    topicsLearned?: string[];
    nextTopic?: string;
  };
}

/**
 * 任务完成通知
 */
export interface TaskCompletedNotification extends Notification {
  type: 'task_completed';
  metadata?: {
    taskId: string;
    taskName: string;
    completionTime: number;     // 完成耗时（秒）
    points?: number;            // 获得的积分
    nextTask?: {
      id: string;
      name: string;
    };
  };
}

/**
 * 卡顿检测通知
 */
export interface ConfusionDetectedNotification extends Notification {
  type: 'confusion_detected';
  metadata?: {
    documentId: string;
    annotationId: string;
    topic: string;
    detectedAt: number;
    timeStuckSeconds: number;
    suggestedActions?: Array<{
      action: string;
      description: string;
    }>;
    recommendedResources?: Array<{
      id: string;
      title: string;
      type: 'video' | 'article' | 'exercise';
      url: string;
    }>;
  };
}

/**
 * 待处理问题通知
 */
export interface PendingQuestionsNotification extends Notification {
  type: 'pending_questions';
  metadata?: {
    questionCount: number;
    completedCount: number;
    topicsWithQuestions?: string[];
    deadlineTimestamp?: number;
  };
}

/**
 * 成就解锁通知
 */
export interface AchievementUnlockedNotification extends Notification {
  type: 'achievement_unlocked';
  metadata?: {
    achievementId: string;
    achievementName: string;
    achievementIcon?: string;
    points: number;
    description: string;
    nextAchievement?: {
      name: string;
      progress: number; // 0-100
    };
  };
}

// ============= 后端配置：通知规则 =============
/**
 * 用户的通知偏好设置（可存储在 localStorage 或后端）
 */
export interface NotificationPreferences {
  userId: string;
  
  // 启用的通知类型
  enabledTypes: NotificationTypeKey[];
  
  // 通知方式
  enableBrowserNotifications: boolean;
  enableInAppNotifications: boolean;
  enableEmailNotifications: boolean;
  
  // 优先级过滤
  minPriorityLevel: NotificationPriorityType;
  
  // 时间设置
  quietHours?: {
    enabled: boolean;
    from: string;  // "22:00"
    to: string;    // "08:00"
  };
  
  // 频率控制
  maxNotificationsPerHour?: number;
  
  updatedAt: number;
}

// ============= 后端 API 路由定义 =============
/**
 * 后端应该提供的通知相关 API 端点：
 * 
 * GET    /api/notifications                    - 获取通知列表
 * POST   /api/notifications/:id/read           - 标记为已读
 * DELETE /api/notifications/:id                - 删除通知
 * POST   /api/notifications/batch-dismiss      - 批量删除
 * GET    /api/notifications/preferences        - 获取偏好设置
 * PUT    /api/notifications/preferences        - 更新偏好设置
 * POST   /api/notifications/test               - 发送测试通知（仅开发）
 * 
 * WebSocket 路由：
 * WS     /ws/notifications/:userId             - 实时通知推送
 */
