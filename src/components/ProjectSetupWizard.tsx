/**
 * 项目初始化向导
 * 为每个学习项目收集特定的学习目标、偏好、资源
 */
import { useState } from 'react';
import { ChevronRight, Folder, Calendar, Target, Upload } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { useAppStore } from '../store/appStore';
import type { LearningProject } from '../types';

interface ProjectSetupWizardProps {
  onComplete?: (project: LearningProject) => void;
  onCancel?: () => void;
}

export function ProjectSetupWizard({ onComplete, onCancel }: ProjectSetupWizardProps) {
  const [step, setStep] = useState(1);
  const [projectData, setProjectData] = useState({
    name: '',
    description: '',
    folderPath: '',
    targetDate: '',
    targetGoal: 'proficient' as 'familiar' | 'proficient' | 'expert',
    goalDescription: '',
    assessmentType: 'exam' as 'exam' | 'project' | 'presentation' | 'none',
    focusAreas: [] as string[],
    // 🔥 补充高优先级修复 #3：项目级个性化收集
    learningStyleForProject: 'visual' as 'visual' | 'auditory' | 'kinesthetic' | 'reading-writing' | 'mixed',
    preferredDetailLevel: 'moderate' as 'concise' | 'moderate' | 'detailed',
    allowProactivePush: true,
    pushFrequency: 'daily' as 'real-time' | 'daily' | 'weekly' | 'manual',
    tutorTone: 'encouraging' as 'encouraging' | 'challenging' | 'socratic' | 'neutral',
    focusDifficulty: 'intermediate' as 'beginner' | 'intermediate' | 'advanced',
  });

  const { createProject } = useAppStore();

  const handleNext = () => {
    if (step < 3) {
      setStep(step + 1);
    } else {
      finishSetup();
    }
  };

  const finishSetup = () => {
    const newProject: LearningProject = {
      id: 'proj_' + Date.now(),
      userId: 'user_1', // TODO: 从 store 获取真实用户 ID
      name: projectData.name,
      description: projectData.description,
      folderPath: projectData.folderPath,
      learningGoal: {
        id: 'goal_' + Date.now(),
        projectId: 'proj_' + Date.now(),
        userId: 'user_1',
        title: projectData.name,
        description: projectData.goalDescription,
        targetDate: projectData.targetDate ? new Date(projectData.targetDate).getTime() : undefined,
        targetMasteryLevel: projectData.targetGoal,
        assessmentType: projectData.assessmentType,
        createdAt: Date.now(),
        updatedAt: Date.now(),
        status: 'active',
      },
      userPreferences: {
        projectId: 'proj_' + Date.now(),
        userId: 'user_1',
        focusAreas: projectData.focusAreas,
        pushNotificationFrequency: projectData.pushFrequency,
        allowProactiveMessages: projectData.allowProactivePush,
        tutorPersonality: projectData.tutorTone,
        feedbackDetailLevel: projectData.preferredDetailLevel,
        difficultyLevel: projectData.focusDifficulty,
        updatedAt: Date.now(),
      },
      documents: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
      status: 'active',
    };

    createProject(newProject);
    onComplete?.(newProject);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full bg-white rounded-2xl shadow-2xl overflow-hidden">
        {/* Progress Bar */}
        <div className="h-1 bg-stone-200">
          <motion.div
            className="h-full bg-gradient-to-r from-indigo-500 to-purple-500"
            initial={{ width: 0 }}
            animate={{ width: `${(step / 3) * 100}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>

        <AnimatePresence mode="wait">
          {/* Step 1: Project Basics */}
          {step === 1 && (
            <motion.div
              key="step1"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="p-8 space-y-6"
            >
              <div>
                <h2 className="text-3xl font-bold text-stone-900 mb-2 flex items-center space-x-2">
                  <Target size={32} className="text-indigo-600" />
                  <span>什么是你的新学习项目？</span>
                </h2>
                <p className="text-stone-600">
                  为你的学习项目起个有意义的名字，这样可以更好地组织你的学习资料。
                </p>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-stone-700 mb-2">
                    项目名称（如：高中数学复习、雅思阅读训练）
                  </label>
                  <input
                    type="text"
                    placeholder="输入项目名称"
                    value={projectData.name}
                    onChange={(e) =>
                      setProjectData({ ...projectData, name: e.target.value })
                    }
                    className="w-full px-4 py-2 border border-stone-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-stone-700 mb-2">
                    项目描述（可选）
                  </label>
                  <textarea
                    placeholder="简单介绍这个项目的背景和目标"
                    value={projectData.description}
                    onChange={(e) =>
                      setProjectData({ ...projectData, description: e.target.value })
                    }
                    rows={3}
                    className="w-full px-4 py-2 border border-stone-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-stone-700 mb-2 flex items-center space-x-2">
                    <Folder size={16} />
                    <span>学习资料文件夹</span>
                  </label>
                  <div className="border-2 border-dashed border-stone-300 rounded-lg p-6 text-center hover:bg-stone-50 cursor-pointer transition-colors">
                    <Upload size={32} className="mx-auto mb-2 text-stone-400" />
                    <p className="text-stone-600 font-medium">选择文件夹</p>
                    <p className="text-xs text-stone-500 mt-1">
                      或者将文件夹拖到这里
                    </p>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* Step 2: Learning Goal */}
          {step === 2 && (
            <motion.div
              key="step2"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="p-8 space-y-6"
            >
              <div>
                <h2 className="text-3xl font-bold text-stone-900 mb-2 flex items-center space-x-2">
                  <Calendar size={32} className="text-purple-600" />
                  <span>你的学习目标</span>
                </h2>
                <p className="text-stone-600">
                  明确的目标帮助我更好地制定学习计划和评估进度。
                </p>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-stone-700 mb-2">
                    目标完成日期
                  </label>
                  <input
                    type="date"
                    value={projectData.targetDate}
                    onChange={(e) =>
                      setProjectData({ ...projectData, targetDate: e.target.value })
                    }
                    className="w-full px-4 py-2 border border-stone-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-stone-700 mb-3">
                    掌握程度目标
                  </label>
                  <div className="space-y-2">
                    {[
                      {
                        value: 'familiar',
                        label: '了解 (Familiar)',
                        desc: '能理解基本概念，认识专业术语',
                      },
                      {
                        value: 'proficient',
                        label: '精通 (Proficient)',
                        desc: '能灵活应用，解决常见问题',
                      },
                      {
                        value: 'expert',
                        label: '精深 (Expert)',
                        desc: '掌握深层原理，能举一反三',
                      },
                    ].map((option) => (
                      <button
                        key={option.value}
                        onClick={() =>
                          setProjectData({ ...projectData, targetGoal: option.value as 'familiar' | 'proficient' | 'expert' })
                        }
                        className={`w-full p-3 rounded-lg border-2 text-left transition-all ${
                          projectData.targetGoal === option.value
                            ? 'border-purple-500 bg-purple-50'
                            : 'border-stone-200 hover:border-stone-300'
                        }`}
                      >
                        <div className="font-medium text-stone-900">{option.label}</div>
                        <div className="text-xs text-stone-600 mt-1">{option.desc}</div>
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-stone-700 mb-2">
                    评估方式（如有）
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    {['exam', 'project', 'presentation', 'none'].map((type) => (
                      <button
                        key={type}
                        onClick={() =>
                          setProjectData({ ...projectData, assessmentType: type as 'exam' | 'project' | 'presentation' | 'none' })
                        }
                        className={`p-2 rounded border-2 text-xs font-medium transition-all ${
                          projectData.assessmentType === type
                            ? 'border-purple-500 bg-purple-50'
                            : 'border-stone-200'
                        }`}
                      >
                        {type === 'exam' && '📝 考试'}
                        {type === 'project' && '🛠️ 项目'}
                        {type === 'presentation' && '🎤 演讲'}
                        {type === 'none' && '📚 仅学习'}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* Step 3: Focus Areas & Preferences */}
          {step === 3 && (
            <motion.div
              key="step3"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="p-8 space-y-6"
            >
              <div>
                <h2 className="text-3xl font-bold text-gray-900 mb-2">
                  个性化偏好设置
                </h2>
                <p className="text-gray-600">
                  使用这些偏好使WayFare更加适应你的学习方式。
                </p>
              </div>

              <div className="space-y-4">
                {/* 重点关注领域 */}
                <div>
                  <label className="block text-sm font-medium text-stone-700 mb-3">
                    重点关注的领域（选择多个）
                  </label>
                  <div className="space-y-2">
                    {['基础概念', '常见错误', '考试高频', '应用场景', '实践技能'].map(
                      (area) => (
                        <button
                          key={area}
                          onClick={() => {
                            setProjectData({
                              ...projectData,
                              focusAreas: projectData.focusAreas.includes(area)
                                ? projectData.focusAreas.filter((a) => a !== area)
                                : [...projectData.focusAreas, area],
                            });
                          }}
                          className={`w-full p-3 rounded-lg border-2 text-left transition-all flex items-center ${
                            projectData.focusAreas.includes(area)
                              ? 'border-purple-500 bg-purple-50'
                              : 'border-stone-200 hover:border-stone-300'
                          }`}
                        >
                          <div
                            className={`w-5 h-5 rounded border-2 mr-3 flex items-center justify-center transition-all ${
                              projectData.focusAreas.includes(area)
                                ? 'bg-purple-500 border-purple-500'
                                : 'border-stone-300'
                            }`}
                          >
                            {projectData.focusAreas.includes(area) && (
                              <div className="w-2 h-2 bg-white rounded-full" />
                            )}
                          </div>
                          <span className="font-medium text-stone-900">{area}</span>
                        </button>
                      )
                    )}
                  </div>
                </div>

                {/* 学习风格偏好（项目级） */}
                <div className="border-t border-stone-200 pt-4">
                  <label className="block text-sm font-medium text-stone-700 mb-3">
                    在此项目中的学习风格
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    {[
                      { val: 'visual', label: '👁️ 视觉型', desc: '图表、图像' },
                      { val: 'auditory', label: '👂 听觉型', desc: '讲解、讨论' },
                      { val: 'kinesthetic', label: '✋ 动手型', desc: '实践、操作' },
                      { val: 'reading-writing', label: '📚 阅读型', desc: '文字、笔记' },
                    ].map((style) => (
                      <button
                        key={style.val}
                        onClick={() =>
                          setProjectData({
                            ...projectData,
                            learningStyleForProject: style.val as 'visual' | 'auditory' | 'kinesthetic' | 'reading-writing' | 'mixed',
                          })
                        }
                        className={`p-2 rounded border-2 text-xs text-center transition-all ${
                          projectData.learningStyleForProject === style.val
                            ? 'border-indigo-500 bg-indigo-50'
                            : 'border-stone-200 hover:border-stone-300'
                        }`}
                      >
                        <div className="font-bold">{style.label}</div>
                        <div className="text-stone-600 text-xs">{style.desc}</div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* 解释详细程度 */}
                <div className="border-t border-stone-200 pt-4">
                  <label className="block text-sm font-medium text-stone-700 mb-3">
                    你希望讲解的详细程度
                  </label>
                  <div className="space-y-2">
                    {[
                      { val: 'concise', label: '简洁', desc: '直切要点，节省时间' },
                      { val: 'moderate', label: '适中', desc: '重点突出，辅以例子' },
                      { val: 'detailed', label: '详细', desc: '深入分析，包含背景' },
                    ].map((level) => (
                      <button
                        key={level.val}
                        onClick={() =>
                          setProjectData({
                            ...projectData,
                            preferredDetailLevel: level.val as 'concise' | 'moderate' | 'detailed',
                          })
                        }
                        className={`w-full p-2 rounded border-2 text-left text-xs transition-all ${
                          projectData.preferredDetailLevel === level.val
                            ? 'border-indigo-500 bg-indigo-50'
                            : 'border-stone-200 hover:border-stone-300'
                        }`}
                      >
                        <div className="font-bold text-stone-900">{level.label}</div>
                        <div className="text-stone-600">{level.desc}</div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Agent风格 */}
                <div className="border-t border-stone-200 pt-4">
                  <label className="block text-sm font-medium text-stone-700 mb-3">
                    你喜欢的Agent教学风格
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    {[
                      { val: 'encouraging', label: '🌟 鼓励型' },
                      { val: 'challenging', label: '🎯 挑战型' },
                      { val: 'socratic', label: '🤔 苏格拉底型' },
                      { val: 'neutral', label: '⚪ 中立型' },
                    ].map((tone) => (
                      <button
                        key={tone.val}
                        onClick={() =>
                          setProjectData({
                            ...projectData,
                            tutorTone: tone.val as 'encouraging' | 'challenging' | 'socratic' | 'neutral',
                          })
                        }
                        className={`p-2 rounded border-2 text-xs text-center transition-all ${
                          projectData.tutorTone === tone.val
                            ? 'border-purple-500 bg-purple-50'
                            : 'border-stone-200 hover:border-stone-300'
                        }`}
                      >
                        {tone.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* 主动推送偏好 */}
                <div className="border-t border-stone-200 pt-4">
                  <div className="flex items-center space-x-3 mb-3">
                    <label className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={projectData.allowProactivePush}
                        onChange={(e) =>
                          setProjectData({
                            ...projectData,
                            allowProactivePush: e.target.checked,
                          })
                        }
                        className="w-4 h-4 rounded border-stone-300"
                      />
                      <span className="text-sm font-medium text-stone-700">允许Agent主动推送提醒</span>
                    </label>
                  </div>
                  {projectData.allowProactivePush && (
                    <div className="grid grid-cols-2 gap-2">
                      {[
                        { val: 'real-time', label: '⚡ 实时' },
                        { val: 'daily', label: '📅 每天' },
                        { val: 'weekly', label: '📆 每周' },
                        { val: 'manual', label: '🤲 手动' },
                      ].map((freq) => (
                        <button
                          key={freq.val}
                          onClick={() =>
                            setProjectData({
                              ...projectData,
                              pushFrequency: freq.val as 'real-time' | 'daily' | 'weekly' | 'manual',
                            })
                          }
                          className={`p-2 rounded border-2 text-xs text-center transition-all ${
                            projectData.pushFrequency === freq.val
                              ? 'border-green-500 bg-green-50'
                              : 'border-stone-200 hover:border-stone-300'
                          }`}
                        >
                          {freq.label}
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-lg p-6">
                  <h3 className="font-semibold text-stone-900 mb-3">✨ 接下来会发生什么</h3>
                  <ul className="space-y-2 text-sm text-stone-700">
                    <li className="flex items-start space-x-2">
                      <span className="text-purple-600 font-bold">1.</span>
                      <span>WayFare 会分析你上传的所有学习资料</span>
                    </li>
                    <li className="flex items-start space-x-2">
                      <span className="text-purple-600 font-bold">2.</span>
                      <span>自动标注重点、难点、例题的优先级</span>
                    </li>
                    <li className="flex items-start space-x-2">
                      <span className="text-purple-600 font-bold">3.</span>
                      <span>在网络上主动检索补充资源</span>
                    </li>
                    <li className="flex items-start space-x-2">
                      <span className="text-purple-600 font-bold">4.</span>
                      <span>每{projectData.pushFrequency === 'real-time' ? '时' : projectData.pushFrequency === 'daily' ? '天' : projectData.pushFrequency === 'weekly' ? '周' : '次'}推送个性化学习建议和提醒</span>
                    </li>
                  </ul>
                </div>
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
          <div className="flex items-center space-x-2">
            <button
              onClick={onCancel}
              className="px-4 py-2 text-stone-700 font-medium rounded-lg hover:bg-stone-200 transition-colors"
            >
              取消
            </button>
            <button
              onClick={handleNext}
              disabled={!projectData.name}
              className="px-6 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-medium rounded-lg hover:shadow-lg transition-all flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span>{step === 3 ? '创建项目' : '下一步'}</span>
              <ChevronRight size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
