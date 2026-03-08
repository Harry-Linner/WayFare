/// 优先级过滤和显示面板
/// 帮助学生快速识别学习的优先级，集中精力在重点内容上

import { useState } from 'react';
import { Filter, Eye, EyeOff } from 'lucide-react';
import type { EnhancedAnnotation, LearningPriorityType } from '../types';
import { LearningPriority } from '../types';
import { motion } from 'motion/react';

interface PriorityPanelProps {
  annotations: EnhancedAnnotation[];
  onFilterChange?: (priorities: LearningPriorityType[]) => void;
  onAnnotationClick?: (annotationId: string) => void;
}

export function PriorityPanel({
  annotations,
  onFilterChange,
  onAnnotationClick,
}: PriorityPanelProps) {
  const [selectedPriorities, setSelectedPriorities] = useState<LearningPriorityType[]>([
    LearningPriority.CRITICAL,
    LearningPriority.HIGH,
    LearningPriority.MEDIUM,
    LearningPriority.LOW,
    LearningPriority.REVIEW,
  ]);
  const [isCollapsed, setIsCollapsed] = useState(false);

  const priorities: Array<{
    value: LearningPriorityType;
    label: string;
    icon: string;
    color: string;
    bgColor: string;
  }> = [
    {
      value: LearningPriority.CRITICAL,
      label: '考试重点',
      icon: '🔴',
      color: 'text-red-600',
      bgColor: 'bg-red-50 hover:bg-red-100',
    },
    {
      value: LearningPriority.HIGH,
      label: '重要',
      icon: '🟠',
      color: 'text-orange-600',
      bgColor: 'bg-orange-50 hover:bg-orange-100',
    },
    {
      value: LearningPriority.MEDIUM,
      label: '中等',
      icon: '🟡',
      color: 'text-amber-600',
      bgColor: 'bg-amber-50 hover:bg-amber-100',
    },
    {
      value: LearningPriority.LOW,
      label: '细节',
      icon: '🔵',
      color: 'text-blue-600',
      bgColor: 'bg-blue-50 hover:bg-blue-100',
    },
    {
      value: LearningPriority.REVIEW,
      label: '复习',
      icon: '🟣',
      color: 'text-purple-600',
      bgColor: 'bg-purple-50 hover:bg-purple-100',
    },
  ];

  const handlePriorityToggle = (priority: LearningPriorityType) => {
    const newSelected = selectedPriorities.includes(priority)
      ? selectedPriorities.filter((p) => p !== priority)
      : [...selectedPriorities, priority];

    setSelectedPriorities(newSelected);
    onFilterChange?.(newSelected);
  };

  // 统计每个优先级的批注数量
  const getCountByPriority = (priority: LearningPriorityType) => {
    return annotations.filter((a) => a.priority === priority).length;
  };

  // 按优先级分组的批注
  const groupedAnnotations = priorities.reduce(
    (acc, priority) => {
      acc[priority.value] = annotations.filter((a) => a.priority === priority.value);
      return acc;
    },
    {} as Record<LearningPriorityType, EnhancedAnnotation[]>
  );

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      className="bg-white border-l border-stone-200 shadow-lg overflow-hidden"
      style={{ width: isCollapsed ? '60px' : '320px' }}
    >
      {/* Header */}
      <div className="border-b border-stone-200 p-3 flex items-center justify-between">
        {!isCollapsed && (
          <div className="flex items-center space-x-2">
            <Filter size={18} className="text-indigo-600" />
            <h3 className="text-sm font-semibold text-stone-800">学习优先级</h3>
          </div>
        )}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="p-1 hover:bg-stone-100 rounded transition-colors"
          title={isCollapsed ? '展开' : '折叠'}
        >
          {isCollapsed ? <Eye size={16} /> : <EyeOff size={16} />}
        </button>
      </div>

      {!isCollapsed && (
        <div className="p-3 space-y-2 max-h-96 overflow-y-auto">
          {/* Priority Filters */}
          <div className="space-y-2 mb-4 pb-4 border-b border-stone-200">
            {priorities.map((priority) => (
              <motion.button
                key={priority.value}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => handlePriorityToggle(priority.value)}
                className={`w-full px-3 py-2 rounded-lg transition-colors flex items-center justify-between text-sm ${
                  selectedPriorities.includes(priority.value)
                    ? priority.bgColor
                    : 'bg-stone-50 opacity-40'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <span className="text-lg">{priority.icon}</span>
                  <span className="font-medium">{priority.label}</span>
                </div>
                <span className="text-xs text-stone-600 font-semibold">
                  {getCountByPriority(priority.value)}
                </span>
              </motion.button>
            ))}
          </div>

          {/* Summary Statistics */}
          <div className="bg-indigo-50 rounded-lg p-3 text-xs">
            <p className="text-indigo-900 font-semibold mb-2">学习进度</p>
            <div className="space-y-1">
              <div className="flex justify-between">
                <span>总批注数</span>
                <span className="font-semibold">{annotations.length}</span>
              </div>
              <div className="flex justify-between text-red-600">
                <span>待完成重点</span>
                <span className="font-semibold">
                  {annotations.filter(
                    (a) => a.priority === 'critical' && a.confidence !== 'mastered'
                  ).length}
                </span>
              </div>
              <div className="flex justify-between text-green-600">
                <span>已掌握</span>
                <span className="font-semibold">
                  {annotations.filter((a) => a.confidence === 'mastered').length}
                </span>
              </div>
            </div>
          </div>

          {/* Annotations by Priority */}
          <div className="mt-4 space-y-3">
            {priorities.map((priority) => {
              const items = groupedAnnotations[priority.value];
              if (items.length === 0) return null;

              return (
                <motion.div key={priority.value} className="space-y-2">
                  <div className="flex items-center space-x-2 px-2">
                    <span className="text-lg">{priority.icon}</span>
                    <span className="text-xs font-semibold text-stone-600 uppercase">
                      {priority.label}
                    </span>
                    <span className="text-xs text-stone-400">({items.length})</span>
                  </div>

                  <div className="space-y-1">
                    {items.map((annotation) => (
                      <motion.button
                        key={annotation.id}
                        whileHover={{ x: 4 }}
                        onClick={() => onAnnotationClick?.(annotation.id)}
                        className="w-full text-left p-2 rounded-lg hover:bg-stone-100 transition-colors border-l-2 border-indigo-400"
                      >
                        <p className="text-xs font-medium text-stone-800 line-clamp-2">
                          {annotation.sourceText || annotation.content}
                        </p>
                        <div className="flex items-center space-x-2 mt-1">
                          <span className="text-xs text-stone-500">
                            {annotation.category}
                          </span>
                          {annotation.confidence === 'mastered' && (
                            <span className="text-xs text-green-600 font-semibold">✓ 已掌握</span>
                          )}
                        </div>
                      </motion.button>
                    ))}
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      )}
    </motion.div>
  );
}
