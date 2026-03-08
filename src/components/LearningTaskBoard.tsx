/**
 * 学习任务看板
 * 展示所有主动式任务：何时需要复习、什么 misconception 需要澄清、什么是当前重点
 * 这直接支持 WayFare 第1、4特性：主动式工作 + 强交互性
 */
import { useState } from 'react';
import {
  CheckCircle2,
  Circle,
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

type TaskStatus = 'pending' | 'in_progress' | 'completed';
type TaskType =
  | 'content_enrichment'
  | 'question_generation'
  | 'confusion_detection'
  | 'resource_recommendation'
  | 'misconception_correction'
  | 'learning_reminder';

interface TaskBoardItem {
  id: string;
  type: TaskType;
  title: string;
  description: string;
  conceptName: string;
  priority: 'critical' | 'high' | 'medium' | 'low';
  status: TaskStatus;
  dueDate: number;
  createdAt: number;
  progress?: number;
}

export function LearningTaskBoard() {
  // 模拟任务数据 - 实际应从 store 获取
  const [tasks, setTasks] = useState<TaskBoardItem[]>([
    {
      id: 'task_1',
      type: 'content_enrichment',
      title: '概率论：条件概率的核心困难点',
      description: '系统检测到你在条件概率上停留很久。已自动查找了 3 篇深入讲解。',
      conceptName: '条件概率',
      priority: 'critical',
      status: 'pending',
      dueDate: new Date().getTime() + 3600000,
      createdAt: new Date().getTime() - 300000,
    },
    {
      id: 'task_2',
      type: 'question_generation',
      title: '生成与你不足相关的练习题',
      description: '基于你最近的错误, AI 生成了 5 道针对性练习。',
      conceptName: '贝叶斯定理应用',
      priority: 'high',
      status: 'pending',
      dueDate: new Date().getTime() + 86400000,
      createdAt: new Date().getTime() - 7200000,
    },
    {
      id: 'task_3',
      type: 'misconception_correction',
      title: '澄清常见误区：P(A|B) ≠ P(B|A)',
      description: '你在练习中多次混淆这两个，系统已准备了详细讲解。',
      conceptName: '条件概率对称性错误',
      priority: 'critical',
      status: 'in_progress',
      dueDate: new Date().getTime() + 1800000,
      createdAt: new Date().getTime() - 600000,
      progress: 40,
    },
    {
      id: 'task_4',
      type: 'learning_reminder',
      title: '复习进度：二项分布（艾宾浩斯计划）',
      description: '距你上次掌握已 2 周。根据遗忘曲线，现在复习最佳。',
      conceptName: '二项分布',
      priority: 'medium',
      status: 'pending',
      dueDate: new Date().getTime() + 604800000,
      createdAt: new Date().getTime() - 1209600000,
    },
    {
      id: 'task_5',
      type: 'resource_recommendation',
      title: '推荐资源：条件概率的可视化教学视频',
      description: '找到了一个评分 4.9/5 的教学视频，特别适合可视化学习者。',
      conceptName: '条件概率可视化',
      priority: 'medium',
      status: 'pending',
      dueDate: new Date().getTime() + 259200000,
      createdAt: new Date().getTime() - 43200000,
    },
  ]);

  const [filterStatus, setFilterStatus] = useState<TaskStatus | 'all'>('all');
  const [sortBy, setSortBy] = useState<'priority' | 'dueDate'>('priority');

  const getTaskTypeLabel = (type: TaskType) => {
    switch (type) {
      case 'content_enrichment':
        return '[Content] Content Enrichment';
      case 'question_generation':
        return '[Practice] Practice Questions';
      case 'confusion_detection':
        return '[Detect] Confusion Detection';
      case 'misconception_correction':
        return '[Fix] Fix Misconceptions';
      case 'resource_recommendation':
        return '[Resources] Recommended Resources';
      case 'learning_reminder':
        return '[Review] Review & Reflect';
      default:
        return '[Task] Task';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical':
        return '🔴 critical';
      case 'high':
        return '🟠 high';
      case 'medium':
        return '🟡 medium';
      case 'low':
        return '🟢 low';
      default:
        return '⚪ unknown';
    }
  };

  const getStatusIcon = (status: TaskStatus) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 size={20} className="text-green-600" />;
      case 'in_progress':
        return <Circle size={20} className="text-yellow-600 fill-yellow-200" />;
      case 'pending':
        return <Circle size={20} className="text-stone-400" />;
      default:
        return <Circle size={20} />;
    }
  };

  const filteredTasks =
    filterStatus === 'all'
      ? tasks
      : tasks.filter((task) => task.status === filterStatus);

  const sortedTasks = [...filteredTasks].sort((a, b) => {
    if (sortBy === 'priority') {
      const priorityOrder: Record<string, number> = {
        critical: 0,
        high: 1,
        medium: 2,
        low: 3,
      };
      return priorityOrder[a.priority] - priorityOrder[b.priority];
    } else {
      return a.dueDate - b.dueDate;
    }
  });

  const handleTaskComplete = (taskId: string) => {
    setTasks((prev) =>
      prev.map((task) =>
        task.id === taskId ? { ...task, status: 'completed' } : task
      )
    );
  };

  const handleTaskStart = (taskId: string) => {
    setTasks((prev) =>
      prev.map((task) =>
        task.id === taskId ? { ...task, status: 'in_progress' } : task
      )
    );
  };

  const stats = {
    total: tasks.length,
    completed: tasks.filter((t) => t.status === 'completed').length,
    inProgress: tasks.filter((t) => t.status === 'in_progress').length,
    pending: tasks.filter((t) => t.status === 'pending').length,
    critical: tasks.filter((t) => t.priority === 'critical').length,
  };

  return (
    <div className="px-4 py-4 space-y-6 h-full overflow-y-auto">
      {/* Header Stats */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-lg p-4 border border-gray-200"
      >
        <h2 className="text-2xl font-bold text-stone-900 mb-4">
          📋 我为你精心准备的学习任务
        </h2>
        <p className="text-sm text-gray-600 mb-4">
          这些都是系统主动为你生成的个性化任务。完成它们将大大加速你的学习进度。
        </p>

        <div className="grid grid-cols-2 gap-3">
          <motion.div
            whileHover={{ scale: 1.05 }}
            className="bg-white rounded-lg p-3 border border-indigo-200 text-center"
          >
            <div className="text-3xl font-bold text-indigo-600">{stats.total}</div>
            <div className="text-xs text-stone-600 mt-1">总任务数</div>
          </motion.div>

          <motion.div
            whileHover={{ scale: 1.05 }}
            className="bg-white rounded-lg p-3 border border-green-200 text-center"
          >
            <div className="text-3xl font-bold text-green-600">
              {stats.completed}
            </div>
            <div className="text-xs text-stone-600 mt-1">已完成</div>
          </motion.div>

          <motion.div
            whileHover={{ scale: 1.05 }}
            className="bg-white rounded-lg p-3 border border-yellow-200 text-center"
          >
            <div className="text-3xl font-bold text-yellow-600">
              {stats.inProgress}
            </div>
            <div className="text-xs text-stone-600 mt-1">进行中</div>
          </motion.div>

          <motion.div
            whileHover={{ scale: 1.05 }}
            className="bg-white rounded-lg p-3 border border-blue-200 text-center"
          >
            <div className="text-3xl font-bold text-blue-600">{stats.pending}</div>
            <div className="text-xs text-stone-600 mt-1">待开始</div>
          </motion.div>

          <motion.div
            whileHover={{ scale: 1.05 }}
            className="bg-white rounded-lg p-3 border border-red-200 text-center"
          >
            <div className="text-3xl font-bold text-red-600">{stats.critical}</div>
            <div className="text-xs text-stone-600 mt-1">急需关注</div>
          </motion.div>
        </div>
      </motion.div>

      {/* Controls */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex items-center space-x-4 flex-wrap"
      >
        <div className="flex space-x-2">
          {(
            ['all', 'pending', 'in_progress', 'completed'] as const
          ).map((status) => (
            <motion.button
              key={status}
              onClick={() => setFilterStatus(status)}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                filterStatus === status
                  ? 'bg-indigo-600 text-white'
                  : 'bg-stone-200 text-stone-700 hover:bg-stone-300'
              }`}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              {status === 'all'
                ? '全部'
                : status === 'pending'
                  ? '待开始'
                  : status === 'in_progress'
                    ? '进行中'
                    : '已完成'}
            </motion.button>
          ))}
        </div>

        <div className="flex space-x-2">
          <motion.button
            onClick={() => setSortBy('priority')}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
              sortBy === 'priority'
                ? 'bg-purple-600 text-white'
                : 'bg-stone-200 text-stone-700 hover:bg-stone-300'
            }`}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            按优先级
          </motion.button>
          <motion.button
            onClick={() => setSortBy('dueDate')}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
              sortBy === 'dueDate'
                ? 'bg-purple-600 text-white'
                : 'bg-stone-200 text-stone-700 hover:bg-stone-300'
            }`}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            按截止时间
          </motion.button>
        </div>
      </motion.div>

      {/* Task List */}
      <div className="space-y-3">
        <AnimatePresence mode="popLayout">
          {sortedTasks.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-12 bg-stone-50 rounded-lg border-2 border-dashed border-stone-300"
            >
              <div className="text-4xl mb-2">✨</div>
              <p className="text-stone-600">
                {filterStatus === 'completed'
                  ? '太棒了！你已经完成了所有任务！'
                  : '暂无任务。系统将在你需要时自动生成新任务。'}
              </p>
            </motion.div>
          ) : (
            sortedTasks.map((task, idx) => (
              <motion.div
                key={task.id}
                layout
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ delay: idx * 0.05 }}
                className="bg-white border-2 border-gray-200 rounded-lg p-4 transition-all cursor-pointer"
                onClick={() => {
                  if (task.status === 'pending') {
                    handleTaskStart(task.id);
                  }
                }}
              >
                <div className="flex items-start space-x-4">
                  {/* Status checkbox */}
                  <motion.button
                    whileHover={{ scale: 1.2 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleTaskComplete(task.id);
                    }}
                    className="flex-shrink-0 mt-1"
                  >
                    {getStatusIcon(task.status)}
                  </motion.button>

                  {/* Content */}
                  <div className="flex-1">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <div className="flex items-center space-x-2 mb-1">
                          <span className="text-sm font-bold text-stone-900">
                            {task.title}
                          </span>
                          <span className="text-xs px-2 py-0.5 rounded-full bg-white bg-opacity-60">
                            {getTaskTypeLabel(task.type)}
                          </span>
                        </div>
                        <p className="text-sm text-stone-700">{task.description}</p>
                      </div>

                      {/* Priority badge */}
                      <div className="flex-shrink-0">
                        <span className="text-xs font-bold px-2 py-1 rounded bg-white bg-opacity-70">
                          {getPriorityColor(task.priority)}
                        </span>
                      </div>
                    </div>

                    {/* Progress bar if in progress */}
                    {task.status === 'in_progress' && task.progress !== undefined && (
                      <div className="mb-2">
                        <div className="w-full bg-white bg-opacity-40 rounded-full h-2">
                          <motion.div
                            className="bg-white bg-opacity-80 h-full rounded-full"
                            initial={{ width: 0 }}
                            animate={{ width: `${task.progress}%` }}
                            transition={{ duration: 0.5 }}
                          />
                        </div>
                        <p className="text-xs text-stone-600 mt-1">
                          进度：{task.progress}%
                        </p>
                      </div>
                    )}

                    {/* Footer */}
                    <div className="flex items-center justify-between mt-2 text-xs text-stone-600">
                      <div className="space-x-3">
                        <span>
                          {task.conceptName}
                        </span>
                        <span>
                          ⏰{' '}
                          {new Date(task.dueDate).toLocaleDateString('zh-CN', {
                            month: 'short',
                            day: 'numeric',
                          })}
                        </span>
                      </div>
                      {task.status === 'pending' && (
                        <motion.button
                          whileHover={{ scale: 1.05 }}
                          onClick={() => handleTaskStart(task.id)}
                          className="bg-white bg-opacity-60 hover:bg-opacity-100 px-3 py-1 rounded font-semibold text-stone-700 transition-all"
                        >
                          开始 →
                        </motion.button>
                      )}
                    </div>
                  </div>
                </div>
              </motion.div>
            ))
          )}
        </AnimatePresence>
      </div>

      {/* Motivational footer */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-lg p-6 border border-gray-200 text-center"
      >
        <p className="text-sm text-gray-700 font-semibold mb-2">
          Every completed task brings you one step closer to mastery!
        </p>
        <p className="text-xs text-gray-600">
          系统会持续监测你的学习状态，并据此调整任务难度和类型。这就是真正的个性化学习。
        </p>
      </motion.div>
    </div>
  );
}
