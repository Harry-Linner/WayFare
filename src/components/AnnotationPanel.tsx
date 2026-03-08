/**
 * 批注面板组件
 * 
 * 漏洞5修复：双列并排显示模式
 * 在右侧栏动态显示当前阅读位置相关的所有内容：
 * - 该位置的所有批注
 * - 补充学习资源
 * - 相关问题
 * 
 * 这是实现"与原学习资料并排呈现补充内容"的核心
 */

import { useState } from 'react';
import { ChevronDown, ChevronUp, BookOpen, LinkIcon, AlertCircle, Award } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { useAppStore } from '../store/appStore';

interface AnnotationPanelProps {
  documentId: string;
  currentPage?: number;
  currentPosition?: { x: number; y: number };
  onAnnotationSelect?: (annotationId: string) => void;
}

interface SupplementaryResource {
  id: string;
  title: string;
  type: 'video' | 'article' | 'interactive' | 'exercise';
  source: string;
  url: string;
  relevanceScore: number;
  description: string;
}

export function AnnotationPanel({
  documentId,
  currentPage = 1,
  onAnnotationSelect,
}: AnnotationPanelProps) {
  const [expandedSections, setExpandedSections] = useState({
    annotations: true,
    resources: true,
    relatedQuestions: true,
  });

  const { getAnnotationsByDocument } = useAppStore();
  const annotations = getAnnotationsByDocument(documentId);

  // 🔥 修复漏洞#5：按页码和优先级过滤批注
  const pageAnnotations = annotations
    .filter((a) => {
      // 如果注解有页码信息，则只显示当前页的
      if (a.position?.page !== undefined) {
        return a.position.page === currentPage;
      }
      // 如果没有页码，假设是相关的
      return true;
    })
    .sort((a, b) => {
      // 按优先级排序（critical > high > medium > low > review）
      const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3, review: 4 };
      const aPriority = priorityOrder[a.priority as keyof typeof priorityOrder] ?? 5;
      const bPriority = priorityOrder[b.priority as keyof typeof priorityOrder] ?? 5;
      return aPriority - bPriority;
    });

  // 模拟补充资源（真实实现时应从后端Tauri获取）
  const supplementaryResources: SupplementaryResource[] = [
    {
      id: 'res_1',
      title: '相关概念讲解视频',
      type: 'video',
      source: 'Khan Academy',
      url: 'https://example.com/video',
      relevanceScore: 0.95,
      description: '更深入的概念讲解，配合你的学习材料可以提升理解深度',
    },
    {
      id: 'res_2',
      title: '维基百科详细条目',
      type: 'article',
      source: 'Wikipedia',
      url: 'https://example.com/wiki',
      relevanceScore: 0.88,
      description: '权威的百科知识，包含历史背景和相关扩展知识',
    },
    {
      id: 'res_3',
      title: '交互式模拟工具',
      type: 'interactive',
      source: 'PhET Interactive',
      url: 'https://example.com/sim',
      relevanceScore: 0.92,
      description: '拖动参数观察现象，加深对原理的理解',
    },
  ];

  // 常见问题示例
  const relatedQuestions = [
    '这个概念与前一章的内容有什么关系？',
    '如何在实际问题中应用这个知识点？',
    '考试时常见的陷阱有哪些？',
    '这与教科书上的例题有何不同？',
  ];

  // 处理切换展开/折叠
  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  const renderResourceIcon = (type: string) => {
    const iconMap: Record<string, string> = {
      video: '🎥',
      article: '📄',
      interactive: '🖱️',
      exercise: '✏️',
    };
    return iconMap[type] || '📚';
  };

  return (
    <div className="flex flex-col h-full bg-white text-gray-900 text-sm overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 flex-shrink-0">
        <h3 className="font-bold text-gray-900 flex items-center space-x-2">
          <BookOpen size={16} />
          <span>学习辅助面板</span>
        </h3>
        <p className="text-xs text-gray-500 mt-1">
          第 {currentPage} 页 • {pageAnnotations.length} 个批注
        </p>
      </div>

      {/* Content Sections */}
      <div className="flex-1 overflow-y-auto">
        {/* 批注部分 */}
        <div className="border-b border-gray-100">
          <button
            onClick={() => toggleSection('annotations')}
            className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center space-x-2">
              <AlertCircle size={16} className="text-amber-600" />
              <span className="font-semibold text-gray-800">
                本页重点 & 难点
              </span>
              <span className="text-xs bg-amber-100 text-amber-800 px-2 py-1 rounded-full">
                {pageAnnotations.length}
              </span>
            </div>
            {expandedSections.annotations ? (
              <ChevronUp size={18} />
            ) : (
              <ChevronDown size={18} />
            )}
          </button>

          <AnimatePresence>
            {expandedSections.annotations && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="space-y-2 px-4 py-3 bg-amber-50 border-t border-amber-100"
              >
                {pageAnnotations.length > 0 ? (
                  <div className="space-y-3">
                    {pageAnnotations.map((annotation) => (
                      <div
                        key={annotation.id}
                        className="bg-white rounded-lg p-3 border border-amber-200 hover:shadow-md transition-shadow cursor-pointer"
                        onClick={() => onAnnotationSelect?.(annotation.id)}
                      >
                        <div className="flex items-start space-x-2 mb-2">
                          <span
                            className={`text-xs font-bold px-2 py-1 rounded-full ${
                              annotation.priority === 'critical'
                                ? 'bg-red-100 text-red-800'
                                : annotation.priority === 'high'
                                  ? 'bg-orange-100 text-orange-800'
                                  : 'bg-blue-100 text-blue-800'
                            }`}
                          >
                            {annotation.priority === 'critical'
                              ? '考试重点'
                              : annotation.priority === 'high'
                                ? '重要'
                                : '有用'}
                          </span>
                          {annotation.confidence === 'mastered' && (
                            <Award
                              size={14}
                              className="text-green-600 flex-shrink-0"
                            />
                          )}
                        </div>

                        <p className="text-xs text-gray-700 leading-relaxed">
                          {annotation.content}
                        </p>

                        {annotation.sourceText && (
                          <p className="text-xs text-gray-500 italic mt-2 border-l-2 border-gray-300 pl-2">
                            原文: "{annotation.sourceText.substring(0, 50)}..."
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-gray-500 italic">
                    这一页还没有标注。继续阅读时，AI会自动识别重点和难点。
                  </p>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* 补充资源部分 */}
        <div className="border-b border-gray-100">
          <button
            onClick={() => toggleSection('resources')}
            className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center space-x-2">
              <LinkIcon size={16} className="text-blue-600" />
              <span className="font-semibold text-gray-800">
                补充学习资源
              </span>
              <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                {supplementaryResources.length}
              </span>
            </div>
            {expandedSections.resources ? (
              <ChevronUp size={18} />
            ) : (
              <ChevronDown size={18} />
            )}
          </button>

          <AnimatePresence>
            {expandedSections.resources && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="space-y-2 px-4 py-3 bg-blue-50 border-t border-blue-100"
              >
                {supplementaryResources.map((resource) => (
                  <a
                    key={resource.id}
                    href={resource.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block bg-white rounded-lg p-3 border border-blue-200 hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start space-x-2 mb-2">
                      <span className="text-lg">
                        {renderResourceIcon(resource.type)}
                      </span>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-semibold text-gray-800 truncate">
                          {resource.title}
                        </p>
                        <p className="text-xs text-gray-500">
                          {resource.source}
                        </p>
                      </div>
                      <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded whitespace-nowrap">
                        {(resource.relevanceScore * 100).toFixed(0)}% 相关
                      </span>
                    </div>
                    <p className="text-xs text-gray-600 leading-relaxed">
                      {resource.description}
                    </p>
                  </a>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* 相关问题部分 */}
        <div>
          <button
            onClick={() => toggleSection('relatedQuestions')}
            className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center space-x-2">
              <span className="text-lg">❓</span>
              <span className="font-semibold text-gray-800">
                你可能想问
              </span>
              <span className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded-full">
                {relatedQuestions.length}
              </span>
            </div>
            {expandedSections.relatedQuestions ? (
              <ChevronUp size={18} />
            ) : (
              <ChevronDown size={18} />
            )}
          </button>

          <AnimatePresence>
            {expandedSections.relatedQuestions && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="space-y-2 px-4 py-3 bg-purple-50 border-t border-purple-100"
              >
                {relatedQuestions.map((question, idx) => (
                  <button
                    key={idx}
                    className="w-full text-left bg-white rounded-lg p-3 border border-purple-200 hover:shadow-md transition-shadow text-xs text-gray-700 hover:text-gray-900"
                  >
                    {question}
                  </button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Footer Tips */}
      <div className="px-4 py-3 border-t border-gray-200 bg-gray-50 flex-shrink-0">
        <p className="text-xs text-gray-500 text-center">
          💡 点击任何批注或资源可获得更详细的帮助
        </p>
      </div>
    </div>
  );
}
