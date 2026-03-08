/**
 * Tauri 事件监听系统
 * 用于接收后端/Tauri推送的主动推送事件
 * 
 * 数据流：后端 → Tauri → 前端事件 → Store → UI 更新
 */

import { useEffect, useRef } from 'react';
import { listen } from '@tauri-apps/api/event';
import type { UnlistenFn } from '@tauri-apps/api/event';
import { useAppStore } from '../store/appStore';

export type BackendEvent =
  | { 
      type: 'file_added'
      file_path: string
      file_name: string
      file_type: string
      document_id?: string
    }
  | { 
      type: 'file_modified'
      file_path: string
      document_id?: string
    }
  | { 
      type: 'file_deleted'
      file_path: string
      document_id?: string
    }
  | {
      type: 'agent_proactive_message'
      message_type: 'confusion_detected' | 'help_offered' | 'misconception_detected'
      document_id: string
      page_number?: number
      suggestion: string
      help_content?: {
        analogy?: string
        key_questions?: string[]
        decomposition?: string[]
      }
      timestamp: number
    }
  | {
      type: 'learning_plan_suggested'
      plan_id: string
      title: string
      topics: string[]
      estimated_hours: number
      start_time: number
    }
  | {
      type: 'review_scheduled'
      concept: string
      annotation_id: string
      scheduled_time: number
      reason: string
    }
  | {
      type: 'common_mistake_detected'
      topic: string
      mistake: string
      mistake_count: number
      total_students: number
      correction: string
      explanation?: string
      timestamp: number
    };

interface BackendEventHandlerOptions {
  autoAddMessages?: boolean; // 是否自动添加到聊天
  onError?: (error: Error) => void;
}

/**
 * 在组件挂载时监听所有后端推送事件
 * 约定：这些事件由 Tauri 中枢通过 emit_all 发送
 */
export function useBackendEventListeners(
  options: BackendEventHandlerOptions = { autoAddMessages: true }
) {
  const {
    addChatMessage,
    currentConversationId,
    updateLearningGoal,
  } = useAppStore();

  const unlistenerRef = useRef<UnlistenFn[]>([]);

  useEffect(() => {
    const listeners: Promise<UnlistenFn>[] = [];

    // ============= 1. 文件事件 =============
    listeners.push(
      listen<{ file_path: string; file_name: string; file_type: string; document_id?: string }>(
        'file_added',
        (event) => {
          console.log('📁 新文件添加:', event.payload.file_name);

          if (options.autoAddMessages && currentConversationId && addChatMessage) {
            const message = {
              id: `msg_${Date.now()}`,
              role: 'assistant' as const,
              content: `我检测到你添加了新文件: **${event.payload.file_name}** (${event.payload.file_type})\n\n我已经开始分析其中的重点和难点。要我生成学习建议吗？`,
              timestamp: new Date().toISOString(),
              documentId: event.payload.document_id,
            };
            addChatMessage(currentConversationId, message);
          }
        }
      )
    );

    listeners.push(
      listen<{ file_path: string; document_id?: string }>(
        'file_modified',
        (event) => {
          console.log('✏️ 文件已修改:', event.payload.file_path);
          // 可选：询问用户是否需要重新分析
        }
      )
    );

    // ============= 2. Agent 主动推送 =============
    listeners.push(
      listen<{
        message_type: string
        document_id: string
        page_number?: number
        suggestion: string
        help_content?: {
          analogy?: string
          key_questions?: string[]
        }
        timestamp: number
      }>('agent_proactive_message', (event) => {
        console.log('💬 收到主动帮助:', event.payload.message_type);

        if (options.autoAddMessages && currentConversationId && addChatMessage) {
          const helpDetails = event.payload.help_content
            ? `

**我为你准备了以下帮助：**
${
  event.payload.help_content.analogy
    ? `- 💡 **类比**: ${event.payload.help_content.analogy}`
    : ''
}
${
  event.payload.help_content.key_questions
    ? `- 🤔 **关键问题**: ${event.payload.help_content.key_questions.join(' / ')}`
    : ''
}`
            : '';

          const message = {
            id: `msg_${Date.now()}`,
            role: 'assistant' as const,
            content: `👋 ${event.payload.suggestion}${helpDetails}`,
            timestamp: new Date().toISOString(),
            documentId: event.payload.document_id,
            annotationId: undefined,
          };
          addChatMessage(currentConversationId, message);
        }
      })
    );

    // ============= 3. 学习计划推荐 =============
    listeners.push(
      listen<{ plan_id: string; title: string; topics: string[]; estimated_hours: number }>(
        'learning_plan_suggested',
        (event) => {
          console.log('📅 收到学习计划:', event.payload.title);

          if (options.autoAddMessages && currentConversationId && addChatMessage) {
            const topicsList = event.payload.topics
              .map((t, i) => `${i + 1}. ${t}`)
              .join('\n');

            const message = {
              id: `msg_${Date.now()}`,
              role: 'assistant' as const,
              content: `📅 **我为你制定了一个学习计划: ${event.payload.title}**

预计耗时：${event.payload.estimated_hours} 小时

涉及主题：
${topicsList}

要我详细展开这个计划吗？`,
              timestamp: new Date().toISOString(),
            };
            addChatMessage(currentConversationId, message);
          }
        }
      )
    );

    // ============= 4. 复习提醒 =============
    listeners.push(
      listen<{ concept: string; annotation_id: string; scheduled_time: number; reason: string }>(
        'review_scheduled',
        (event) => {
          console.log('🔔 复习提醒:', event.payload.concept);

          if (options.autoAddMessages && currentConversationId && addChatMessage) {
            const message = {
              id: `msg_${Date.now()}`,
              role: 'assistant' as const,
              content: `🔔 **复习提醒**: 是时候复习 **${event.payload.concept}** 了\n\n📌 原因: ${event.payload.reason}\n\n现在复习可以强化记忆，帮助打破遗忘曲线。`,
              timestamp: new Date().toISOString(),
              annotationId: event.payload.annotation_id,
            };
            addChatMessage(currentConversationId, message);
          }
        }
      )
    );

    // ============= 5. 常见错误检测 =============
    listeners.push(
      listen<{
        topic: string
        mistake: string
        mistake_count: number
        total_students: number
        correction: string
        explanation?: string
      }>('common_mistake_detected', (event) => {
        console.log('⚠️ 检测到常见错误:', event.payload.mistake);

        if (options.autoAddMessages && currentConversationId && addChatMessage) {
          const percentage = Math.round(
            (event.payload.mistake_count / event.payload.total_students) * 100
          );

          const message = {
            id: `msg_${Date.now()}`,
            role: 'assistant' as const,
            content: `🚫 **注意：常见错误检测**

**错误**: ${event.payload.mistake}
📊 班级中 ${percentage}% 的学生 (${event.payload.mistake_count}/${event.payload.total_students}) 都在这里失手

**正确理解**: ${event.payload.correction}

${event.payload.explanation ? `**深度解释**: ${event.payload.explanation}` : ''}`,
            timestamp: new Date().toISOString(),
          };
          addChatMessage(currentConversationId, message);
        }
      })
    );

    // 🔥 修复漏洞#6：添加更多事件监听器以完善后端事件链
    // ============= 6. 考试截止提醒 =============
    listeners.push(
      listen<{ deadline: number; days_remaining: number; message: string }>(
        'deadline_alert',
        (event) => {
          console.log('🔥 考试截止提醒');

          if (options.autoAddMessages && currentConversationId && addChatMessage) {
            const message = {
              id: `msg_${Date.now()}`,
              role: 'assistant' as const,
              content: `🔥 **考试倒计时提醒**\n\n距离你的目标日期还有 **${event.payload.days_remaining} 天**。\n\n${event.payload.message}\n\n现在是冲刺阶段，建议集中力量突破重点难点。我已经为你制定了复习计划。`,
              timestamp: new Date().toISOString(),
            };
            addChatMessage(currentConversationId, message);
          }
        }
      )
    );

    // ============= 7. 内容范围检查提醒 =============
    listeners.push(
      listen<{ message: string; priority_topics: string[] }>(
        'content_out_of_scope',
        (event) => {
          console.log('📚 内容范围检查');

          if (options.autoAddMessages && currentConversationId && addChatMessage) {
            const topicsList = event.payload.priority_topics
              .map((t) => `• ${t}`)
              .join('\n');

            const message = {
              id: `msg_${Date.now()}`,
              role: 'assistant' as const,
              content: `📌 ${event.payload.message}\n\n**建议重点关注以下主题：**\n${topicsList}`,
              timestamp: new Date().toISOString(),
            };
            addChatMessage(currentConversationId, message);
          }
        }
      )
    );

    // ============= 8. 补充资源就绪 =============
    listeners.push(
      listen<{
        message_type: string
        resources: Array<{ title: string; url: string; type: string }>
      }>('supplementary_resources_available', (event) => {
        console.log('📚 补充资源可用');

        if (options.autoAddMessages && currentConversationId && addChatMessage) {
          const resourcesList = event.payload.resources
            .map((r) => `• [${r.title}](${r.url}) (${r.type})`)
            .join('\n');

          const message = {
            id: `msg_${Date.now()}`,
            role: 'assistant' as const,
            content: `📚 **我为你找到了补充资源：**\n\n${resourcesList}`,
            timestamp: new Date().toISOString(),
          };
          addChatMessage(currentConversationId, message);
        }
      })
    );

    // ============= 等待所有监听器绑定 =============
    Promise.all(listeners)
      .then((unlisteners) => {
        unlistenerRef.current = unlisteners;
        console.log('✅ 后端事件监听器启动完成，共', unlisteners.length, '个监听器');
      })
      .catch((error) => {
        console.error('❌ 事件监听器启动失败:', error);
        options.onError?.(error);
      });

    // 清理函数
    return () => {
      unlistenerRef.current.forEach((unlisten) => {
        unlisten();
      });
      console.log('🔌 已断开所有事件监听');
    };
  }, [addChatMessage, currentConversationId, options, updateLearningGoal]);
}

/// 通知系统类型
export interface Notification {
  id: string
  type: 'info' | 'success' | 'warning' | 'error'
  message: string
  timestamp: number
  duration?: number
}

/// 通知系统类型
export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  message: string;
  timestamp: number;
  duration?: number;
}
