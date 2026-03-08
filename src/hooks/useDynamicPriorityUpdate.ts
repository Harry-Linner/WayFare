/**
 * 动态优先级更新 Hook
 * 
 * 漏洞8修复：根据用户的交互数据自动调整批注优先级
 * 如果学生在某个概念上停留多次且仍未掌握，系统会自动调高其优先级
 */

import { useEffect, useCallback } from 'react';
import { useAppStore } from '../store/appStore';
import type { LearningPriorityType } from '../types';

export function useDynamicPriorityUpdate(documentId?: string) {
  const { 
    annotations,
    batchUpdateAnnotations,
    getInteractionsByDocument,
  } = useAppStore();

  // 定期检查交互数据，更新优先级
  const updatePrioritiesBasedOnInteractions = useCallback(() => {
    if (!documentId) return;

    const interactions = getInteractionsByDocument(documentId);

    // 按批注ID统计停留时间和交互频率
    const interactionStats: Record<string, { count: number; totalDuration: number }> = {};

    interactions.forEach((interaction) => {
      if (interaction.metadata?.annotation_id) {
        const annotationId = interaction.metadata.annotation_id as string;
        if (!interactionStats[annotationId]) {
          interactionStats[annotationId] = { count: 0, totalDuration: 0 };
        }
        interactionStats[annotationId].count += 1;
        interactionStats[annotationId].totalDuration += interaction.metadata.duration as number || 0;
      }
    });

    // 🔥 根据交互频率调整优先级
    const priorityUpdates: Record<string, { priority: LearningPriorityType }> = {};

    Object.entries(interactionStats).forEach(([annotationId, stats]) => {
      const annotation = annotations.find((a) => a.id === annotationId);
      if (!annotation) return;

      // 规则：
      // - 如果交互>5次且未掌握 → 升级为 critical/high
      // - 如果交互1-2次 → 保持或略降
      // - 如果已掌握 → review 或 low
      
      let newPriority: LearningPriorityType = annotation.priority;

      if (annotation.confidence === 'mastered') {
        newPriority = 'review';
      } else if (stats.count > 5 && annotation.confidence !== 'high') {
        // 多次停留但未掌握 = 重点
        newPriority = annotation.priority === 'critical' ? 'critical' : 'high';
      } else if (stats.count > 8) {
        // 非常频繁停留 + 仍未掌握 = 考试重点
        newPriority = 'critical';
      }

      if (newPriority !== annotation.priority) {
        priorityUpdates[annotationId] = { priority: newPriority };
        console.log(
          `🔄 更新优先级: ${annotationId} (交互${stats.count}次) ${annotation.priority} → ${newPriority}`
        );
      }
    });

    // 批量应用更新
    if (Object.keys(priorityUpdates).length > 0) {
      const annotationIds = Object.keys(priorityUpdates);
      const updates = priorityUpdates[annotationIds[0]];
      batchUpdateAnnotations(annotationIds, updates);
      console.log(`✅ 已更新 ${annotationIds.length} 个批注的优先级`);
    }
  }, [documentId, annotations, batchUpdateAnnotations, getInteractionsByDocument]);

  // 每5分钟检查一次
  useEffect(() => {
    const timer = setInterval(() => {
      updatePrioritiesBasedOnInteractions();
    }, 5 * 60 * 1000);

    return () => clearInterval(timer);
  }, [updatePrioritiesBasedOnInteractions]);

  // 立即检查一次
  useEffect(() => {
    updatePrioritiesBasedOnInteractions();
  }, [updatePrioritiesBasedOnInteractions]);

  return { updatePrioritiesBasedOnInteractions };
}
