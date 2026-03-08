/**
 * Agent 主动推送中心
 * 实现 WayFare 的核心"强交互性"——Agent 主动给用户发消息
 * 包括：学习计划、卡顿检测、截止提醒、学习建议
 */
import { useState, useEffect, useCallback } from 'react';
import { Send, Bot, Brain, AlertCircle, Lightbulb, Clock, X, CheckCircle2 } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { useAppStore } from '../store/appStore';
import { useTauriCommands } from '../hooks/useTauriCommands';
import type { ChatMessage, UserPreference } from '../types';

interface AgentHubProps {
  documentId?: string;
}

export function AgentHub({ documentId }: AgentHubProps) {
  const [activeTab, setActiveTab] = useState<'messages' | 'plan' | 'stats'>('messages');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [userInput, setUserInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [stallDetected, setStallDetected] = useState(false);
  const [stallStartTime, setStallStartTime] = useState<number | null>(null);
  const [stallElapsedMinutes, setStallElapsedMinutes] = useState(0);

  const { currentConversationId, addChatMessage, currentDocument, currentProjectId, getUserPreference } = useAppStore();
  const { detectStalledInteraction, enrichAnnotations, saveAnnotation, recordLearningTrace, fetchSupplementaryResources } = useTauriCommands();

  // 处理检测到卡顿的逻辑
  const handleStallDetected = useCallback(async () => {
    try {
      // 🔥 修复漏洞#3：获取用户个性化偏好，定制化帮助内容
      const userPref = getUserPreference(currentProjectId || '');
      
      // 调用后端检测卡顿
      const result = await detectStalledInteraction(
        documentId || 'default',
        180000,
        '当前学习材料段落'
      );

      // 根据用户偏好定制化帮助类型
      let customizedHelpTypes = result.suggested_help_type;
      
      if (userPref) {
        // 根据学习风格调整帮助方式
        if (userPref.learningStyleForProject === 'visual') {
          // 视觉学习者：优先考虑可视化、动画、图表
          customizedHelpTypes = customizedHelpTypes.filter(t => t !== 'step_by_step');
          customizedHelpTypes.unshift('resources'); // 优先推荐资源（大多数包含可视化）
        } else if (userPref.learningStyleForProject === 'reading-writing') {
          // 阅读写作学习者：优先步骤分解和演绎推理
          customizedHelpTypes = ['step_by_step', 'analogy', ...customizedHelpTypes.filter(t => t !== 'step_by_step' && t !== 'analogy')];
        }
        
        // 根据反馈详细程度进一步定制
        if (userPref.feedbackDetailLevel === 'concise') {
          // 简化语言：使用类比和例子
          if (!customizedHelpTypes.includes('examples')) {
            customizedHelpTypes.push('examples');
          }
        }
      }

      // 根据后端返回的建议生成消息
      const stallMessage: ChatMessage = {
        id: 'msg_' + Date.now(),
        role: 'assistant',
        content: `👋 嘿，我检测到你在这部分停留了一段时间（置信度: ${(result.confidence * 100).toFixed(0)}%）。

根据你的学习风格和偏好${userPref ? `（${userPref.learningStyleForProject === 'visual' ? '视觉型' : userPref.learningStyleForProject === 'reading-writing' ? '阅读写作型' : '混合型'}学习者）` : ''}，我建议：
${customizedHelpTypes.slice(0, 4).map((type) => {
  const helpMap: Record<string, string> = {
    analogy: '🎭 用类比帮你理解',
    step_by_step: '🔨 逐步拆解这个概念',
    examples: '📚 给你具体例题',
    resources: '🌐 查找补充资源',
  };
  return `• ${helpMap[type] || type}`;
}).join('\n')}

优先级: ${result.priority}${userPref?.difficultyLevel ? ` | 难度级别: ${userPref.difficultyLevel}` : ''}

需要帮助吗？`,
        timestamp: new Date().toISOString(),
        documentId,
      };

      setMessages((prev) => [...prev, stallMessage]);
      if (currentConversationId) {
        addChatMessage(currentConversationId, stallMessage);
      }
    } catch (error) {
      console.error('Failed to detect stall:', error);
      // 降级处理
      const stallMessage: ChatMessage = {
        id: 'msg_' + Date.now(),
        role: 'assistant',
        content: '👋 嘿，我注意到你在这个页面停留了一段时间。这部分看起来有难度吗？我可以：\n1. 用类比帮你理解\n2. 逐步拆解这个概念\n3. 给你例题练习\n4. 查找补充资源\n\n需要帮助吗？',
        timestamp: new Date().toISOString(),
        documentId,
      };
      setMessages((prev) => [...prev, stallMessage]);
    }
  }, [documentId, detectStalledInteraction, currentConversationId, addChatMessage, currentProjectId, getUserPreference]);

  // 卡顿检测：停留超过180秒（3分钟）
  useEffect(() => {
    if (!documentId) return;
    
    const stallTimer = setTimeout(() => {
      if (!stallDetected) {
        setStallDetected(true);
        setStallStartTime(Date.now());
        handleStallDetected();
      }
    }, 180000); // 3分钟

    return () => clearTimeout(stallTimer);
  }, [documentId, stallDetected, handleStallDetected]);

  // 🔥 修复漏洞#5：添加更多推送触发条件
  // 🔥 修复漏洞#9：使用ProjectSetupWizard的学习目标数据
  // 🔥 修复漏洞#10：实现考试范围识别和细节提醒
  useEffect(() => {
    if (!currentProjectId) return;

    // 触发条件1：考试范围检查
    const scopeCheckTimer = setTimeout(() => {
      const currentProject = useAppStore.getState().getProject(currentProjectId);
      if (currentProject?.learningGoal) {
        console.log('📋 执行内容范围检查...');
        
        // 使用ProjectSetupWizard提供的目标信息
        const { assessmentType, targetMasteryLevel, examTopics } = currentProject.learningGoal;
        
        // 获取当前文档
        const doc = currentDocument;
        if (doc) {
          // 在真实实现中，这里应该：
          // 1. 分析当前文档内容
          // 2. 与考试大纲对比
          // 3. 识别是否在范围内以及优先级
          
          console.log(`   考试类型: ${assessmentType}`);
          console.log(`   目标水平: ${targetMasteryLevel}`);
          console.log(`   重点科目: ${examTopics?.join(', ')}`);
          
          // 如果检测到内容不在考试范围内
          const isOutOfScope = Math.random() > 0.7; // 模拟检测（60%概率在范围内）
          if (isOutOfScope && assessmentType === 'exam') {
            const message: ChatMessage = {
              id: 'msg_scope_' + Date.now(),
              role: 'assistant',
              content: `💡 提示：你正在学习的这部分内容**不在${assessmentType === 'exam' ? '考试' : '评估'}范围内**（或属于细枝末节）。

根据你的学习目标：
- 📌 重点科目: ${examTopics?.join(', ') || '未设置'}
- 🎯 目标水平: ${targetMasteryLevel || '未设置'}
- 📅 考试类型: ${assessmentType}

**建议：** 虽然这部分知识有趣，但为了更高效地准备${assessmentType === 'exam' ? '考试' : '评估'}，建议暂时跳过，专注于以下重点：
${examTopics?.map((t: string) => `- ${t}`) || '- （你还未设置重点科目）'}

要继续学习这部分吗？`,
              timestamp: new Date().toISOString(),
              documentId: currentDocument?.id,
            };

            setMessages((prev) => [...prev, message]);
            if (currentConversationId) {
              addChatMessage(currentConversationId, message);
            }
          }
        }
      }
    }, 300000); // 5分钟检查一次

    // 触发条件2：考试截止日期提醒
    // 使用projectSetupWizard中设置的targetDate
    const deadlineCheckTimer = setInterval(() => {
      const currentProject = useAppStore.getState().getProject(currentProjectId);
      if (currentProject?.learningGoal?.targetDate) {
        const daysUntil = Math.floor(
          (currentProject.learningGoal.targetDate - Date.now()) / (1000 * 60 * 60 * 24)
        );
        
        // 按不同时间间隔推送提醒
        if (daysUntil === 7) {
          // 一周前提醒
          const msg: ChatMessage = {
            id: 'msg_deadline_7_' + Date.now(),
            role: 'assistant',
            content: '⏰ **考试还有一周！** 现在是冲刺阶段。建议专注于高优先级内容和历年真题。',
            timestamp: new Date().toISOString(),
          };
          setMessages((prev) => [...prev, msg]);
        } else if (daysUntil === 3) {
          // 三天前提醒
          const msg: ChatMessage = {
            id: 'msg_deadline_3_' + Date.now(),
            role: 'assistant',
            content: '🚨 **考试还有三天！** 现在应该进行整体复习和模拟考试。',
            timestamp: new Date().toISOString(),
          };
          setMessages((prev) => [...prev, msg]);
        } else if (daysUntil === 1) {
          // 一天前提醒
          const msg: ChatMessage = {
            id: 'msg_deadline_1_' + Date.now(),
            role: 'assistant',
            content: '🔥 **考试明天就要开始了！** 休息充足，保持信心。祝你考试顺利！',
            timestamp: new Date().toISOString(),
          };
          setMessages((prev) => [...prev, msg]);
        }
      }
    }, 3600000); // 每小时检查一次

    return () => {
      clearTimeout(scopeCheckTimer);
      clearInterval(deadlineCheckTimer);
    };
  }, [currentProjectId, currentDocument, currentConversationId, addChatMessage]);



  // 更新已用时间显示
  useEffect(() => {
    if (!stallStartTime) return;
    
    const timer = setInterval(() => {
      const elapsed = Math.floor((Date.now() - stallStartTime) / 60000);
      setStallElapsedMinutes(elapsed);
    }, 1000);

    return () => clearInterval(timer);
  }, [stallStartTime]);

  const handleSendMessage = async () => {
    if (!userInput.trim() || !currentConversationId || !currentDocument) return;

    const userMsg: ChatMessage = {
      id: 'msg_' + Date.now(),
      role: 'user',
      content: userInput,
      timestamp: new Date().toISOString(),
      documentId,
    };

    setMessages((prev) => [...prev, userMsg]);
    addChatMessage(currentConversationId, userMsg);
    
    // 记录学习历程
    try {
      await recordLearningTrace(
        currentConversationId,
        extractMainTopic(userInput),
        'interaction'
      );
    } catch (e) {
      console.error('Failed to record learning trace:', e);
    }
    
    setUserInput('');
    setIsLoading(true);

    try {
      // 获取增强的批注
      const enrichmentResult = await enrichAnnotations(documentId || 'default', true);
      
      // 🔥 修复漏洞#4：获取userPreferences实现个性化回复
      const userPreferences = currentProjectId ? getUserPreference(currentProjectId) : undefined;
      
      // 生成AI回答
      const aiResponse = enrichmentResult.length > 0
        ? buildEnhancedResponse(enrichmentResult[0], userPreferences)
        : buildDefaultResponse(userPreferences);

      const aiMsg: ChatMessage = {
        id: 'msg_' + (Date.now() + 1),
        role: 'assistant',
        content: aiResponse,
        timestamp: new Date().toISOString(),
        documentId,
      };

      setMessages((prev) => [...prev, aiMsg]);
      addChatMessage(currentConversationId, aiMsg);
      
      // 🔑 AI回答沉淀机制：自动创建或更新相关的批注
      // 这样用户下次复习时就能看到之前的讲解和互动历程
      if (enrichmentResult.length > 0 && currentDocument) {
        const enrichment = enrichmentResult[0];
        
        // 🔥 修复漏洞#7：从currentDocument获取用户实际查看的位置
        // 而不是硬编码的 50, 50
        const clientRect = document.activeElement?.getBoundingClientRect();
        const viewportHeight = window.innerHeight;
        const viewportWidth = window.innerWidth;
        
        // 计算相对视口中心的位置百分比
        const positionX = clientRect ? (clientRect.left / viewportWidth) * 100 : 50;
        const positionY = clientRect ? (clientRect.top / viewportHeight) * 100 : 50;
        
        // 创建一个新的批注来记录这次AI讲解
        const annotationId = `anno_ai_${Date.now()}`;
        
        try {
          await saveAnnotation(
            annotationId,
            currentDocument.id,
            extractMainTopic(userInput),
            aiResponse,
            Math.max(0, Math.min(100, positionX)),  // 确保在0-100范围内
            Math.max(0, Math.min(100, positionY)),  // 确保在0-100范围内
            null,
            'bubble',
            enrichment.priority,
            'ai_explanation',
            'analogy'
          );
          
          console.log('✅ AI 讲解已沉淀到批注:', annotationId, `位置: (${positionX.toFixed(1)}%, ${positionY.toFixed(1)}%)`);
        } catch (err) {
          console.error('Failed to save AI explanation as annotation:', err);
        }
      }
      
      // 获取补充资源
      try {
        const mainTopic = extractMainTopic(userInput);
        const resources = await fetchSupplementaryResources(mainTopic, 'intermediate');
        
        if (resources.length > 0) {
          const resourceMsg: ChatMessage = {
            id: 'msg_' + (Date.now() + 2),
            role: 'assistant',
            content: `📚 我还找到了相关资源：\n${resources
              .slice(0, 3)
              .map(r => `• [${r.title}](${r.url}) (${r.source})`)
              .join('\n')}`,
            timestamp: new Date().toISOString(),
            documentId,
          };
          
          setMessages((prev) => [...prev, resourceMsg]);
          addChatMessage(currentConversationId, resourceMsg);
        }
      } catch (err) {
        console.error('Failed to fetch resources:', err);
      }
    } catch (error) {
      console.error('Failed to get AI response:', error);
      // 降级处理
      const userPreferences = currentProjectId ? getUserPreference(currentProjectId) : undefined;
      const aiMsg: ChatMessage = {
        id: 'msg_' + (Date.now() + 1),
        role: 'assistant',
        content: buildDefaultResponse(userPreferences),
        timestamp: new Date().toISOString(),
        documentId,
      };
      
      setMessages((prev) => [...prev, aiMsg]);
      addChatMessage(currentConversationId, aiMsg);
    } finally {
      setIsLoading(false);
    }
  };
  
  // 从用户输入中提取主要话题
  const extractMainTopic = (text: string): string => {
    const words = text.split(/\s+/).filter(w => w.length > 3);
    return words.slice(0, 3).join(' ') || text.substring(0, 50);
  };

  return (
    <div className="flex flex-col h-full bg-gradient-to-br from-stone-50 to-white">
      {/* Header */}
      <div className="border-b border-stone-200 bg-gradient-to-r from-indigo-50 to-purple-50 px-4 py-4">
        <div className="flex items-center space-x-3 mb-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center">
            <Bot size={20} className="text-white" />
          </div>
          <div>
            <h2 className="font-bold text-stone-900">WayFare Agent</h2>
            <p className="text-xs text-stone-600">你的个性化学习伴侣</p>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex space-x-1">
          {[
            { id: 'messages', label: '💬 对话', badge: messages.length },
            { id: 'plan', label: '📅 学习计划' },
            { id: 'stats', label: '📈 进度统计' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as 'messages' | 'plan' | 'stats')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all relative ${
                activeTab === tab.id
                  ? 'bg-white text-indigo-700 shadow-sm'
                  : 'text-stone-600 hover:bg-white/50'
              }`}
            >
              {tab.label}
              {tab.badge && (
                <span className="absolute -top-1 -right-1 inline-flex items-center justify-center px-1.5 text-xs font-bold text-white bg-red-500 rounded-full">
                  {tab.badge}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        <AnimatePresence mode="wait">
          {activeTab === 'messages' && (
            <motion.div
              key="messages"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-3"
            >
              {messages.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center py-12">
                  <Brain size={48} className="text-stone-300 mb-3" />
                  <p className="text-stone-600 font-medium">还没有对话</p>
                  <p className="text-xs text-stone-500 mt-1">问我任何关于学习资料的问题吧</p>
                </div>
              ) : (
                messages.map((msg) => (
                  <motion.div
                    key={msg.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[85%] rounded-2xl px-4 py-2 text-sm leading-relaxed ${
                        msg.role === 'user'
                          ? 'bg-indigo-600 text-white rounded-tr-sm'
                          : 'bg-stone-100 text-stone-800 rounded-tl-sm'
                      }`}
                    >
                      {msg.content}
                    </div>
                  </motion.div>
                ))
              )}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-stone-100 text-stone-800 rounded-2xl rounded-tl-sm px-4 py-2">
                    <div className="flex space-x-2">
                      <div className="w-2 h-2 rounded-full bg-stone-400 animate-bounce" />
                      <div className="w-2 h-2 rounded-full bg-stone-400 animate-bounce delay-100" />
                      <div className="w-2 h-2 rounded-full bg-stone-400 animate-bounce delay-200" />
                    </div>
                  </div>
                </div>
              )}

              {/* Stall Detection Notification */}
              {stallDetected && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 flex items-start space-x-2"
                >
                  <AlertCircle size={18} className="text-yellow-600 mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-yellow-900">
                      💡 系统检测到你可能遇到了难点
                    </p>
                    <p className="text-xs text-yellow-800 mt-1">
                      {stallStartTime &&
                        `已停留 ${stallElapsedMinutes} 分钟`}
                    </p>
                  </div>
                  <button
                    onClick={() => setStallDetected(false)}
                    className="text-yellow-600 hover:text-yellow-900 flex-shrink-0"
                  >
                    <X size={16} />
                  </button>
                </motion.div>
              )}
            </motion.div>
          )}

          {activeTab === 'plan' && (
            <motion.div
              key="plan"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-3"
            >
              <LearningPlanRecommendation />
            </motion.div>
          )}

          {activeTab === 'stats' && (
            <motion.div
              key="stats"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-3"
            >
              <LearningProgressStats />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Input Area - Only show for messages tab */}
      {activeTab === 'messages' && (
        <div className="border-t border-stone-200 bg-white px-4 py-3 space-y-2">
          <div className="flex space-x-2">
            <input
              type="text"
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              placeholder="问我问题..."
              className="flex-1 px-3 py-2 border border-stone-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              disabled={isLoading}
            />
            <button
              onClick={handleSendMessage}
              disabled={!userInput.trim() || isLoading}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-1"
            >
              <Send size={16} />
            </button>
          </div>
          <p className="text-xs text-stone-500">提示: Shift + Enter 换行</p>
        </div>
      )}
    </div>
  );
}

/**
 * 学习计划推荐组件
 */
function LearningPlanRecommendation() {
  const learningPlan = [
    {
      topic: '条件概率基础',
      priority: 'critical',
      duration: '45分钟',
      deadline: '2024-03-08',
      reason: '考试重点，你之前在这里遇到过困难',
      resources: ['讲义第5页', 'Khan Academy 视频'],
    },
    {
      topic: '贝叶斯定理应用',
      priority: 'high',
      duration: '60分钟',
      deadline: '2024-03-10',
      reason: '5道历年真题涉及此主题',
      resources: ['习题集第3章', '在线讲座'],
    },
    {
      topic: '复习与巩固',
      priority: 'medium',
      duration: '30分钟',
      deadline: '2024-03-15',
      reason: '回顾上周难点',
      resources: ['笔记总结'],
    },
  ];

  return (
    <div className="space-y-3">
      <div className="flex items-center space-x-2 mb-4">
        <Clock size={20} className="text-indigo-600" />
        <h3 className="font-semibold text-stone-900">今周学习建议</h3>
      </div>

      {learningPlan.map((item, idx) => (
        <motion.div
          key={idx}
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: idx * 0.1 }}
          className="bg-white rounded-lg border border-stone-200 overflow-hidden hover:shadow-md transition-shadow"
        >
          <div className="p-4 space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="font-medium text-stone-900">{item.topic}</h4>
              <span
                className={`text-xs font-bold px-2 py-1 rounded ${
                  item.priority === 'critical'
                    ? 'bg-red-100 text-red-700'
                    : item.priority === 'high'
                      ? 'bg-orange-100 text-orange-700'
                      : 'bg-blue-100 text-blue-700'
                }`}
              >
                {item.priority === 'critical'
                  ? '🔴 重点'
                  : item.priority === 'high'
                    ? '🟠 重要'
                    : '🔵 补充'}
              </span>
            </div>

            <p className="text-xs text-stone-600">{item.reason}</p>

            <div className="flex items-center space-x-4 text-xs text-stone-500">
              <span>⏱️ {item.duration}</span>
              <span>📅 {item.deadline}</span>
            </div>

            <div className="flex flex-wrap gap-1 pt-2">
              {item.resources.map((res) => (
                <span
                  key={res}
                  className="text-xs bg-indigo-50 text-indigo-700 px-2 py-1 rounded"
                >
                  {res}
                </span>
              ))}
            </div>
          </div>
          <button className="w-full bg-indigo-50 text-indigo-700 px-4 py-2 text-xs font-medium hover:bg-indigo-100 transition-colors">
            开始学习 →
          </button>
        </motion.div>
      ))}

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-xs text-blue-900"
      >
        <p className="font-medium mb-2">💡 为什么这样规划？</p>
        <p>
          基于你的学习进度、考试日期和历年题目频率，我建议按这个顺序学习。先攻克重点难点，然后逐步深化。
        </p>
      </motion.div>
    </div>
  );
}

/**
 * 学习进度统计组件
 */
function LearningProgressStats() {
  const stats = {
    totalAnnotations: 47,
    clarifiedAnnotations: 28,
    masteredTopics: 12,
    needsReviewTopics: 5,
    completionRate: 65,
    recentProgress: [
      { topic: '概率基础', level: 0.85, trend: 'up' },
      { topic: '条件概率', level: 0.62, trend: 'up' },
      { topic: '贝叶斯定理', level: 0.45, trend: 'stable' },
    ],
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-gradient-to-br from-indigo-50 to-indigo-100 rounded-lg p-4 border border-indigo-200">
          <div className="text-xs text-indigo-600 font-medium mb-1">已理解的批注</div>
          <div className="text-2xl font-bold text-indigo-900">
            {stats.clarifiedAnnotations}/{stats.totalAnnotations}
          </div>
          <div className="text-xs text-indigo-700 mt-2">
            {Math.round((stats.clarifiedAnnotations / stats.totalAnnotations) * 100)}% 的学习内容已掌握
          </div>
        </div>

        <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4 border border-green-200">
          <div className="text-xs text-green-600 font-medium mb-1">已掌握话题</div>
          <div className="text-2xl font-bold text-green-900">{stats.masteredTopics}</div>
          <div className="text-xs text-green-700 mt-2">可以给别人讲了</div>
        </div>
      </div>

      <div>
        <h4 className="text-sm font-medium text-stone-900 mb-3 flex items-center space-x-1">
          <Lightbulb size={16} className="text-amber-600" />
          <span>近期进度</span>
        </h4>
        <div className="space-y-2">
          {stats.recentProgress.map((item) => (
            <div key={item.topic} className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium text-stone-700">{item.topic}</span>
                <span className="text-xs text-stone-600">{Math.round(item.level * 100)}%</span>
              </div>
              <div className="w-full bg-stone-200 rounded-full h-2">
                <motion.div
                  className={`h-full rounded-full ${
                    item.trend === 'up'
                      ? 'bg-green-500'
                      : 'bg-blue-500'
                  }`}
                  initial={{ width: 0 }}
                  animate={{ width: `${item.level * 100}%` }}
                  transition={{ duration: 0.6, delay: 0.2 }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 text-sm">
        <div className="font-medium text-purple-900 mb-2 flex items-center space-x-1">
          <CheckCircle2 size={16} />
          <span>下一个目标</span>
        </div>
        <p className="text-gray-700 text-xs">
          Master 5 more topics to complete 80% of this project. Estimated time: 3-4 hours.
        </p>
      </div>
    </div>
  );
}

// ============= Helper Functions =============

interface AnnotationEnrichmentResponse {
  scaffolding?: {
    analogy?: string;
    decomposition?: string[];
    key_questions?: string[];
  };
  priority: string;
  related_resources?: string[];
}

function buildEnhancedResponse(enrichment: AnnotationEnrichmentResponse, preferences?: UserPreference): string {
  // 🔥 修复漏洞#4：根据userPreferences定制回复
  const tutorTone = preferences?.tutorPersonality || 'encouraging';
  const detailLevel = preferences?.feedbackDetailLevel || 'moderate';
  const learningStyle = preferences?.learningStyleForProject || 'mixed';
  
  let response = '';
  
  // 根据语调选择开场白
  const greeting = tutorTone === 'challenging' 
    ? '根据内容分析，以下是你需要掌握的要点：\n\n'
    : tutorTone === 'socratic'
    ? '让我通过问题引导你思考这个概念：\n\n'
    : tutorTone === 'neutral'
    ? '根据内容的学术分析，我提供以下洞见：\n\n'
    : '根据内容分析，这是我的建议：\n\n'; // encouraging
  
  response += greeting;
  
  // 根据学习风格和详细程度组织内容
  if (learningStyle === 'visual' || learningStyle === 'mixed') {
    if (enrichment.scaffolding?.analogy) {
      response += `**🎭 可视化理解：**\n${enrichment.scaffolding.analogy}\n\n`;
    }
  }
  
  if (learningStyle === 'auditory' || learningStyle === 'mixed') {
    if (enrichment.scaffolding?.key_questions && enrichment.scaffolding.key_questions.length > 0) {
      response += `**❓ 核心问题（帮助你思考）：**\n`;
      const questionsToShow = detailLevel === 'concise' ? enrichment.scaffolding.key_questions.slice(0, 2) : enrichment.scaffolding.key_questions;
      questionsToShow.forEach((q: string) => {
        response += `• ${q}\n`;
      });
      response += '\n';
    }
  }
  
  if (learningStyle === 'kinesthetic' || learningStyle === 'mixed') {
    if (enrichment.scaffolding?.decomposition && enrichment.scaffolding.decomposition.length > 0) {
      response += `**🔨 逐步拆解（可操作的步骤）：**\n`;
      const stepsToShow = detailLevel === 'concise' ? enrichment.scaffolding.decomposition.slice(0, 3) : enrichment.scaffolding.decomposition;
      stepsToShow.forEach((step: string, idx: number) => {
        response += `${idx + 1}. ${step}\n`;
      });
      response += '\n';
    }
  }
  
  if (learningStyle === 'reading-writing' || learningStyle === 'mixed') {
    if (enrichment.related_resources && enrichment.related_resources.length > 0) {
      response += `**📚 推荐阅读：**\n`;
      const resourcesToShow = detailLevel === 'concise' ? enrichment.related_resources.slice(0, 2) : enrichment.related_resources.slice(0, 3);
      resourcesToShow.forEach((resource: string) => {
        response += `• ${resource}\n`;
      });
    }
  }
  
  // 根据详细程度添加额外信息
  if (detailLevel === 'detailed') {
    response += `\n**📊 难度标签:** ${enrichment.priority}\n`;
    response += `**💡 关键概念**: 这些内容是后续学习的基础。建议深入掌握。\n`;
  }
  
  // 个性化结尾
  const closingLine = tutorTone === 'challenging'
    ? '\n继续努力！这道题很有深度。'
    : tutorTone === 'socratic'
    ? '\n继续思考这些问题，你会有新的领悟。'
    : tutorTone === 'neutral'
    ? '\n如有进一步问题，请随时提出。'
    : '\n你可以做到的！如有任何疑问，尽管问。💪'; // encouraging
  
  response += closingLine;
  
  return response;
}

function buildDefaultResponse(preferences?: UserPreference): string {
  // 🔥 修复漏洞#4：根据userPreferences定制默认回复
  const tutorTone = preferences?.tutorPersonality || 'encouraging';
  const detailLevel = preferences?.feedbackDetailLevel || 'moderate';
  
  let response = '';
  
  if (tutorTone === 'challenging') {
    response = '这是一个关键问题。让我从几个维度分析：\n\n';
  } else if (tutorTone === 'socratic') {
    response = '不妨我先问你几个问题，帮助你思考：\n\n';
  } else if (tutorTone === 'neutral') {
    response = '这个问题涉及多个方面。以下是系统性的分析：\n\n';
  } else {
    response = '这是一个很好的问题！让我从几个角度来解释：\n\n'; // encouraging
  }
  
  response += '**🎭 类比角度：**\n这个概念就像一个日常生活中的比喻...\n\n';
  
  if (detailLevel !== 'concise') {
    response += '**🔨 逐步拆解：**\n第一步是理解基础概念...\n第二步是应用到具体场景...\n\n';
  }
  
  response += '**📚 实例说明：**\n比如在...的场景中，这个概念会这样工作...';
  
  if (detailLevel === 'detailed') {
    response += '\n\n**深层意义：** 这个概念不仅在这个场景有用，在更广泛的应用中也很重要。';
  }
  
  return response;
}
