/**
 * 用户入驻流程
 * 收集学习风格、理解偏好，建立个性化基线
 */
import { useState } from 'react';
import { ChevronRight, CheckCircle2 } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { useAppStore } from '../store/appStore';
import type { LearnerProfile } from '../types';

interface OnboardingFlowProps {
  onComplete?: (profile: LearnerProfile) => void;
}

export function OnboardingFlow({ onComplete }: OnboardingFlowProps) {
  const [step, setStep] = useState(1);
  const [profile, setProfile] = useState<Partial<LearnerProfile>>({
    displayName: '',
    preferredLearningStyle: 'mixed',
    preferredPaceLevel: 'medium',
    explanationPreferences: {
      useAnalogies: true,
      useStepByStep: true,
      useExamples: true,
      useVisualDiagrams: true,
      preferredLanguageLevel: 'simple',
    },
  });

  const { updateUserProfile } = useAppStore();

  const handleNext = () => {
    if (step < 4) {
      setStep(step + 1);
    } else {
      finishOnboarding();
    }
  };

  const finishOnboarding = () => {
    const finalProfile: LearnerProfile = {
      userId: 'user_' + Date.now(),
      ...profile,
      createdAt: Date.now(),
      updatedAt: Date.now(),
    } as LearnerProfile;

    updateUserProfile(finalProfile);
    onComplete?.(finalProfile);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full bg-white rounded-2xl shadow-2xl overflow-hidden">
        {/* Progress Bar */}
        <div className="h-1 bg-stone-200">
          <motion.div
            className="h-full bg-gray-400"
            initial={{ width: 0 }}
            animate={{ width: `${(step / 4) * 100}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>

        <AnimatePresence mode="wait">
          {/* Step 1: Basic Info */}
          {step === 1 && (
            <motion.div
              key="step1"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="p-8 space-y-6"
            >
              <div>
                <h2 className="text-3xl font-bold text-stone-900 mb-2">
                  👋 欢迎来到 WayFare
                </h2>
                <p className="text-stone-600">
                  首先，让我们了解一下你。这将帮我为你提供最个性化的学习体验。
                </p>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-stone-700 mb-2">
                    你的名字
                  </label>
                  <input
                    type="text"
                    placeholder="输入你的名字"
                    value={profile.displayName || ''}
                    onChange={(e) =>
                      setProfile({ ...profile, displayName: e.target.value })
                    }
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-400"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-stone-700 mb-3">
                    你通常如何学习新概念？
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    {['visual', 'auditory', 'kinesthetic', 'reading-writing'].map(
                      (style) => (
                        <button
                          key={style}
                          onClick={() =>
                            setProfile({
                              ...profile,
                              preferredLearningStyle: style as 'visual' | 'auditory' | 'kinesthetic' | 'reading-writing',
                            })
                          }
                          className={`p-3 rounded-lg border-2 transition-all ${
                            profile.preferredLearningStyle === style
                              ? 'border-indigo-500 bg-indigo-50'
                              : 'border-stone-200 hover:border-stone-300'
                          }`}
                        >
                          <div className="text-sm font-medium">
                            {style === 'visual' && '👁️ 视觉化'}
                            {style === 'auditory' && '👂 听觉化'}
                            {style === 'kinesthetic' && '🤲 动手做'}
                            {style === 'reading-writing' && '📚 阅读写作'}
                          </div>
                        </button>
                      )
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* Step 2: Learning Pace */}
          {step === 2 && (
            <motion.div
              key="step2"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="p-8 space-y-6"
            >
              <div>
                <h2 className="text-3xl font-bold text-stone-900 mb-2">
                  ⏱️ 你的学习节奏
                </h2>
                <p className="text-stone-600">
                  我们会根据你的节奏调整内容深度和讲解详细程度。
                </p>
              </div>

              <div className="space-y-4">
                {['slow', 'medium', 'fast'].map((pace) => (
                  <button
                    key={pace}
                    onClick={() =>
                      setProfile({ ...profile, preferredPaceLevel: pace as 'slow' | 'medium' | 'fast' })
                    }
                    className={`w-full p-4 rounded-lg border-2 text-left transition-all ${
                      profile.preferredPaceLevel === pace
                        ? 'border-indigo-500 bg-indigo-50'
                        : 'border-stone-200 hover:border-stone-300'
                    }`}
                  >
                    <div className="font-medium text-stone-900">
                      {pace === 'slow' && '🐢 偏喜欢详细讲解，慢慢理解'}
                      {pace === 'medium' && '🚴 适中节奏，既有深度又不啰嗦'}
                      {pace === 'fast' && '🚀 喜欢快速把握要点'}
                    </div>
                    <div className="text-sm text-stone-600 mt-1">
                      {pace === 'slow' &&
                        '我会提供详细的步骤分解和多个例子'}
                      {pace === 'medium' &&
                        '我会平衡详细性和简洁性'}
                      {pace === 'fast' &&
                        '我会直击重点，给出核心概念和关键策略'}
                    </div>
                  </button>
                ))}
              </div>
            </motion.div>
          )}

          {/* Step 3: Explanation Preferences */}
          {step === 3 && (
            <motion.div
              key="step3"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="p-8 space-y-6"
            >
              <div>
                <h2 className="text-3xl font-bold text-stone-900 mb-2">
                  🧠 你最喜欢的讲解方式
                </h2>
                <p className="text-stone-600">
                  我可以用不同的方式解释同一件事。选择最有效的对你来说是什么。
                </p>
              </div>

              <div className="space-y-3">
                {[
                  { key: 'useAnalogies', label: '🎭 类比 (用我已知的东西解释新东西)' },
                  { key: 'useStepByStep', label: '🔨 拆解 (逐步分解复杂概念)' },
                  { key: 'useExamples', label: '📚 例题 (通过大量实例学习)' },
                  { key: 'useVisualDiagrams', label: '📊 图表 (用图表和图像表达)' },
                ].map((pref) => (
                  <button
                    key={pref.key}
                    onClick={() => {
                      setProfile({
                        ...profile,
                        explanationPreferences: {
                          ...profile.explanationPreferences,
                          [pref.key]: !(
                            profile.explanationPreferences?.[
                              pref.key as keyof typeof profile.explanationPreferences
                            ]
                          ),
                        },
                      });
                    }}
                    className={`w-full p-4 rounded-lg border-2 text-left transition-all flex items-center ${
                      profile.explanationPreferences?.[
                        pref.key as keyof typeof profile.explanationPreferences
                      ]
                        ? 'border-indigo-500 bg-indigo-50'
                        : 'border-stone-200 hover:border-stone-300'
                    }`}
                  >
                    <div
                      className={`w-5 h-5 rounded border-2 mr-3 flex items-center justify-center ${
                        profile.explanationPreferences?.[
                          pref.key as keyof typeof profile.explanationPreferences
                        ]
                          ? 'bg-indigo-500 border-indigo-500'
                          : 'border-stone-300'
                      }`}
                    >
                      {profile.explanationPreferences?.[
                        pref.key as keyof typeof profile.explanationPreferences
                      ] && <CheckCircle2 size={16} className="text-white" />}
                    </div>
                    <span className="font-medium text-stone-900">{pref.label}</span>
                  </button>
                ))}
              </div>
            </motion.div>
          )}

          {/* Step 4: Summary */}
          {step === 4 && (
            <motion.div
              key="step4"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="p-8 space-y-6"
            >
              <div>
                <h2 className="text-3xl font-bold text-stone-900 mb-2">
                  ✨ 准备就绪
                </h2>
                <p className="text-stone-600">
                  这是我对你的初步理解。之后在每个项目中，我会更深入地了解你和你的学习需求。
                </p>
              </div>

              <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-lg p-6 space-y-4">
                <div>
                  <div className="text-sm text-stone-600">名字</div>
                  <div className="text-lg font-medium text-stone-900">
                    {profile.displayName || '学生'}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-stone-600">学习风格</div>
                  <div className="text-lg font-medium text-stone-900">
                    {profile.preferredLearningStyle === 'visual' && '视觉化学习者'}
                    {profile.preferredLearningStyle === 'auditory' && '听觉化学习者'}
                    {profile.preferredLearningStyle === 'kinesthetic' && '动手型学习者'}
                    {profile.preferredLearningStyle === 'reading-writing' &&
                      '阅读写作型学习者'}
                    {profile.preferredLearningStyle === 'mixed' && '混合型学习者'}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-stone-600">学习节奏</div>
                  <div className="text-lg font-medium text-stone-900">
                    {profile.preferredPaceLevel === 'slow' && '喜欢详细和深入'}
                    {profile.preferredPaceLevel === 'medium' && '平衡的节奏'}
                    {profile.preferredPaceLevel === 'fast' && '快速高效'}
                  </div>
                </div>
              </div>

              <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
                <p className="text-sm text-blue-900">
                  💡
                  提示：这些偏好不是固定的。在每个项目中，我会根据你的学习效果持续调整和优化。
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Navigation */}
        <div className="bg-stone-50 px-8 py-4 flex justify-between">
          <button
            onClick={() => setStep(Math.max(1, step - 1))}
            disabled={step === 1}
            className="px-4 py-2 text-stone-700 font-medium rounded-lg hover:bg-stone-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            ← 上一步
          </button>
          <div className="text-sm text-stone-600">
            第 {step} 步，共 4 步
          </div>
          <button
            onClick={handleNext}
            className="px-6 py-2 bg-gray-200 text-gray-800 font-medium rounded-lg transition-all flex items-center space-x-2"
          >
            <span>{step === 4 ? '完成' : '下一步'}</span>
            <ChevronRight size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}
