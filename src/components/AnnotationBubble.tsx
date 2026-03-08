import { useState } from 'react';
import {
  MessageCircle,
  X,
  AlertCircle,
  Lightbulb,
  TrendingUp,
  Zap,
  Brain,
  Award,
  HelpCircle,
  Clock,
} from 'lucide-react';
import type { EnhancedAnnotation } from '../types';
import { motion, AnimatePresence } from 'motion/react';

interface EnhancedAnnotationBubbleProps {
  annotation: EnhancedAnnotation;
  onDismiss?: (id: string) => void;
  onRequestDetail?: (id: string) => void;
  onAskQuestion?: (id: string) => void;
  onFeedbackSubmit?: (annotationId: string, feedback: string, clarifications: string[]) => void;
}

/**
 * 增强的批注气泡
 * 支持：
 * - 优先级标注（考试重点/细节等）
 * - 信心度显示（学生的理解程度）
 * - 认知支架展示（类比、拆解、关键问题）
 * - 学习历程回溯（何时首次卡住、何时掌握）
 */
export function AnnotationBubble({
  annotation,
  onDismiss,
  onRequestDetail,
  onAskQuestion,
  onFeedbackSubmit,
}: EnhancedAnnotationBubbleProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [showScaffolding, setShowScaffolding] = useState(false);
  const [showFeedbackForm, setShowFeedbackForm] = useState(false);
  const [studentFeedback, setStudentFeedback] = useState('');
  const [studentClarifications, setStudentClarifications] = useState<string[]>([]);
  const [newClarification, setNewClarification] = useState('');

  const handleSubmitFeedback = () => {
    onFeedbackSubmit?.(annotation.id, studentFeedback, studentClarifications);
    setStudentFeedback('');
    setStudentClarifications([]);
    setShowFeedbackForm(false);
  };

  const handleAddClarification = () => {
    if (newClarification.trim()) {
      setStudentClarifications([...studentClarifications, newClarification]);
      setNewClarification('');
    }
  };

  // ============= Color & Icon Mapping =============

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical':
        return 'bg-red-500 text-red-600 border-red-200';
      case 'high':
        return 'bg-orange-500 text-orange-600 border-orange-200';
      case 'medium':
        return 'bg-amber-500 text-amber-600 border-amber-200';
      case 'low':
        return 'bg-blue-500 text-blue-600 border-blue-200';
      case 'review':
        return 'bg-purple-500 text-purple-600 border-purple-200';
      default:
        return 'bg-stone-500 text-stone-600 border-stone-200';
    }
  };

  const getPriorityLabel = (priority: string) => {
    const map: Record<string, string> = {
      critical: '🔴 考试重点',
      high: '🟠 重要',
      medium: '🟡 中等',
      low: '🔵 细节',
      review: '🟣 复习',
    };
    return map[priority] || priority;
  };

  const getConfidenceColor = (confidence: string) => {
    switch (confidence) {
      case 'very_low':
        return 'from-red-100 to-red-50';
      case 'low':
        return 'from-orange-100 to-orange-50';
      case 'medium':
        return 'from-amber-100 to-amber-50';
      case 'high':
        return 'from-green-100 to-green-50';
      case 'mastered':
        return 'from-emerald-100 to-emerald-50';
      default:
        return 'from-stone-100 to-stone-50';
    }
  };

  const getConfidenceText = (confidence: string) => {
    const map: Record<string, string> = {
      very_low: '很困惑',
      low: '有点懵',
      medium: '基本明白',
      high: '理解良好',
      mastered: '已掌握',
    };
    return map[confidence] || confidence;
  };

  const getConfidenceIcon = (confidence: string) => {
    switch (confidence) {
      case 'very_low':
        return <AlertCircle size={14} />;
      case 'low':
        return <HelpCircle size={14} />;
      case 'medium':
        return <Brain size={14} />;
      case 'high':
        return <Lightbulb size={14} />;
      case 'mastered':
        return <Award size={14} />;
      default:
        return <MessageCircle size={14} />;
    }
  };

  const getCategoryLabel = (category?: string) => {
    const map: Record<string, string> = {
      core_concept: '核心概念',
      misunderstanding: '常见误区',
      learning_strategy: '学习策略',
      exam_preparation: '考试准备',
    };
    return map[category || ''] || '批注';
  };

  // ============= Render =============

  return (
    <div className="w-full relative">
      {/* Priority Badge - Visual Indicator */}
      <motion.button
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setIsOpen(!isOpen)}
        className={`w-10 h-10 rounded-full flex items-center justify-center shadow-lg hover:shadow-xl transition-all flex-shrink-0 border-2 ${getPriorityColor(annotation.priority).split(' ')[0]} text-white`}
        title={`${getPriorityLabel(annotation.priority)} - ${getConfidenceText(annotation.confidence)}`}
      >
        {annotation.priority === 'critical' && <Zap size={18} />}
        {annotation.priority === 'high' && <AlertCircle size={18} />}
        {annotation.priority === 'medium' && <Lightbulb size={18} />}
        {annotation.priority === 'low' && <HelpCircle size={18} />}
        {annotation.priority === 'review' && <Clock size={18} />}
      </motion.button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="absolute left-12 top-0 w-96 bg-white rounded-2xl shadow-2xl border border-stone-200 overflow-hidden z-50"
          >
            {/* Header with Priority and Confidence */}
            <div className={`bg-gradient-to-r ${getConfidenceColor(annotation.confidence)} p-4 border-b border-stone-200`}>
              <div className="flex justify-between items-start mb-2">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <span className="text-xs font-bold px-2 py-1 bg-white rounded-full">
                      {getPriorityLabel(annotation.priority)}
                    </span>
                    <span className="text-xs font-semibold text-stone-600 uppercase tracking-wider">
                      {getCategoryLabel(annotation.category)}
                    </span>
                  </div>

                  {/* Confidence Indicator */}
                  <div className="flex items-center space-x-1 text-xs text-stone-600">
                    {getConfidenceIcon(annotation.confidence)}
                    <span>信心度: {getConfidenceText(annotation.confidence)}</span>
                  </div>
                </div>

                <button
                  onClick={() => {
                    setIsOpen(false);
                    onDismiss?.(annotation.id);
                  }}
                  className="text-stone-400 hover:text-stone-600 flex-shrink-0"
                >
                  <X size={18} />
                </button>
              </div>

              {/* Source Text */}
              {annotation.sourceText && (
                <p className="text-xs text-stone-600 italic line-clamp-2 border-l-2 border-stone-300 pl-2">
                  "{annotation.sourceText}"
                </p>
              )}
            </div>

            {/* Main Content */}
            <div className="p-4">
              <p className="text-sm text-stone-700 leading-relaxed mb-4">
                {annotation.content}
              </p>

              {/* Learning Timeline */}
              {(annotation.firstMissingAt || annotation.masterAt) && (
                <div className="bg-stone-50 rounded-lg p-3 mb-4 text-xs text-stone-600 space-y-1 border-l-4 border-indigo-400">
                  {annotation.firstMissingAt && (
                    <div className="flex items-center space-x-2">
                      <AlertCircle size={12} className="text-red-500" />
                      <span>首次卡顿: {new Date(annotation.firstMissingAt).toLocaleDateString()}</span>
                    </div>
                  )}
                  {annotation.masterAt && (
                    <div className="flex items-center space-x-2">
                      <Award size={12} className="text-green-600" />
                      <span>掌握时间: {new Date(annotation.masterAt).toLocaleDateString()}</span>
                    </div>
                  )}
                  {annotation.reviewCount && annotation.reviewCount > 0 && (
                    <div className="flex items-center space-x-2">
                      <TrendingUp size={12} className="text-blue-600" />
                      <span>复习次数: {annotation.reviewCount}</span>
                    </div>
                  )}
                </div>
              )}

              {/* Cognitive Scaffolding */}
              {annotation.scaffolding && (
                <div className="mb-4">
                  <button
                    onClick={() => setShowScaffolding(!showScaffolding)}
                    className="w-full flex items-center justify-between px-3 py-2 rounded-lg bg-indigo-50 hover:bg-indigo-100 transition-colors text-sm font-medium text-indigo-700 mb-2"
                  >
                    <div className="flex items-center space-x-2">
                      <Brain size={16} />
                      <span>认知支架</span>
                    </div>
                    <span>{showScaffolding ? '▼' : '▶'}</span>
                  </button>

                  <AnimatePresence>
                    {showScaffolding && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="space-y-3 px-3 py-3 bg-indigo-50 rounded-lg"
                      >
                        {annotation.scaffolding.analogy && (
                          <div>
                            <p className="text-xs font-semibold text-indigo-700 mb-1">
                              📍 类比理解
                            </p>
                            <p className="text-xs text-stone-600">
                              {annotation.scaffolding.analogy}
                            </p>
                          </div>
                        )}

                        {annotation.scaffolding.decomposition && annotation.scaffolding.decomposition.length > 0 && (
                          <div>
                            <p className="text-xs font-semibold text-indigo-700 mb-1">
                              📌 逐步拆解
                            </p>
                            <ol className="text-xs text-stone-600 space-y-1 list-decimal list-inside">
                              {annotation.scaffolding.decomposition.map((step, idx) => (
                                <li key={idx}>{step}</li>
                              ))}
                            </ol>
                          </div>
                        )}

                        {annotation.scaffolding.keyQuestions && annotation.scaffolding.keyQuestions.length > 0 && (
                          <div>
                            <p className="text-xs font-semibold text-indigo-700 mb-1">
                              ❓ 费曼检验
                            </p>
                            <ul className="text-xs text-stone-600 space-y-1">
                              {annotation.scaffolding.keyQuestions.map((q, idx) => (
                                <li key={idx}>• {q}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {annotation.scaffolding.priorKnowledge && (
                          <div className="pt-2 border-t border-indigo-200">
                            <p className="text-xs font-semibold text-gray-700 mb-1">
                              Prior Knowledge
                            </p>
                            <p className="text-xs text-stone-600">
                              {annotation.scaffolding.priorKnowledge}
                            </p>
                          </div>
                        )}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              )}
            </div>

            {/* Student Feedback Section */}
            {annotation.studentResponses && (
              <div className="mb-4 bg-green-50 border-l-4 border-green-400 p-3 rounded-lg">
                <p className="text-xs font-semibold text-green-700 mb-2">💬 你的反馈</p>
                {annotation.studentResponses.feedback && (
                  <p className="text-xs text-stone-600 mb-2">{annotation.studentResponses.feedback}</p>
                )}
                {annotation.studentResponses.clarifications && annotation.studentResponses.clarifications.length > 0 && (
                  <div className="text-xs">
                    <p className="text-green-700 font-semibold mb-1">需要澄清的地方:</p>
                    <ul className="space-y-1 text-stone-600">
                      {annotation.studentResponses.clarifications.map((c, idx) => (
                        <li key={idx}>• {c}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {/* Feedback Form */}
            <AnimatePresence>
              {showFeedbackForm && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="bg-blue-50 p-3 rounded-lg mb-4 space-y-3"
                >
                  <div>
                    <label className="text-xs font-semibold text-blue-700 block mb-1">
                      ❓ 这个解释对你有帮助吗？
                    </label>
                    <textarea
                      value={studentFeedback}
                      onChange={(e) => setStudentFeedback(e.target.value)}
                      placeholder="告诉我你的想法，比如：'这个类比很清楚' 或 '我还是不太明白'..."
                      className="w-full text-xs p-2 border border-blue-200 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent"
                      rows={3}
                    />
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-blue-700 block mb-1">
                      🤔 还需要澄清什么?（可选）
                    </label>
                    <div className="space-y-2">
                      {studentClarifications.length > 0 && (
                        <div className="space-y-1">
                          {studentClarifications.map((c, idx) => (
                            <div
                              key={idx}
                              className="flex items-center justify-between bg-white p-2 rounded border border-blue-200"
                            >
                              <span className="text-xs text-stone-600">{c}</span>
                              <button
                                onClick={() =>
                                  setStudentClarifications(studentClarifications.filter((_, i) => i !== idx))
                                }
                                className="text-xs text-red-500 hover:text-red-700"
                              >
                                ✕
                              </button>
                            </div>
                          ))}
                        </div>
                      )}
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={newClarification}
                          onChange={(e) => setNewClarification(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') handleAddClarification();
                          }}
                          placeholder="比如：'请再解释一下...' 然后按Enter"
                          className="flex-1 text-xs p-2 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent"
                        />
                        <button
                          onClick={handleAddClarification}
                          className="text-xs px-2 py-2 bg-blue-200 hover:bg-blue-300 text-blue-700 rounded-lg font-medium transition-colors"
                        >
                          +
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-2 pt-2 border-t border-blue-200">
                    <button
                      onClick={() => setShowFeedbackForm(false)}
                      className="flex-1 text-xs px-2 py-2 rounded hover:bg-blue-100 transition-colors text-blue-700"
                    >
                      取消
                    </button>
                    <button
                      onClick={handleSubmitFeedback}
                      disabled={!studentFeedback.trim()}
                      className="flex-1 text-xs px-2 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white rounded font-medium transition-colors"
                    >
                      💾 保存反馈
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
            <div className="flex justify-end space-x-2 p-4 border-t border-stone-200">
              <button
                onClick={() => {
                  setIsOpen(false);
                  onDismiss?.(annotation.id);
                }}
                className="text-xs text-stone-500 hover:text-stone-700 px-2 py-1 rounded hover:bg-stone-100 transition-colors"
              >
                关闭
              </button>
              <button
                onClick={() => setShowFeedbackForm(!showFeedbackForm)}
                className="text-xs bg-green-50 text-green-700 px-3 py-1 rounded hover:bg-green-100 transition-colors font-medium flex items-center space-x-1"
              >
                <MessageCircle size={14} />
                <span>反馈</span>
              </button>
              <button
                onClick={() => {
                  onAskQuestion?.(annotation.id);
                }}
                className="text-xs bg-blue-50 text-blue-700 px-3 py-1 rounded hover:bg-blue-100 transition-colors font-medium flex items-center space-x-1"
              >
                <HelpCircle size={14} />
                <span>提问</span>
              </button>
              <button
                onClick={() => {
                  onRequestDetail?.(annotation.id);
                }}
                className="text-xs bg-indigo-50 text-indigo-700 px-3 py-1 rounded hover:bg-indigo-100 transition-colors font-medium flex items-center space-x-1"
              >
                <Lightbulb size={14} />
                <span>深入讲解</span>
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
