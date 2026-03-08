/**
 * 学习进度看板
 * 展示学生的总体学习进度：已掌握的概念、正在学的、需要改进的
 * 这支持WayFare的个性化特性：记录每个用户的学习历程
 */
import { useState } from 'react';
import {
  TrendingUp,
  Award,
  Target,
  AlertCircle,
  BarChart3,
  Calendar,
  Zap,
  CheckCircle2,
} from 'lucide-react';
import { motion } from 'motion/react';

interface ConceptProgress {
  id: string;
  name: string;
  category: string;
  masteryLevel: number; // 0-100
  status: 'mastered' | 'proficient' | 'familiar' | 'beginner' | 'confused';
  lastReviewDate?: number;
  nextReviewDate?: number;
  practiceCount: number;
  errorCount: number;
  timeSpent: number; // 分钟
}

export function LearningProgressDashboard() {
  // 模拟数据 - 实际应从 store 获取
  const [concepts] = useState<ConceptProgress[]>([
    {
      id: 'c1',
      name: '条件概率',
      category: '概率论基础',
      masteryLevel: 85,
      status: 'proficient',
      lastReviewDate: new Date().getTime() - 86400000,
      nextReviewDate: new Date().getTime() + 604800000,
      practiceCount: 12,
      errorCount: 2,
      timeSpent: 180,
    },
    {
      id: 'c2',
      name: '贝叶斯定理',
      category: '概率论应用',
      masteryLevel: 62,
      status: 'familiar',
      lastReviewDate: new Date().getTime() - 259200000,
      nextReviewDate: new Date().getTime() + 259200000,
      practiceCount: 8,
      errorCount: 4,
      timeSpent: 120,
    },
    {
      id: 'c3',
      name: '二项分布',
      category: '统计分布',
      masteryLevel: 92,
      status: 'mastered',
      lastReviewDate: new Date().getTime() - 1209600000,
      nextReviewDate: new Date().getTime() + 1209600000,
      practiceCount: 20,
      errorCount: 1,
      timeSpent: 240,
    },
    {
      id: 'c4',
      name: '假设检验',
      category: '统计推断',
      masteryLevel: 35,
      status: 'beginner',
      practiceCount: 3,
      errorCount: 2,
      timeSpent: 45,
    },
    {
      id: 'c5',
      name: '正态分布',
      category: '统计分布',
      masteryLevel: 10,
      status: 'confused',
      practiceCount: 1,
      errorCount: 1,
      timeSpent: 15,
    },
  ]);

  const [sortBy, setSortBy] = useState<'mastery' | 'recent' | 'category'>(
    'mastery'
  );
  const [selectedCategory, setSelectedCategory] = useState<string | 'all'>('all');

  // 统计数据
  const stats = {
    totalConcepts: concepts.length,
    mastered: concepts.filter((c) => c.status === 'mastered').length,
    proficient: concepts.filter((c) => c.status === 'proficient').length,
    confused: concepts.filter((c) => c.status === 'confused').length,
    averageMastery:
      Math.round(
        concepts.reduce((sum, c) => sum + c.masteryLevel, 0) / concepts.length
      ) || 0,
    totalTimeSpent: concepts.reduce((sum, c) => sum + c.timeSpent, 0),
    totalPractice: concepts.reduce((sum, c) => sum + c.practiceCount, 0),
  };

  const categories = Array.from(new Set(concepts.map((c) => c.category)));

  const filteredConcepts =
    selectedCategory === 'all'
      ? concepts
      : concepts.filter((c) => c.category === selectedCategory);

  const sortedConcepts = [...filteredConcepts].sort((a, b) => {
    if (sortBy === 'mastery') {
      return b.masteryLevel - a.masteryLevel;
    } else if (sortBy === 'recent') {
      return (
        (b.lastReviewDate || 0) - (a.lastReviewDate || 0)
      );
    } else {
      return a.category.localeCompare(b.category);
    }
  });

  const getMasteryColor = (level: number) => {
    if (level >= 80) return 'from-green-400 to-green-600';
    if (level >= 60) return 'from-blue-400 to-blue-600';
    if (level >= 40) return 'from-yellow-400 to-yellow-600';
    if (level >= 20) return 'from-orange-400 to-orange-600';
    return 'from-red-400 to-red-600';
  };

  const getMasteryLabel = (status: ConceptProgress['status']) => {
    switch (status) {
      case 'mastered':
        return '[Mastered] Complete Mastery';
      case 'proficient':
        return '[Proficient] Proficient';
      case 'familiar':
        return '[Familiar] Familiar';
      case 'beginner':
        return '[Beginner] Learning';
      case 'confused':
        return '[Confused] Confused';
      default:
        return '[Unknown] Unknown';
    }
  };

  const getMasteryBgColor = (status: ConceptProgress['status']) => {
    switch (status) {
      case 'mastered':
        return 'bg-green-100';
      case 'proficient':
        return 'bg-blue-100';
      case 'familiar':
        return 'bg-blue-50';
      case 'beginner':
        return 'bg-yellow-100';
      case 'confused':
        return 'bg-red-100';
      default:
        return 'bg-stone-100';
    }
  };

  const getMasteryTextColor = (status: ConceptProgress['status']) => {
    switch (status) {
      case 'mastered':
        return 'text-green-700';
      case 'proficient':
        return 'text-blue-700';
      case 'familiar':
        return 'text-blue-600';
      case 'beginner':
        return 'text-yellow-700';
      case 'confused':
        return 'text-red-700';
      default:
        return 'text-stone-700';
    }
  };

  return (
    <div className="px-4 py-4 space-y-6 h-full overflow-y-auto">
      {/* Overview Stats */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="grid grid-cols-2 gap-4"
      >
        {/* Average Mastery */}
        <motion.div
          whileHover={{ scale: 1.05 }}
          className="bg-white rounded-lg p-4 border border-gray-200"
        >
          <div className="flex items-start justify-between mb-2">
            <div>
              <p className="text-xs text-stone-600 mb-1">平均掌握度</p>
              <div className="text-3xl font-bold text-gray-800">
                {stats.averageMastery}%
              </div>
            </div>
            <TrendingUp size={24} className="text-gray-600" />
          </div>
          <div className="text-xs text-stone-600 mt-2">
            基于 {stats.totalConcepts} 个概念
          </div>
        </motion.div>

        {/* Mastered */}
        <motion.div
          whileHover={{ scale: 1.05 }}
          className="bg-white rounded-lg p-4 border border-gray-200"
        >
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs text-stone-600 mb-1">完全掌握</p>
              <div className="text-3xl font-bold text-gray-800">
                {stats.mastered}
              </div>
            </div>
            <Award size={24} className="text-gray-600" />
          </div>
          <div className="text-xs text-stone-600 mt-2">
            {Math.round((stats.mastered / stats.totalConcepts) * 100)}% of total
          </div>
        </motion.div>

        {/* Study time */}
        <motion.div
          whileHover={{ scale: 1.05 }}
          className="bg-white rounded-lg p-4 border border-gray-200"
        >
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs text-stone-600 mb-1">总学习时间</p>
              <div className="text-3xl font-bold text-gray-800">
                {Math.floor(stats.totalTimeSpent / 60)}
              </div>
            </div>
            <Calendar size={24} className="text-gray-600" />
          </div>
          <div className="text-xs text-stone-600 mt-2">小时</div>
        </motion.div>

        {/* Practice count */}
        <motion.div
          whileHover={{ scale: 1.05 }}
          className="bg-white rounded-lg p-4 border border-gray-200"
        >
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs text-stone-600 mb-1">练习题</p>
              <div className="text-3xl font-bold text-gray-800">
                {stats.totalPractice}
              </div>
            </div>
            <Zap size={24} className="text-gray-600" />
          </div>
          <div className="text-xs text-stone-600 mt-2">道题目</div>
        </motion.div>
      </motion.div>

      {/* 学习进度图表 */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="bg-white rounded-lg border border-stone-200 p-6"
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-stone-900 flex items-center space-x-2">
            <BarChart3 size={20} />
            <span>学习分布</span>
          </h3>
        </div>

        <div className="space-y-3">
          {/* Mastery distribution */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-semibold text-stone-600">掌握度分布</span>
              <span className="text-xs text-stone-500">
                {concepts.filter((c) => c.masteryLevel >= 80).length}
                个高掌握度
              </span>
            </div>
            <div className="flex space-x-2">
              {[
                {
                  range: '90-100',
                  count: concepts.filter((c) => c.masteryLevel >= 90).length,
                  color: 'bg-green-600',
                },
                {
                  range: '70-89',
                  count: concepts.filter(
                    (c) => c.masteryLevel >= 70 && c.masteryLevel < 90
                  ).length,
                  color: 'bg-green-400',
                },
                {
                  range: '50-69',
                  count: concepts.filter(
                    (c) => c.masteryLevel >= 50 && c.masteryLevel < 70
                  ).length,
                  color: 'bg-yellow-400',
                },
                {
                  range: '30-49',
                  count: concepts.filter(
                    (c) => c.masteryLevel >= 30 && c.masteryLevel < 50
                  ).length,
                  color: 'bg-orange-400',
                },
                {
                  range: '0-29',
                  count: concepts.filter((c) => c.masteryLevel < 30).length,
                  color: 'bg-red-500',
                },
              ].map((item) => (
                <motion.div
                  key={item.range}
                  whileHover={{ scale: 1.1 }}
                  title={`${item.range}: ${item.count} 个概念`}
                  className={`flex-1 h-12 ${item.color} rounded flex items-center justify-center cursor-pointer hover:shadow-lg transition-shadow`}
                >
                  <span className="text-xs font-bold text-white">
                    {item.count}
                  </span>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Status distribution */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-stone-600">学习阶段</span>
            </div>
            <div className="space-y-2">
              {[
                { status: 'mastered', color: 'bg-green-500' },
                { status: 'proficient', color: 'bg-blue-500' },
                { status: 'familiar', color: 'bg-blue-300' },
                { status: 'beginner', color: 'bg-yellow-500' },
                { status: 'confused', color: 'bg-red-500' },
              ].map((item) => {
                const count = concepts.filter((c) => c.status === item.status as 'mastered' | 'proficient' | 'familiar' | 'beginner' | 'confused').length;
                const percentage = Math.round((count / concepts.length) * 100);
                return (
                  <motion.div
                    key={item.status}
                    initial={{ width: 0 }}
                    animate={{ width: '100%' }}
                    className="flex items-center space-x-2"
                  >
                    <div className="w-20 text-xs font-semibold text-stone-600">
                      {getMasteryLabel(item.status as 'mastered' | 'proficient' | 'familiar' | 'beginner' | 'confused')}
                    </div>
                    <div className="flex-1 h-6 bg-stone-100 rounded overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${percentage}%` }}
                        transition={{ delay: 0.3 }}
                        className={`h-full ${item.color} flex items-center justify-end pr-2`}
                      >
                        {percentage > 5 && (
                          <span className="text-xs font-bold text-white">
                            {percentage}%
                          </span>
                        )}
                      </motion.div>
                    </div>
                    <div className="w-12 text-right text-xs text-stone-600">
                      {count} 个
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </div>
        </div>
      </motion.div>

      {/* Concepts List */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="bg-white rounded-lg border border-stone-200 overflow-hidden"
      >
        <div className="px-6 py-4 border-b border-stone-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-gray-900">学习进度详情</h3>
          </div>

          {/* Filters */}
          <div className="flex items-center space-x-3 flex-wrap gap-2">
            {/* Sort */}
            <div className="flex space-x-1">
              {(
                ['mastery', 'recent', 'category'] as const
              ).map((sort) => (
                <motion.button
                  key={sort}
                  onClick={() => setSortBy(sort)}
                  className={`text-xs px-2 py-1 rounded transition-all ${
                    sortBy === sort
                      ? 'bg-gray-800 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                  whileHover={{ scale: 1.05 }}
                >
                  {sort === 'mastery'
                    ? '按掌握度'
                    : sort === 'recent'
                      ? '按最近'
                      : '按分类'}
                </motion.button>
              ))}
            </div>

            {/* Category filter */}
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value as string | 'all')}
              className="text-xs px-2 py-1 rounded border border-stone-300 bg-white hover:bg-stone-50"
            >
              <option value="all">所有分类</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* List */}
        <div className="divide-y divide-stone-200">
          {sortedConcepts.map((concept, idx) => (
            <motion.div
              key={concept.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.05 }}
              className={`p-4 hover:bg-stone-50 transition-colors`}
            >
              <div className="flex items-start space-x-4">
                {/* Status icon */}
                <div className="flex-shrink-0 mt-1">
                  {concept.status === 'mastered' ? (
                    <CheckCircle2 size={20} className="text-green-600" />
                  ) : concept.status === 'confused' ? (
                    <AlertCircle size={20} className="text-red-600" />
                  ) : (
                    <Target size={20} className="text-stone-400" />
                  )}
                </div>

                {/* Content */}
                <div className="flex-1">
                  <div className="flex items-baseline justify-between mb-2">
                    <div>
                      <h4 className="font-semibold text-stone-900">
                        {concept.name}
                      </h4>
                      <p className="text-xs text-stone-500">{concept.category}</p>
                    </div>
                    <div className={`text-xs font-semibold px-2 py-1 rounded ${getMasteryBgColor(concept.status)} ${getMasteryTextColor(concept.status)}`}>
                      {getMasteryLabel(concept.status)}
                    </div>
                  </div>

                  {/* Progress bar */}
                  <div className="mb-2">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-stone-600">掌握度</span>
                      <span className="text-xs font-bold text-stone-700">
                        {concept.masteryLevel}%
                      </span>
                    </div>
                    <div className="w-full h-2 bg-stone-200 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${concept.masteryLevel}%` }}
                        transition={{ delay: 0.3 }}
                        className={`h-full bg-gradient-to-r ${getMasteryColor(concept.masteryLevel)}`}
                      />
                    </div>
                  </div>

                  {/* Stats */}
                  <div className="flex items-center space-x-4 text-xs text-stone-600">
                    <span>✏️ {concept.practiceCount} 道</span>
                    <span>❌ {concept.errorCount} 错</span>
                    <span>⏱️ {concept.timeSpent} 分钟</span>
                    {concept.nextReviewDate && (
                      <span className="text-indigo-600">
                        📅 下次复习：
                        {new Date(concept.nextReviewDate).toLocaleDateString('zh-CN')}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Recommendations */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-lg p-6 border border-gray-200"
      >
        <h3 className="text-lg font-bold text-stone-900 mb-3 flex items-center space-x-2">
          <Zap size={20} className="text-indigo-600" />
          <span>学习建议</span>
        </h3>
        <ul className="space-y-2 text-sm text-stone-700">
          <li>
            ✅ 你已掌握 {stats.mastered} 个核心概念。继续保持复习频率。
          </li>
          <li>
            🔴 有 {stats.confused} 个概念还在困惑中。建议立即启动相关任务。
          </li>
          <li>
            📈 基于艾宾浩斯遗忘曲线，现在是复习"二项分布"的最佳时机。
          </li>
          <li>
            💡 你的学习效率在上升。继续保持这个节奏！
          </li>
        </ul>
      </motion.div>
    </div>
  );
}
