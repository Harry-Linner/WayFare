import { useState, useEffect, useMemo } from 'react';
import { Send, Bot, Brain, Lightbulb, Star } from 'lucide-react';
import type { ChatMessage } from '../types.js';
import { motion, AnimatePresence } from 'motion/react';
import { useAppStore } from '../store/appStore';

/**
 * 增强的 Sidebar - AI 导师助手
 * 支持：
 * 1. 双向对话（用户提问，AI 回答）
 * 2. 主动式推送（AI 主动发现问题并推送消息）
 * 3. 智能建议（基于学习进度推荐资源）
 * 4. 个性化交互（根据用户风格调整）
 */
export function Sidebar() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'chat' | 'proactive' | 'progress'>('chat');

  const { conversations, currentConversationId, addChatMessage, getAgentTasksByStatus } =
    useAppStore();

  // 初始化当前对话的消息
  const displayMessages = useMemo(() => {
    const currentConv = conversations.find((c) => c.id === currentConversationId);
    return currentConv ? currentConv.messages : [];
  }, [currentConversationId, conversations]);

  // 同步 store 中的消息到本地状态
  useEffect(() => {
    setMessages(displayMessages);
  }, [displayMessages]);

  const proactiveTasks = getAgentTasksByStatus('completed');

  const handleSend = async () => {
    if (!input.trim() || !currentConversationId) return;

    const newUserMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    };

    setMessages([...messages, newUserMsg]);
    addChatMessage(currentConversationId, newUserMsg);
    setInput('');
    setIsLoading(true);

    // 模拟 AI 响应
    setTimeout(() => {
      const aiMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '好的，正在为你调用费曼转化器...\n\n这个问题很好！让我用通俗的方式为你解释...',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, aiMsg]);
      addChatMessage(currentConversationId, aiMsg);
      setIsLoading(false);
    }, 1000);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header with Tabs */}
      <div className="border-b border-gray-200 bg-white">
        <div className="p-3">
          <div className="flex items-center space-x-2 mb-3">
            <Bot size={18} className="text-gray-600" />
            <h2 className="font-semibold text-gray-800">AI Tutor Assistant</h2>
            <span className="ml-auto text-xs text-stone-500 flex items-center space-x-1">
              <Brain size={14} />
              <span>Sidecar Kernel</span>
            </span>
          </div>

          {/* Tab Navigation */}
          <div className="flex space-x-2">
            {[
              { id: 'chat', label: 'Chat', icon: 'Chat' },
              { id: 'proactive', label: 'Suggestions', icon: 'Suggestions', badge: proactiveTasks.length },
              { id: 'progress', label: 'Progress', icon: 'Progress' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as 'chat' | 'proactive' | 'progress')}
                className={`flex-1 px-2 py-1.5 rounded-lg text-xs font-medium transition-colors relative ${
                  activeTab === tab.id
                    ? 'bg-gray-200 text-gray-900'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <span className="mr-1">{tab.icon}</span>
                {tab.label}
                {tab.badge && (
                  <span className="absolute -top-1 -right-1 inline-flex items-center justify-center px-2 py-0.5 text-xs font-bold leading-none text-white transform translate-x-1/2 -translate-y-1/2 bg-red-500 rounded-full">
                    {tab.badge}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-hidden flex flex-col">
        <AnimatePresence mode="wait">
          {activeTab === 'chat' && (
            <motion.div
              key="chat"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex-1 flex flex-col overflow-hidden"
            >
              {/* Chat Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-stone-50">
                {messages.map((msg) => (
                  <motion.div
                    key={msg.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                        msg.role === 'user'
                          ? 'bg-indigo-600 text-white rounded-tr-sm'
                          : 'bg-stone-100 text-stone-800 rounded-tl-sm'
                      }`}
                    >
                      <div className="text-sm leading-relaxed whitespace-pre-wrap">
                        {msg.content}
                      </div>
                      <p className="text-xs opacity-60 mt-1">
                        {new Date(msg.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                  </motion.div>
                ))}
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-stone-100 text-stone-800 rounded-2xl rounded-tl-sm px-4 py-3">
                      <div className="flex space-x-2">
                        <div className="w-2 h-2 rounded-full bg-stone-400 animate-bounce" />
                        <div className="w-2 h-2 rounded-full bg-stone-400 animate-bounce delay-100" />
                        <div className="w-2 h-2 rounded-full bg-stone-400 animate-bounce delay-200" />
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Input Area */}
              <div className="p-4 border-t border-stone-200 bg-white">
                <div className="relative flex items-center">
                  <textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSend();
                      }
                    }}
                    placeholder="向 AI 导师提问..."
                    className="w-full bg-stone-50 border border-stone-200 rounded-xl pl-4 pr-12 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 resize-none"
                    rows={1}
                  />
                  <button
                    onClick={handleSend}
                    disabled={!input.trim() || isLoading}
                    className="absolute right-2 w-8 h-8 flex items-center justify-center text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Send size={18} />
                  </button>
                </div>
                <div className="mt-2 text-xs text-stone-400 text-center">
                  基于本地 RAG 引擎与教育专用模型
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'proactive' && (
            <motion.div
              key="proactive"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex-1 overflow-y-auto p-4 space-y-3"
            >
              {proactiveTasks.length === 0 ? (
                <div className="h-full flex items-center justify-center text-center text-stone-400">
                  <div>
                    <Lightbulb size={32} className="mx-auto mb-2 opacity-50" />
                    <p className="text-xs">暂无主动建议</p>
                  </div>
                </div>
              ) : (
                proactiveTasks.map((task) => (
                  <motion.div
                    key={task.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="bg-indigo-50 border border-indigo-200 rounded-lg p-3"
                  >
                    <div className="flex items-start space-x-2">
                      <span className="text-lg">✨</span>
                      <p className="text-xs font-semibold text-indigo-900">AI 建议</p>
                    </div>
                  </motion.div>
                ))
              )}
            </motion.div>
          )}

          {activeTab === 'progress' && (
            <motion.div
              key="progress"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex-1 overflow-y-auto p-4 space-y-4"
            >
              <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg p-4 border border-green-200">
                <div className="flex items-center space-x-2 mb-3">
                  <Star size={18} className="text-green-600" />
                  <h3 className="text-sm font-semibold text-green-900">学习进度</h3>
                </div>
                <div className="space-y-2 text-xs text-green-800">
                  <div className="flex justify-between">
                    <span>总批注</span>
                    <span className="font-bold">42</span>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
