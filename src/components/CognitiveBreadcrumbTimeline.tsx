/**
 * 认知痕迹时间线
 * 展示学生的学习足迹：何时困惑→何时理解→何时掌握
 * 这是 WayFare "与资料深度挂钩" 特性的核心体现
 */
import { useState } from 'react';
import { Calendar, Map, TrendingUp, AlertCircle, Lightbulb, Award } from 'lucide-react';
import { motion } from 'motion/react';
import type { CognitiveBreadcrumb } from '../types';

interface CognitiveBreadcrumbTimelineProps {
  documentId: string;
  annotationId?: string;
}

export function CognitiveBreadcrumbTimeline({
  documentId,
  annotationId,
}: CognitiveBreadcrumbTimelineProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // 模拟数据 - 实际应从 store 获取
  const traces: CognitiveBreadcrumb[] = [
    {
      id: 'trace_1',
      userId: 'user_1',
      documentId,
      annotationId: annotationId || 'anno_1',
      type: 'first_confusion',
      description: '第一次遇到这个概念时感到困惑',
      timestamp: new Date('2024-01-15').getTime(),
      pedagogicalInsight: '学生容易混淆条件概率和联合概率',
    },
    {
      id: 'trace_2',
      userId: 'user_1',
      documentId,
      annotationId: annotationId || 'anno_1',
      type: 'clarification',
      description: 'AI 用树形图讲解，用类比解释',
      timestamp: new Date('2024-01-16').getTime(),
      conversationId: 'conv_1',
      pedagogicalInsight: '树形图这个类比很有效',
    },
    {
      id: 'trace_3',
      userId: 'user_1',
      documentId,
      annotationId: annotationId || 'anno_1',
      type: 'deepening',
      description: '在做练习题时加深了理解',
      timestamp: new Date('2024-02-10').getTime(),
      pedagogicalInsight: '通过三道例题，学生的理解从 60% 提升到 85%',
    },
    {
      id: 'trace_4',
      userId: 'user_1',
      documentId,
      annotationId: annotationId || 'anno_1',
      type: 'mastery',
      description: '完全掌握，能用自己的方式讲解',
      timestamp: new Date('2024-03-01').getTime(),
      pedagogicalInsight: '从困惑到精通用了 45 天',
    },
    {
      id: 'trace_5',
      userId: 'user_1',
      documentId,
      annotationId: annotationId || 'anno_1',
      type: 'application',
      description: '在新的问题中应用了这个概念',
      timestamp: new Date('2024-03-15').getTime(),
      pedagogicalInsight: '迁移成功，学生能举一反三',
    },
  ];

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'first_confusion':
        return <AlertCircle size={20} />;
      case 'clarification':
        return <Lightbulb size={20} />;
      case 'deepening':
        return <TrendingUp size={20} />;
      case 'mastery':
        return <Award size={20} />;
      case 'application':
        return <Map size={20} />;
      default:
        return <Calendar size={20} />;
    }
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'first_confusion':
        return '[Confused] First Encounter';
      case 'clarification':
        return '[Explained] Was Explained';
      case 'deepening':
        return '[Progress] Deeper Understanding';
      case 'mastery':
        return '[Mastered] Complete Mastery';
      case 'application':
        return '[Applied] Applied';
      default:
        return '[Event] Event';
    }
  };

  const getTypeTextColor = (type: string) => {
    switch (type) {
      case 'first_confusion':
        return 'text-red-700';
      case 'clarification':
        return 'text-blue-700';
      case 'deepening':
        return 'text-yellow-700';
      case 'mastery':
        return 'text-green-700';
      case 'application':
        return 'text-purple-700';
      default:
        return 'text-stone-700';
    }
  };

  const daysDuration = Math.floor(
    (traces[traces.length - 1].timestamp - traces[0].timestamp) / (1000 * 60 * 60 * 24)
  );

  return (
    <div className="bg-white rounded-lg border border-stone-200 overflow-hidden">
      {/* Header */}
      <div className="bg-white px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-bold text-stone-900 mb-1">🎩 你的认知之旅</h3>
        <p className="text-sm text-stone-600">
          从首次困惑到完全掌握的完整学习足迹（耗时 {daysDuration} 天）
        </p>
      </div>

      {/* Timeline */}
      <div className="p-6">
        {/* 每个步骤 */}
        <div className="relative">
          {/* Vertical line */}
          <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gray-300" />

          {/* Timeline items */}
          <div className="space-y-6">
            {traces.map((trace, idx) => (
              <motion.div
                key={trace.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.1 }}
                className="relative pl-20"
              >
                {/* Node */}
                <div className={`absolute left-0 w-16 h-16 rounded-full bg-white border-4 border-gray-200 flex items-center justify-center ${getTypeTextColor(trace.type)}`}>
                  {getTypeIcon(trace.type)}
                </div>

                {/* Content */}
                <div
                  className="bg-stone-50 rounded-lg p-4 cursor-pointer hover:shadow-md transition-shadow"
                  onClick={() =>
                    setExpandedId(expandedId === trace.id ? null : trace.id)
                  }
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        <span className="font-semibold text-stone-900">
                          {getTypeLabel(trace.type)}
                        </span>
                        <span className="text-xs text-stone-500">
                          {new Date(trace.timestamp).toLocaleDateString('zh-CN')}
                        </span>
                      </div>
                      <p className="text-sm text-stone-700">{trace.description}</p>

                      {/* Expandable pedagogical insight */}
                      {expandedId === trace.id && trace.pedagogicalInsight && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          exit={{ opacity: 0, height: 0 }}
                          className="mt-3 pt-3 border-t border-stone-200"
                        >
                          <p className="text-xs text-gray-700 bg-gray-100 px-3 py-2 rounded">
                            📊 <strong>系统观察：</strong> {trace.pedagogicalInsight}
                          </p>
                        </motion.div>
                      )}
                    </div>

                    {trace.pedagogicalInsight && (
                      <div className="ml-3 text-stone-400 hover:text-stone-600">
                        {expandedId === trace.id ? '▼' : '▶'}
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Summary */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: traces.length * 0.1 }}
          className="mt-8 pt-6 border-t border-stone-200"
        >
          <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg p-6 space-y-4">
            <h4 className="font-semibold text-stone-900 flex items-center space-x-2">
              <TrendingUp size={20} className="text-indigo-600" />
              <span>学习统计</span>
            </h4>

            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <div className="text-3xl font-bold text-indigo-600">
                  {daysDuration}
                </div>
                <div className="text-xs text-stone-600 mt-1">天</div>
                <p className="text-xs text-stone-600">从困惑到掌握的耗时</p>
              </div>
              <div>
                <div className="text-3xl font-bold text-green-600">
                  {traces.filter((t) => t.type === 'clarification').length}
                </div>
                <div className="text-xs text-stone-600 mt-1">次讲解</div>
                <p className="text-xs text-stone-600">AI 帮你理解的次数</p>
              </div>
            </div>

            <div className="bg-white rounded p-3 text-xs text-stone-700 space-y-2">
              <p>
                💡 <strong>核心洞察：</strong> 树形图和具体例子对你特别有效。加深后来使用它们来讲解相关概念。
              </p>
              <p>
                <strong>Suggestion:</strong> Review this topic in 3 weeks (Ebbinghaus forgetting curve). The system will remind you.
              </p>
              <p>
                <strong>Transfer Success:</strong> You can now apply this concept to new scenarios, indicating deep understanding.
              </p>
            </div>
          </div>
        </motion.div>

        {/* No more records placeholder */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: traces.length * 0.1 + 0.3 }}
          className="mt-8 text-center"
        >
          <p className="text-xs text-stone-500">
            • 下次学习交互，新的痕迹就会被记录在这里 •
          </p>
        </motion.div>
      </div>
    </div>
  );
}
