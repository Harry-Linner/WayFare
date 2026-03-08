/**
 * 学习历程面板
 * 展示学生的认知痕迹：
 * - 之前在哪里卡住过
 * - AI当时的讲解
 * - 学生后来的理解深化
 * - 掌握时间轴
 * 
 * 这实现了WayFare的核心承诺：学习不是一次性消费，而是可回溯、可复盘的过程
 */

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { ChevronDown, Brain, MessageCircle, CheckCircle } from 'lucide-react';
import { useTauriCommands } from '../hooks/useTauriCommands';

interface LearningHistoryPanelProps {
  documentId: string;
}


interface LearningEvent {
  id: string;
  timestamp: number;
  type: 'first_encounter' | 'confusion' | 'ai_explanation' | 'breakthrough' | 'mastery';
  content: string;
  relatedAnnotations: string[];
  metadata?: {
    difficulty?: string;
    masteringTime?: number;
  };
}

export function LearningHistoryPanel({ documentId }: LearningHistoryPanelProps) {
  const [expandedEvents, setExpandedEvents] = useState<Set<string>>(new Set());
  const [learningEvents, setLearningEvents] = useState<LearningEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [sortBy, setSortBy] = useState<'time' | 'event_type'>('time');

  const { getDocumentAnnotations } = useTauriCommands();

  const loadLearningEvents = useCallback(async () => {
    setLoading(true);
    try {
      // 从数据库获取文档的所有批注
      const savedAnnotations = await getDocumentAnnotations(documentId);

      // 构建学习事件时间线
      const events: LearningEvent[] = [];

      for (const anno of savedAnnotations) {
        // 普通批注
        if (anno.category && ['core_concept', 'learning_strategy', 'misunderstanding', 'exam_preparation'].includes(anno.category)) {
          events.push({
            id: anno.id,
            timestamp: (anno.createdAt || 0) * 1000,
            type: 'first_encounter',
            content: anno.content,
            relatedAnnotations: anno.relatedKeywords || [],
            metadata: {
              difficulty: anno.priority || 'medium',
            },
          });
        }
      }

      // 按时间排序
      events.sort((a, b) => a.timestamp - b.timestamp);

      setLearningEvents(events);
    } catch (error) {
      console.error('Failed to load learning events:', error);
    } finally {
      setLoading(false);
    }
  }, [documentId, getDocumentAnnotations]);

  useEffect(() => {
    loadLearningEvents();
  }, [documentId, loadLearningEvents]);

  const toggleExpanded = (eventId: string) => {
    setExpandedEvents((prev) => {
      const next = new Set(prev);
      if (next.has(eventId)) {
        next.delete(eventId);
      } else {
        next.add(eventId);
      }
      return next;
    });
  };

  const sortedEvents = [...learningEvents].sort((a, b) => {
    if (sortBy === 'time') {
      return a.timestamp - b.timestamp;
    }
    const typeOrder = {
      first_encounter: 0,
      confusion: 1,
      ai_explanation: 2,
      breakthrough: 3,
      mastery: 4,
    };
    return typeOrder[a.type] - typeOrder[b.type];
  });

  const getEventIcon = (type: LearningEvent['type']) => {
    switch (type) {
      case 'first_encounter':
        return '[1st]';
      case 'confusion':
        return '[?]';
      case 'ai_explanation':
        return '[AI]';
      case 'breakthrough':
        return '[✓]';
      case 'mastery':
        return '[✓✓]';
      default:
        return '•';
    }
  };

  const getEventLabel = (type: LearningEvent['type']) => {
    const labels = {
      first_encounter: '首次接触',
      confusion: '遇到困难',
      ai_explanation: 'Agent讲解',
      breakthrough: '突破点',
      mastery: '已掌握',
    };
    return labels[type];
  };


  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
      return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    } else if (diffDays === 1) {
      return '昨天';
    } else if (diffDays < 7) {
      return `${diffDays}天前`;
    } else {
      return date.toLocaleDateString('zh-CN');
    }
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <p className="text-stone-500">加载学习历程中...</p>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto flex flex-col bg-white">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200">
        <h3 className="font-semibold text-gray-900 mb-1">认知痕迹</h3>
        <p className="text-xs text-gray-500 mb-2">
          你的学习旅程：每次与 Agent 的互动都会在此留下痕迹。
        </p>

        <div className="flex space-x-2 text-xs">
          <button
            onClick={() => setSortBy('time')}
            className={`px-2 py-1 rounded ${
              sortBy === 'time'
                ? 'bg-gray-200 text-gray-900'
                : 'bg-white text-gray-500 hover:bg-gray-100'
            }`}
          >
            时间
          </button>
          <button
            onClick={() => setSortBy('event_type')}
            className={`px-2 py-1 rounded ${
              sortBy === 'event_type'
                ? 'bg-gray-200 text-gray-900'
                : 'bg-white text-gray-500 hover:bg-gray-100'
            }`}
          >
            类型
          </button>
        </div>
      </div>

      {/* Timeline */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {sortedEvents.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center py-8">
            <Brain size={40} className="text-stone-300 mb-3" />
            <p className="text-stone-600 font-medium">还没有学习记录</p>
            <p className="text-xs text-stone-500 mt-1">开始与 Agent 互动，你的学习之旅将被记录下来</p>
          </div>
        ) : (
          <>
            {sortedEvents.map((event, idx) => (
              <motion.div
                key={event.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
              >
                <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                  <button
                    onClick={() => toggleExpanded(event.id)}
                    className="w-full p-3 hover:bg-black/5 transition-colors text-left"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-2 flex-1">
                        <span className="text-sm mt-0.5">{getEventIcon(event.type)}</span>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2">
                            <span className="text-xs font-semibold text-gray-800">
                              {getEventLabel(event.type)}
                            </span>
                            {event.metadata?.difficulty && (
                              <span className={`text-xs px-1.5 py-0.5 rounded ${
                                event.metadata.difficulty === 'high'
                                  ? 'bg-red-100 text-red-700'
                                  : event.metadata.difficulty === 'medium'
                                    ? 'bg-yellow-100 text-yellow-700'
                                    : 'bg-blue-100 text-blue-700'
                              }`}>
                                {event.metadata.difficulty === 'high' ? '难' : event.metadata.difficulty === 'medium' ? '中' : '易'}
                              </span>
                            )}
                          </div>
                          <p className="text-xs text-stone-600 mt-1 line-clamp-2">
                            {event.content.substring(0, 80)}...
                          </p>
                        </div>
                      </div>
                      <div className="flex flex-col items-end space-y-1 ml-2">
                        <span className="text-xs text-gray-500 whitespace-nowrap">
                          {formatTime(event.timestamp)}
                        </span>
                        <motion.div
                          animate={{ rotate: expandedEvents.has(event.id) ? 180 : 0 }}
                          transition={{ duration: 0.2 }}
                        >
                          <ChevronDown size={14} className="text-stone-400" />
                        </motion.div>
                      </div>
                    </div>
                  </button>

                  {/* Expanded Content */}
                  <AnimatePresence>
                    {expandedEvents.has(event.id) && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.2 }}
                        className="border-t border-stone-300 bg-white/50 p-3 space-y-2"
                      >
                        <p className="text-xs text-stone-700 leading-relaxed">{event.content}</p>

                        {event.relatedAnnotations.length > 0 && (
                          <div className="pt-2 border-t border-stone-200">
                            <p className="text-xs font-medium text-stone-600 mb-1">相关概念：</p>
                            <div className="flex flex-wrap gap-1">
                              {event.relatedAnnotations.slice(0, 3).map((keyword) => (
                                <span
                                  key={keyword}
                                  className="text-xs bg-stone-100 text-stone-600 px-2 py-0.5 rounded"
                                >
                                  {keyword}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        <div className="flex items-center justify-between pt-2 text-xs text-stone-500">
                          {event.type === 'ai_explanation' && (
                            <span className="flex items-center space-x-1">
                              <MessageCircle size={12} />
                              <span>Agent的讲解</span>
                            </span>
                          )}
                          {event.type === 'mastery' && (
                            <span className="flex items-center space-x-1 text-green-600">
                              <CheckCircle size={12} />
                              <span>已掌握</span>
                            </span>
                          )}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </motion.div>
            ))}
          </>
        )}
      </div>

      {/* Footer Tips (minimal) */}
      <div className="px-4 py-2 border-t border-gray-200 text-xs text-gray-500">
        记录自动保存，安心学习。
      </div>
    </div>
  );
}
