/**
 * 前端交互监控 Hook
 * 
 * 职责：
 * 1. 追踪用户在文档上的交互（滚动、鼠标悬停、高亮、点击）
 * 2. 计算停留时长和卡顿检测的基础数据
 * 3. 定期将交互数据发送到 Tauri 中枢
 * 4. Tauri 将数据转发给后端进行复杂分析
 * 
 * 数据流：用户交互 → (前端记录) → Tauri → 后端分析 → 核心决策
 */

import { useEffect, useRef, useCallback, useMemo } from 'react';
import { useAppStore } from '../store/appStore';
import { invoke } from '@tauri-apps/api/core';
import type { InteractionHistory } from '../types';

interface InteractionConfig {
  enableTracking: boolean
  recordDelay: number // ms between recording scroll events
  highlightDebounce: number // ms to debounce highlight detection
  batchSize: number // 累积多少条交互后批量上传
  flushInterval: number // 多长时间强制上传一次（毫秒）
}

const DEFAULT_CONFIG: InteractionConfig = {
  enableTracking: true,
  recordDelay: 500,
  highlightDebounce: 300,
  batchSize: 20,
  flushInterval: 30000, // 30 秒
};

export interface TrackableInteraction {
  type: 'scroll' | 'highlight' | 'click' | 'hover' | 'page_change'
  timestamp: number
  documentId?: string
  pageNumber?: number
  duration?: number
  metadata?: Record<string, unknown>
}

export function useInteractionMonitor(
  config: Partial<InteractionConfig> = {},
  options?: {
    documentId?: string
    pageNumber?: number
    onError?: (error: Error) => void
  }
) {
  const finalConfig = useMemo(() => ({ ...DEFAULT_CONFIG, ...config }), [config]);
  const { recordInteraction, currentDocument, currentUserId } = useAppStore();

  const scrollTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const highlightTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastScrollPosRef = useRef<number>(0);
  const pageStayTimeRef = useRef<number>(0);
  const batchInteractionsRef = useRef<TrackableInteraction[]>([]);
  const flushTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const flushInteractionsRef = useRef<(() => Promise<void>) | null>(null);

  const documentId = options?.documentId || currentDocument?.id;
  const retryCountRef = useRef<number>(0);
  const maxRetries = 3; // 最多重试3次

  /**
   * 上报交互数据到 Tauri
   * 🔥 修复漏洞#11：增加重试机制和错误恢复
   * Tauri 将批量转发给后端
   */
  const flushInteractions = useCallback(async () => {
    if (batchInteractionsRef.current.length === 0) return;

    const interactions = [...batchInteractionsRef.current];
    const batchId = `batch_${Date.now()}`;

    try {
      await invoke('report_interactions', {
        interactions,
        batch_id: batchId,
        document_id: documentId,
      } as Record<string, unknown>);

      console.log('✅ 上报', interactions.length, '条交互记录到 Tauri（批次:', batchId, '）');
      batchInteractionsRef.current = [];
      retryCountRef.current = 0; // 重置重试计数
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      console.error(
        `❌ 上报交互失败 (尝试 ${retryCountRef.current + 1}/${maxRetries}):`,
        errorMsg
      );

      // 🔥 重试逻辑：指数退避
      if (retryCountRef.current < maxRetries) {
        retryCountRef.current += 1;
        const retryDelay = Math.pow(2, retryCountRef.current) * 1000; // 2s, 4s, 8s
        console.log(`   ⏳ ${retryDelay / 1000}秒后重试...`);

        setTimeout(() => {
          flushInteractionsRef.current?.();
        }, retryDelay);
      } else {
        // 重试次数耗尽，采用降级策略
        console.error('   💾 超过最大重试次数，尝试本地存储备份...');
        
        // 降级方案：将数据保存到浏览器localStorage，等待恢复
        try {
          const backup = localStorage.getItem('interaction_backup') || '[]';
          const backupData = JSON.parse(backup);
          backupData.push(...interactions);
          localStorage.setItem('interaction_backup', JSON.stringify(backupData));
          console.log('   ✅ 已备份到本地存储');
        } catch (storageError) {
          console.error('   ❌ 本地存储失败:', storageError);
        }

        // 不清空队列，等待下次重试（用户恢复网络连接时）
        options?.onError?.(
          new Error(
            `交互数据上报失败，已达最大重试次数。数据已缓存。网络恢复后将自动重新上报。`
          )
        );
      }
    }
  }, [documentId, options]);

  // 保存 flushInteractions 到 ref，供 setTimeout 回调使用
  useEffect(() => {
    flushInteractionsRef.current = flushInteractions;
  }, [flushInteractions]);

  /**
   * 记录单个交互，添加到批量队列
   */
  const addInteractionToBatch = useCallback(
    (interaction: TrackableInteraction) => {
      // 统一添加 documentId 和 pageNumber
      const enrichedInteraction: TrackableInteraction = {
        ...interaction,
        documentId: interaction.documentId || documentId,
        pageNumber: interaction.pageNumber || options?.pageNumber,
      };

      // 前端本地记录（用于 UI 显示）
      recordInteraction({
        ...enrichedInteraction,
        userId: currentUserId || 'anonymous',
        type: enrichedInteraction.type as InteractionHistory['type'],
      } as Omit<InteractionHistory, 'id'> & { id?: string });

      // 添加到 Tauri 上报队列
      batchInteractionsRef.current.push(enrichedInteraction);

      // 达到批量大小时自动上报
      if (batchInteractionsRef.current.length >= finalConfig.batchSize) {
        flushInteractions();
      }
    },
    [
      documentId,
      options?.pageNumber,
      recordInteraction,
      flushInteractions,
      finalConfig.batchSize,
      currentUserId,
    ]
  );

  useEffect(() => {
    if (!finalConfig.enableTracking) return;

    // 初始化页面停留时间
    pageStayTimeRef.current = Date.now();

    // ============= 1. 滚动事件追踪 =============
    const handleScroll = (e: Event) => {
      const target = e.target as Element;
      const scrollPos = target.scrollTop || 0;

      if (scrollTimerRef.current) clearTimeout(scrollTimerRef.current);

      scrollTimerRef.current = setTimeout(() => {
        addInteractionToBatch({
          type: 'scroll',
          timestamp: Date.now(),
          metadata: {
            scrollPosition: scrollPos,
            scrollDirection: scrollPos > lastScrollPosRef.current ? 'down' : 'up',
            scrollDelta: Math.abs(scrollPos - lastScrollPosRef.current),
          },
        });
        lastScrollPosRef.current = scrollPos;
      }, finalConfig.recordDelay);
    };

    // ============= 2. 文本高亮追踪 =============
    const handleTextSelect = () => {
      const selection = window.getSelection();
      if (!selection || selection.toString().length === 0) return;

      if (highlightTimerRef.current) clearTimeout(highlightTimerRef.current);

      highlightTimerRef.current = setTimeout(() => {
        addInteractionToBatch({
          type: 'highlight',
          timestamp: Date.now(),
          metadata: {
            selectedText: selection.toString().substring(0, 100),
            selectionLength: selection.toString().length,
          },
        });
      }, finalConfig.highlightDebounce);
    };

    // ============= 3. 点击事件追踪 =============
    const handleClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      addInteractionToBatch({
        type: 'click',
        timestamp: Date.now(),
        metadata: {
          targetClass: target.className,
          targetId: target.id,
          clickX: e.clientX,
          clickY: e.clientY,
          targetText: target.textContent?.substring(0, 50) || '',
        },
      });
    };

    // ============= 4. 鼠标悬停追踪 =============
    let hoverStartTime: number | null = null;
    const handleMouseEnter = () => {
      hoverStartTime = Date.now();
    };

    const handleMouseLeave = () => {
      if (hoverStartTime) {
        const duration = Date.now() - hoverStartTime;
        addInteractionToBatch({
          type: 'hover',
          timestamp: Date.now(),
          duration,
          metadata: {
            hoverDuration: duration,
          },
        });
        hoverStartTime = null;
      }
    };

    // ============= 5. 页面可见性变化 =============
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        // 用户回到这个标签页
        addInteractionToBatch({
          type: 'page_change',
          timestamp: Date.now(),
          metadata: {
            visibility: 'visible',
            stayTimeSinceLastVisible: Date.now() - pageStayTimeRef.current,
          },
        });
        pageStayTimeRef.current = Date.now();
      } else {
        // 用户切走标签页，计算停留时长
        const stayTime = Date.now() - pageStayTimeRef.current;
        console.log(`📌 用户离开，在此页停留 ${stayTime}ms`);

        // 如果停留超过 3 分钟（180000ms），主动上报给 Tauri 进行卡顿检测
        if (stayTime > 180000) {
          invoke('check_confusion', {
            document_id: documentId,
            page_number: options?.pageNumber,
            time_elapsed_sec: Math.floor(stayTime / 1000),
          } as Record<string, unknown>).catch((error: unknown) => {
            console.error('❌ 卡顿检测请求失败:', error);
            options?.onError?.(error as Error);
          });
        }
      }
    };

    // ============= 6. 挂载监听器 =============
    const contentArea = document.querySelector('[data-content-area]');
    if (contentArea) {
      contentArea.addEventListener('scroll', handleScroll);
    }

    document.addEventListener('selectionchange', handleTextSelect);
    document.addEventListener('click', handleClick, true); // 捕获阶段
    document.addEventListener('visibilitychange', handleVisibilityChange);

    // 针对可悬停元素的追踪
    const hoverElements = document.querySelectorAll('[data-hoverable]');
    hoverElements.forEach((el) => {
      el.addEventListener('mouseenter', handleMouseEnter);
      el.addEventListener('mouseleave', handleMouseLeave);
    });

    // ============= 7. 定期强制上报 =============
    flushTimerRef.current = setInterval(() => {
      if (batchInteractionsRef.current.length > 0) {
        console.log(
          `⏰ 定时上报 ${batchInteractionsRef.current.length} 条交互（${finalConfig.flushInterval}ms 间隔）`
        );
        flushInteractions();
      }
    }, finalConfig.flushInterval);

    // ============= 8. 清理 =============
    return () => {
      // 清理定时器
      if (scrollTimerRef.current) clearTimeout(scrollTimerRef.current);
      if (highlightTimerRef.current) clearTimeout(highlightTimerRef.current);
      if (flushTimerRef.current) clearInterval(flushTimerRef.current);

      // 移除事件监听
      if (contentArea) {
        contentArea.removeEventListener('scroll', handleScroll);
      }
      document.removeEventListener('selectionchange', handleTextSelect);
      document.removeEventListener('click', handleClick, true);
      document.removeEventListener('visibilitychange', handleVisibilityChange);

      hoverElements.forEach((el) => {
        el.removeEventListener('mouseenter', handleMouseEnter);
        el.removeEventListener('mouseleave', handleMouseLeave);
      });

      // 离开前上报剩余数据
      flushInteractions();
    };
  }, [
    finalConfig,
    addInteractionToBatch,
    documentId,
    options,
    flushInteractions,
  ]);

  // 返回公开的工具函数
  return {
    /**
     * 手动记录交互（用于非标准的用户行为）
     */
    recordManualInteraction: (
      type: TrackableInteraction['type'],
      metadata?: Record<string, unknown>
    ) => {
      addInteractionToBatch({
        type,
        timestamp: Date.now(),
        metadata,
      });
    },

    /**
     * 立即上报队列中的所有交互
     */
    flush: flushInteractions,

    /**
     * 获取当前队列中的交互数量
     */
    getPendingCount: () => batchInteractionsRef.current.length,
  };
}
