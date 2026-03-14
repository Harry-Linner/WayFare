import type { Annotation, ChatMessage } from '../types/sharedtypes';

export const MOCK_ANNOTATIONS: Annotation[] = [
  {
    id: 'ann-001',
    contentId: 'doc-1',
    pageNumber: 1,
    boundingBox: { x: 100, y: 150, width: 200, height: 30 },
    knowledgePoint: 'AVL树平衡因子',
    frequency: 5,
    priority: 'critical', // 应该显示深橙色 #E9A254
    weight: 0.9,
    type: 'concept',
    aiComment: '这是408数据结构的高频考点，务必掌握旋转逻辑。',
    contextQuote: '平衡因子的绝对值不超过1...'
  },
  {
    id: 'ann-002',
    contentId: 'doc-1',
    pageNumber: 1,
    boundingBox: { x: 100, y: 400, width: 150, height: 30 },
    knowledgePoint: '背景补充',
    frequency: 1,
    priority: 'low', // 应该显示灰色
    weight: 0.3,
    type: 'summary',
    aiComment: '这段话只是历史背景，简单了解即可。',
    contextQuote: '1962年由两位苏联数学家提出...'
  }
];

export const MOCK_CHAT: ChatMessage[] = [
  {
    id: 'm1',
    role: 'assistant',
    content: '你好！我是你的学习助手。今天我们要攻克《数据结构》的第三章，准备好了吗？',
    suggestedActions: ['生成学习路线', '开始今日复盘']
  }
];

export const MOCK_CHAT_DASHBOARD: ChatMessage[] = [
  {
    id: 'm1',
    role: 'assistant',
    content: '欢迎来到知识库管理中心！我可以帮你：\n• 分析学习进度和统计\n• 制定个性化学习计划\n• 推荐适合的学习资源\n• 解答学习中的疑问\n有什么我可以帮助你的吗？',
    suggestedActions: ['查看学习建议', '制定学习计划', '分析学习数据']
  }
];