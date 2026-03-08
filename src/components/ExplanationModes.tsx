/**
 * 多层次解释模式
 * 这是 WayFare "输出易理解" 特性的核心体现
 * 
 * 支持四种解释方式：
 * 1. 类比解释 (Analogy) - 用熟悉的东西类比陌生的概念
 * 2. 分解解释 (Decompose) - 复杂概念→子概念→更细的部分
 * 3. 费曼解释 (Feynman) - 用简单语言讲清楚，找出概念缝隙
 * 4. 证据解释 (Evidence) - 真实例子/案例/图表
 */

import { useState } from 'react';
import { ChevronDown, Lightbulb, Zap, BookOpen, BarChart3 } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

interface ExplanationContent {
  title: string;
  content: string;
  examples?: string[];
  keyPoints?: string[];
  warnings?: string[];
}

interface ExplanationModesProps {
  conceptName: string;
  analogyExplanation?: ExplanationContent;
  decomposeExplanation?: ExplanationContent;
  feynmanExplanation?: ExplanationContent;
  evidenceExplanation?: ExplanationContent;
  difficulty?: 'easy' | 'medium' | 'hard';
}

interface ModeTabProps {
  label: string;
  icon: React.ReactNode;
  isActive: boolean;
  onClick: () => void;
  difficulty?: string;
}

function ModeTab({ label, icon, isActive, onClick }: ModeTabProps) {
  return (
    <motion.button
      onClick={onClick}
      className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-all ${
        isActive
          ? 'bg-indigo-100 text-indigo-700 font-semibold'
          : 'bg-stone-100 text-stone-600 hover:bg-stone-200'
      }`}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
    >
      {icon}
      <span>{label}</span>
    </motion.button>
  );
}

/**
 * 类比解释组件
 */
export function AnalogExplanation({ explanation }: { explanation?: ExplanationContent }) {
  const [open, setOpen] = useState(true);

  if (!explanation) {
    return (
      <div className="text-stone-500 text-sm p-4">
        还没有类比解释。尝试问 AI：&quot;用生活中的例子给我讲讲这个概念&quot;
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-4"
    >
      {/* 类比本身 */}
      <div className="bg-white rounded-lg p-4 border border-gray-200">
        <p className="text-sm text-stone-700 leading-relaxed">{explanation.content}</p>
        {explanation.keyPoints && explanation.keyPoints.length > 0 && (
          <div className="mt-3 space-y-2">
            {explanation.keyPoints.map((point, idx) => (
              <div key={idx} className="flex items-start space-x-2 text-xs text-blue-700">
                <span className="font-bold">→</span>
                <span>{point}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 类比成立的前提 */}
      {explanation.warnings && explanation.warnings.length > 0 && (
        <div className="bg-amber-50 rounded-lg p-3 border border-amber-200">
          <button
            onClick={() => setOpen(!open)}
            className="w-full flex items-center justify-between text-xs font-semibold text-amber-700 hover:text-amber-900"
          >
            <span>⚠️ 这个类比的局限</span>
            <ChevronDown size={16} className={open ? 'rotate-180' : ''} />
          </button>
          <AnimatePresence>
            {open && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-2 space-y-1 text-xs text-amber-700"
              >
                {explanation.warnings.map((warning, idx) => (
                  <p key={idx}>• {warning}</p>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* 相关例子 */}
      {explanation.examples && explanation.examples.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-semibold text-gray-600">Related Examples:</p>
          {explanation.examples.map((example, idx) => (
            <div
              key={idx}
              className="bg-stone-50 rounded p-2 text-xs text-stone-700 flex items-start space-x-2"
            >
              <span className="text-blue-500">•</span>
              <span>{example}</span>
            </div>
          ))}
        </div>
      )}
    </motion.div>
  );
}

/**
 * 分解解释组件
 */
export function DecomposeExplanation({
  explanation,
}: {
  explanation?: ExplanationContent;
}) {
  if (!explanation) {
    return (
      <div className="text-stone-500 text-sm p-4">
        还没有分解讲解。尝试问 AI：&quot;给我分步骤讲解这个概念&quot;
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-4"
    >
      {/* 总体描述 */}
      <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg p-4 border border-green-200">
        <p className="text-sm text-stone-700 leading-relaxed">{explanation.content}</p>
      </div>

      {/* 分解步骤 */}
      {explanation.keyPoints && explanation.keyPoints.length > 0 && (
        <div className="space-y-3">
          <p className="text-xs font-semibold text-stone-600">🧩 分解步骤：</p>
          {explanation.keyPoints.map((point, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.1 }}
              className="bg-white rounded-lg p-3 border-l-4 border-green-400"
            >
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-7 h-7 rounded-full bg-green-100 flex items-center justify-center text-xs font-bold text-green-700">
                  {idx + 1}
                </div>
                <div className="flex-1">
                  <p className="text-sm text-stone-700">{point}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* 常见错误 */}
      {explanation.warnings && explanation.warnings.length > 0 && (
        <div className="bg-red-50 rounded-lg p-4 border border-red-200 space-y-2">
          <p className="text-xs font-semibold text-red-600">Common Mistakes:</p>
          {explanation.warnings.map((warning, idx) => (
            <div key={idx} className="flex items-start space-x-2 text-xs text-red-700">
              <span>✗</span>
              <span>{warning}</span>
            </div>
          ))}
        </div>
      )}

      {/* 实际例子 */}
      {explanation.examples && explanation.examples.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-semibold text-gray-600">Real-world Application:</p>
          {explanation.examples.map((example, idx) => (
            <div
              key={idx}
              className="bg-stone-50 rounded p-3 text-xs text-stone-700 border-l-2 border-green-400"
            >
              {example}
            </div>
          ))}
        </div>
      )}
    </motion.div>
  );
}

/**
 * 费曼解释组件 - 用最简单的语言，找出理解缝隙
 */
export function FeynmanExplanation({
  explanation,
}: {
  explanation?: ExplanationContent;
}) {
  if (!explanation) {
    return (
      <div className="text-stone-500 text-sm p-4">
        还没有简洁解释。尝试问 AI：&quot;用小学生都能懂的方式给我讲讲&quot;
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-4"
    >
      {/* 极简讲解 */}
      <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg p-4 border border-purple-200">
        <div className="text-sm text-stone-800 leading-relaxed font-medium">
          {explanation.content}
        </div>
        <p className="text-xs text-gray-600 mt-3 italic">
          This is the core idea. Everything else is an extension of this one sentence.
        </p>
      </div>

      {/* 你可能卡住的地方 */}
      {explanation.keyPoints && explanation.keyPoints.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-semibold text-gray-600">Potential Sticking Points:</p>
          {explanation.keyPoints.map((point, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: idx * 0.1 }}
              className="bg-white rounded-lg p-3 border border-purple-200"
            >
              <p className="text-xs font-semibold text-purple-700 mb-1">
                问题 {idx + 1}：为什么...?
              </p>
              <p className="text-xs text-stone-700">{point}</p>
            </motion.div>
          ))}
        </div>
      )}

      {/* 为什么有人不理解 */}
      {explanation.warnings && explanation.warnings.length > 0 && (
        <div className="bg-blue-50 rounded-lg p-4 border border-blue-200 space-y-2">
          <p className="text-xs font-semibold text-blue-700">😕 常见困点：</p>
          {explanation.warnings.map((warning, idx) => (
            <p key={idx} className="text-xs text-blue-700">
              • {warning}
            </p>
          ))}
        </div>
      )}

      {/* 自我检验 */}
      <div className="bg-green-50 rounded-lg p-4 border border-green-200">
        <p className="text-xs font-semibold text-green-700 mb-2">✅ 自我检验：</p>
        <p className="text-xs text-green-700">
          如果你能用自己的方式给别人讲清这个概念，那就说明你真正理解了。试试用最简单的语言给朋友讲讲？
        </p>
      </div>

      {/* 进阶问题 */}
      {explanation.examples && explanation.examples.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-semibold text-stone-600">🚀 进阶问题：</p>
          {explanation.examples.map((example, idx) => (
            <div key={idx} className="bg-stone-50 rounded p-3 text-xs text-stone-700">
              <p className="font-semibold text-purple-700 mb-1">问题：</p>
              <p>{example}</p>
            </div>
          ))}
        </div>
      )}
    </motion.div>
  );
}

/**
 * 证据解释组件 - 通过真实数据、图表、案例
 */
export function EvidenceExplanation({
  explanation,
}: {
  explanation?: ExplanationContent;
}) {
  if (!explanation) {
    return (
      <div className="text-stone-500 text-sm p-4">
        还没有案例证据。尝试问 AI：&quot;给我举个真实的例子&quot;
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-4"
    >
      {/* 证据主体 */}
      <div className="bg-gradient-to-br from-orange-50 to-red-50 rounded-lg p-4 border border-orange-200">
        <p className="text-sm text-stone-700 leading-relaxed font-medium">
          {explanation.content}
        </p>
        <div className="mt-3 text-xs text-orange-700 italic">
          📊 这是基于实际数据/案例的证明
        </div>
      </div>

      {/* 具体案例 */}
      {explanation.examples && explanation.examples.length > 0 && (
        <div className="space-y-3">
          <p className="text-xs font-semibold text-gray-600">Concrete Examples:</p>
          {explanation.examples.map((example, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.1 }}
              className="bg-white rounded-lg p-4 border-2 border-orange-200"
            >
              <div className="flex items-start space-x-3">
                <div className="text-2xl">[Case]</div>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-stone-900 mb-1">
                    案例 {idx + 1}
                  </p>
                  <p className="text-sm text-stone-700">{example}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* 关键数据/指标 */}
      {explanation.keyPoints && explanation.keyPoints.length > 0 && (
        <div className="grid grid-cols-2 gap-3">
          {explanation.keyPoints.map((point, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: idx * 0.1 }}
              className="bg-stone-50 rounded-lg p-3 border border-stone-200"
            >
              <p className="text-xs text-stone-600 mb-1">关键指标：</p>
              <p className="text-sm font-bold text-orange-600">{point}</p>
            </motion.div>
          ))}
        </div>
      )}

      {/* 需要注意的限制 */}
      {explanation.warnings && explanation.warnings.length > 0 && (
        <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200 space-y-2">
          <p className="text-xs font-semibold text-yellow-700">⚠️ 需要注意的限制：</p>
          {explanation.warnings.map((warning, idx) => (
            <p key={idx} className="text-xs text-yellow-700">
              • {warning}
            </p>
          ))}
        </div>
      )}

      {/* 验证建议 */}
      <div className="bg-green-50 rounded-lg p-4 border border-green-200">
        <p className="text-xs font-semibold text-green-700 mb-2">✅ 进一步验证：</p>
        <p className="text-xs text-green-700">
          这些例子来自可靠来源。你也可以尝试找其他类似的案例来验证这个规律是否普遍成立。
        </p>
      </div>
    </motion.div>
  );
}

/**
 * 主要组件：多模式解释选择器
 */
export function ExplanationModes({
  conceptName,
  analogyExplanation,
  decomposeExplanation,
  feynmanExplanation,
  evidenceExplanation,
  difficulty = 'medium',
}: ExplanationModesProps) {
  const [activeMode, setActiveMode] = useState<
    'analogy' | 'decompose' | 'feynman' | 'evidence'
  >('decompose');

  const modes = [
    {
      id: 'analogy' as const,
      label: '类比',
      icon: <Lightbulb size={16} />,
      description: '用熟悉的事物类比陌生的概念',
      component: <AnalogExplanation explanation={analogyExplanation} />,
    },
    {
      id: 'decompose' as const,
      label: '分解',
      icon: <Zap size={16} />,
      description: '复杂→简单，逐步讲解',
      component: <DecomposeExplanation explanation={decomposeExplanation} />,
    },
    {
      id: 'feynman' as const,
      label: '费曼',
      icon: <BookOpen size={16} />,
      description: '最简单的语言，找缝隙',
      component: <FeynmanExplanation explanation={feynmanExplanation} />,
    },
    {
      id: 'evidence' as const,
      label: '证据',
      icon: <BarChart3 size={16} />,
      description: '用真实案例和数据',
      component: <EvidenceExplanation explanation={evidenceExplanation} />,
    },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-lg border border-stone-200 overflow-hidden"
    >
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-50 to-purple-50 px-6 py-4 border-b border-stone-200">
        <div className="flex items-start justify-between mb-3">
          <div>
            <h3 className="text-lg font-bold text-gray-900">
              Understanding 《{conceptName}》
            </h3>
            <p className="text-xs text-stone-500 mt-1">
              选择适合你的解释方式。每个角度都能帮你加深理解。
            </p>
          </div>
          {difficulty && (
            <div className="text-xs font-semibold px-2 py-1 rounded bg-stone-200 text-stone-700">
              {difficulty === 'easy'
                ? '🟢 简单'
                : difficulty === 'medium'
                  ? '🟡 中等'
                  : '🔴 困难'}
            </div>
          )}
        </div>

        {/* Mode tabs */}
        <div className="flex space-x-2 overflow-x-auto pb-2">
          {modes.map((mode) => (
            <ModeTab
              key={mode.id}
              label={mode.label}
              icon={mode.icon}
              isActive={activeMode === mode.id}
              onClick={() => setActiveMode(mode.id)}
            />
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeMode}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
          >
            {modes.find((m) => m.id === activeMode)?.component}
          </motion.div>
        </AnimatePresence>

        {/* Mode description */}
        <motion.div className="mt-6 pt-4 border-t border-stone-200">
          <p className="text-xs text-stone-600 italic">
            💫{' '}
            {
              modes.find((m) => m.id === activeMode)?.description
            }
          </p>
        </motion.div>
      </div>

      {/* Tips footer */}
      <div className="bg-stone-50 px-6 py-3 border-t border-stone-200">
        <p className="text-xs text-gray-600">
          <strong>Tip:</strong>
          如果某个解释方式对你特别有效，系统会记住。下次讲解相似的概念时会优先使用这种方式。
        </p>
      </div>
    </motion.div>
  );
}
