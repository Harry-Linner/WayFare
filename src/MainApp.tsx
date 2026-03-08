/**
 * 主应用界面
 * 核心学习环境，整合了阅读器、批注面板、任务看板、进度统计
 * 
 * 🔥 修复漏洞#5：现在右侧栏默认显示批注面板，而非通用AI助手
 * 这样用户可以直接看到当前阅读位置相关的所有内容
 */
import { useState } from 'react';
import { motion } from 'motion/react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Header } from './components/Header';
import { Reader } from './components/Reader';
import { AgentHub } from './components/AgentHub';
import { AnnotationPanel } from './components/AnnotationPanel';
import { LearningTaskBoard } from './components/LearningTaskBoard';
import { LearningProgressDashboard } from './components/LearningProgressDashboard';
import { useAppStore } from './store/appStore';
import { useBackendEventListeners } from './hooks/useBackendEvents';

type PanelView = 'annotations' | 'agent' | 'tasks' | 'progress' | 'settings';

export function MainApp() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [bottomPanelOpen, setBottomPanelOpen] = useState(true);
  const [activePanel, setActivePanel] = useState<PanelView>('annotations');
  const [showNotifications, setShowNotifications] = useState(false);

  const { currentDocument } = useAppStore();

  // 全局后端事件监听（仅在这里调用一次，所有子组件可访问事件）
  useBackendEventListeners({
    autoAddMessages: true,
    onError: (error) => {
      console.error('❌ 后端事件监听错误:', error);
    },
  });

  const handleSettingsClick = () => {
    setSidebarOpen(true);
    setActivePanel('settings');
  };

  const handleNotificationsClick = () => {
    setShowNotifications(!showNotifications);
  };

  return (
    <div className="flex flex-col h-screen bg-white text-gray-900 font-sans overflow-hidden">
      {/* Header */}
      <Header 
        onSettingsClick={handleSettingsClick}
        onNotificationsClick={handleNotificationsClick}
      />

      {/* Main Content Area */}
      <div className="flex flex-1 overflow-hidden gap-1 bg-stone-100 p-1">
        {/* Left: Document Reader */}
        <motion.main
          layout
          className="flex-1 relative overflow-hidden flex flex-col bg-white rounded-lg border border-gray-200"
        >
          {currentDocument ? (
            <Reader documentId={currentDocument.id} />
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center space-y-4">
                <div className="text-6xl">📚</div>
                <p className="text-gray-600">Select or upload learning materials to begin</p>
                <button className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors">
                  上传资料
                </button>
              </div>
            </div>
          )}
        </motion.main>

        {/* Right: Sidebar with Tabs */}
        {sidebarOpen && (
          <motion.aside
            layout
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="w-96 bg-white rounded-lg border border-gray-200 flex flex-col overflow-hidden"
          >
            {/* Sidebar Header */}
              <div className="px-4 py-3 border-b border-gray-200 bg-white">
              <div className="flex items-center justify-between">
                <h2 className="font-bold text-gray-900">AI Assistant</h2>
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setSidebarOpen(false)}
                  className="p-1 hover:bg-stone-200 rounded transition-colors"
                >
                  <ChevronRight size={18} />
                </motion.button>
              </div>

              {/* Tab Navigation */}
              <div className="flex flex-wrap gap-2 mt-3">
                {[
                  { id: 'annotations' as const, label: '批注', icon: '📝' },
                  { id: 'agent' as const, label: 'Chat', icon: '💬' },
                  { id: 'tasks' as const, label: 'Tasks', icon: '✓' },
                  { id: 'progress' as const, label: 'Progress', icon: '📊' },
                  { id: 'settings' as const, label: 'Settings', icon: '⚙️' },
                ].map((tab) => (
                  <motion.button
                    key={tab.id}
                    onClick={() => setActivePanel(tab.id)}
                    className={`px-3 py-2 rounded text-xs font-medium transition-all whitespace-nowrap ${
                      activePanel === tab.id
                        ? 'bg-gray-800 text-white'
                        : 'bg-white text-gray-600 hover:bg-gray-100'
                    }`}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    {tab.label}
                  </motion.button>
                ))}
              </div>
            </div>

            {/* Sidebar Content */}
            <div className="flex-1 overflow-y-auto bg-stone-50">
              {activePanel === 'annotations' && currentDocument && (
                <AnnotationPanel documentId={currentDocument.id} />
              )}
              {activePanel === 'agent' && <AgentHub documentId={currentDocument?.id} />}
              {activePanel === 'tasks' && <LearningTaskBoard />}
              {activePanel === 'progress' && <LearningProgressDashboard />}
              {activePanel === 'settings' && (
                <div className="px-4 py-4 space-y-4">
                  <div>
                    <label className="block text-sm font-semibold text-stone-900 mb-2">
                      学习偏好设置
                    </label>
                    <div className="space-y-2 text-sm text-stone-700">
                      <div className="flex items-center justify-between p-2 bg-stone-50 rounded">
                        <span>主动消息提醒</span>
                        <input type="checkbox" defaultChecked className="w-4 h-4" />
                      </div>
                      <div className="flex items-center justify-between p-2 bg-stone-50 rounded">
                        <span>禁用卡顿检测</span>
                        <input type="checkbox" className="w-4 h-4" />
                      </div>
                      <div className="flex items-center justify-between p-2 bg-stone-50 rounded">
                        <span>启用数据同步</span>
                        <input type="checkbox" defaultChecked className="w-4 h-4" />
                      </div>
                    </div>
                  </div>
                  <div className="pt-4 border-t border-stone-200">
                    <button className="w-full px-3 py-2 bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors text-sm font-semibold">
                      清空所有数据
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Sidebar Footer */}
            <div className="px-4 py-3 border-t border-gray-200 bg-white text-xs text-gray-500">
              <p className="text-xs text-gray-500">Tip: System is monitoring your learning progress in real-time</p>
            </div>
          </motion.aside>
        )}

        {/* Sidebar Toggle Button */}
        {!sidebarOpen && (
          <motion.button
            layout
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            onClick={() => setSidebarOpen(true)}
            className="w-10 bg-white rounded-lg border border-stone-200 shadow-sm flex items-center justify-center hover:bg-stone-50 transition-colors"
          >
            <ChevronLeft size={20} className="text-stone-600" />
          </motion.button>
        )}
      </div>

      {/* Bottom Panel: Cognitive Breadcrumb Timeline (Optional) */}
      {bottomPanelOpen && currentDocument && (
        <motion.div
          layout
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="h-48 bg-white border-t border-gray-200 overflow-y-auto"
        >
          <div className="p-4 flex items-center justify-between border-b border-gray-200 bg-white">
            <h3 className="font-bold text-gray-900">Learning Journey</h3>
            <motion.button
              whileHover={{ scale: 1.1 }}
              onClick={() => setBottomPanelOpen(false)}
              className="text-stone-600 hover:text-stone-900"
            >
              ×
            </motion.button>
          </div>

          {/* Timeline Preview */}
          <div className="p-4 space-y-2">
            <div className="text-sm text-stone-600 italic">
              📝 点击任何批注查看详细的学习轨迹：何时困惑、何时理解、何时掌握...
            </div>
            <div className="flex space-x-2 overflow-x-auto pb-2">
              {['困惑', '理解', '掌握', '应用'].map((stage, idx) => (
                <div
                  key={idx}
                  className="px-3 py-1 bg-gray-100 rounded-full text-xs text-gray-700 whitespace-nowrap"
                >
                  {stage}
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      )}

      {/* Notifications Panel */}
      {showNotifications && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          className="absolute top-14 right-6 w-80 bg-white rounded-lg border border-gray-200 shadow-lg z-50"
        >
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-gray-900">通知</h3>
              <motion.button
                whileHover={{ scale: 1.1 }}
                onClick={() => setShowNotifications(false)}
                className="text-stone-600 hover:text-stone-900"
              >
                ×
              </motion.button>
            </div>
          </div>
          <div className="max-h-96 overflow-y-auto">
            <div className="p-4 space-y-3">
              <div className="p-3 bg-blue-50 border border-blue-200 rounded">
                <p className="text-sm font-semibold text-blue-900">学习建议</p>
                <p className="text-xs text-blue-700 mt-1">您在认知心理学章节的进度已达到 75%</p>
              </div>
              <div className="p-3 bg-green-50 border border-green-200 rounded">
                <p className="text-sm font-semibold text-green-900">任务完成</p>
                <p className="text-xs text-green-700 mt-1">您已完成今日的学习任务</p>
              </div>
              <div className="p-3 bg-yellow-50 border border-yellow-200 rounded">
                <p className="text-sm font-semibold text-yellow-900">提醒</p>
                <p className="text-xs text-yellow-700 mt-1">您有 2 个待处理的问题需要回答</p>
              </div>
            </div>
          </div>
          <div className="p-3 border-t border-gray-200 text-center">
            <button className="text-xs text-blue-600 hover:text-blue-800 font-medium">
              查看所有通知
            </button>
          </div>
        </motion.div>
      )}

      {/* Floating Action Buttons - Removed to avoid overlaying send button */}
    </div>
  );
}
