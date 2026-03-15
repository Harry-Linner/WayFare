import type { Annotation, ChatMessage } from '../types/sharedtypes';

export const MOCK_ANNOTATIONS: Annotation[] = [
  {
    id: 'ann-001',
    contentId: 'doc-1',
    pageNumber: 1,
    boundingBox: { x: 100, y: 150, width: 200, height: 30 },
    knowledgePoint: 'AVL树平衡因子',
    frequency: 5,
    priority: 'critical',
    weight: 0.9,
    type: 'concept',
    aiComment: '这是数据结构中的高频考点，重点掌握平衡因子和旋转逻辑。',
    contextQuote: '平衡因子的绝对值不超过1...'
  },
  {
    id: 'ann-002',
    contentId: 'doc-1',
    pageNumber: 1,
    boundingBox: { x: 100, y: 400, width: 150, height: 30 },
    knowledgePoint: '背景补充',
    frequency: 1,
    priority: 'low',
    weight: 0.3,
    type: 'summary',
    aiComment: '这段更多是历史背景，理解其来源即可，不必投入过多记忆成本。',
    contextQuote: '1962年由两位苏联数学家提出...'
  }
];

export const MOCK_CHAT: ChatMessage[] = [
  {
    id: 'm1',
    role: 'assistant',
    content: '你好！我是你的学习助手。今天我们一起攻克《数据结构》的 AVL 树内容。你可以让我总结重点、解释概念，或者直接生成练习题。',
    suggestedActions: ['生成学习路线', '开始今日复习']
  }
];

export const MOCK_CHAT_DASHBOARD: ChatMessage[] = [
  {
    id: 'm1',
    role: 'assistant',
    content: '欢迎来到知识库管理中心！我可以帮你分析学习进度、制定学习计划、推荐资料，也能根据你的知识库内容回答问题。你想先看哪一部分？',
    suggestedActions: ['查看学习建议', '制定学习计划', '分析学习数据']
  }
];

export const MOCK_CHAT_PAPER_DEMO: ChatMessage[] = [
  {
    id: 'pm1',
    role: 'assistant',
    content:
      '我已经预处理完这篇关于“检索练习提升学习效果”的论文演示内容。你现在可以直接问我：\n• 作者的核心观点是什么\n• 18% 的实验结果说明了什么\n• 检索练习为什么不等于单纯刷题\n• 这篇文章适合怎么写进读书报告\n\n如果你愿意，我也可以先帮你总结这篇文章的论证结构。',
    suggestedActions: ['总结论文结构', '解释检索练习', '提炼读书报告观点']
  }
];
