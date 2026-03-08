/// 测试数据生成器
/// 用于本地测试和演示

import { useAppStore } from '../store/appStore';
import type { LearnerProfile, ChatMessage } from '../types';

export interface MockDataConfig {
  userCount: number;
  projectCount: number;
  annotationsPerProject: number;
  conversationLength: number;
}

const defaultConfig: MockDataConfig = {
  userCount: 1,
  projectCount: 2,
  annotationsPerProject: 10,
  conversationLength: 5,
};

/**
 * 生成模拟用户档案
 */
export function generateMockLearnerProfile(): LearnerProfile {
  const now = Date.now();
  return {
    userId: `user_${Math.random().toString(36).substr(2, 9)}`,
    preferredLearningStyle: ['visual', 'auditory', 'kinesthetic', 'reading-writing', 'mixed'][
      Math.floor(Math.random() * 5)
    ] as 'visual' | 'auditory' | 'kinesthetic' | 'reading-writing' | 'mixed',
    preferredPaceLevel: ['slow', 'medium', 'fast'][Math.floor(Math.random() * 3)] as 'slow' | 'medium' | 'fast',
    createdAt: now,
    updatedAt: now,
  };
}

/**
 * 生成模拟项目
 */
export function generateMockProject(index: number) {
  const topics = [
    '概率论基础',
    '线性代数',
    '微积分',
    '机器学习',
    '数据科学',
  ];
  const topic = topics[index % topics.length];

  return {
    projectId: `proj_${Date.now()}_${index}`,
    name: `${topic}学习项目 #${index + 1}`,
    description: `深入学习${topic}的原理和应用`,
    learningGoals: [`理解${topic}的基本概念`, `掌握${topic}的计算方法`, `应用到实际问题`],
    focusAreas: [
      `${topic}定义`,
      `${topic}性质`,
      `${topic}应用`,
    ],
    createdAt: Date.now(),
    updatedAt: Date.now(),
  };
}

/**
 * 生成模拟批注
 */
export function generateMockAnnotations(projectId: string, count: number) {
  const annotations = [];
  const concepts = [
    { cn: '条件概率', en: 'Conditional Probability' },
    { cn: '贝叶斯定理', en: 'Bayes Theorem' },
    { cn: '期望值', en: 'Expected Value' },
    { cn: '方差', en: 'Variance' },
    { cn: '正态分布', en: 'Normal Distribution' },
  ];

  for (let i = 0; i < count; i++) {
    const concept = concepts[i % concepts.length];
    annotations.push({
      annotationId: `anno_${projectId}_${i}`,
      projectId,
      text: `${concept.cn} (${concept.en})`,
      type: ['concept', 'question', 'difficulty', 'important'][i % 4],
      color: ['yellow', 'red', 'green', 'blue'][i % 4],
      createdAt: Date.now() - Math.random() * 86400000, // 随机过去时间
      understanding: Math.random() > 0.5 ? 'understood' : 'confused',
    });
  }

  return annotations;
}

/**
 * 生成模拟对话
 */
export function generateMockConversations(length: number) {
  const conversations = [];
  const messages = [
    '这个概念怎么理解？',
    '能否举个例子？',
    '为什么这样计算？',
    '与之前学的有什么关联？',
    '这在实际中有什么应用？',
  ];

  const responses = [
    '这个概念表示在已知事件B发生的条件下，事件A发生的概率。',
    '例如：已知天下雨，路面湿滑的概率。',
    '这个公式推导出来的原因是...',
    '这与前面学的概率公式紧密相关。',
    '在医学诊断、垃圾邮件过滤等领域广泛应用。',
  ];

  for (let i = 0; i < length; i++) {
    conversations.push({
      id: `msg_user_${i}`,
      role: 'user',
      content: messages[i % messages.length],
      timestamp: new Date(Date.now() - (length - i) * 60000).toISOString(),
    });

    conversations.push({
      id: `msg_assistant_${i}`,
      role: 'assistant',
      content: responses[i % responses.length],
      timestamp: new Date(Date.now() - (length - i) * 60000 + 5000).toISOString(),
    });
  }

  return conversations;
}

/**
 * 生成模拟学习面包屑
 */
export function generateMockBreadcrumbs() {
  const concepts = [
    '条件概率',
    '贝叶斯定理',
    '期望值',
  ];

  return concepts.map((_concept, index) => ({
    conceptId: `concept_${index}`,
    stage: [
      'first_confusion',
      'clarification',
      'deepening',
      'mastery',
      'application',
    ][index % 5],
    timestamp: Date.now() - (5 - index) * 86400000,
    details: {
      clarificationCount: index + 1,
      daysTaken: index + 1,
      annotations: Array.from({ length: index + 1 }, (_, i) => `anno_${i}`),
      migrationSuccess: Math.random() > 0.3,
    },
  }));
}

/**
 * 初始化模拟数据
 */
export function initializeMockData(config: Partial<MockDataConfig> = {}) {
  const finalConfig = { ...defaultConfig, ...config };
  const store = useAppStore.getState();

  console.log('📊 初始化模拟数据...');
  console.log(`   用户数: ${finalConfig.userCount}`);
  console.log(`   项目数: ${finalConfig.projectCount}`);

  // 创建用户档案
  const learnerProfile = generateMockLearnerProfile();
  store.setLearnerProfile(learnerProfile);

  // 创建项目
  for (let i = 0; i < finalConfig.projectCount; i++) {
    const project = generateMockProject(i);
    const userId = learnerProfile.userId;
    const now = Date.now();
    store.addProject({
      id: project.projectId,
      userId,
      name: project.name,
      description: project.description,
      folderPath: `./projects/${project.projectId}`,
      learningGoal: {
        id: `goal_${project.projectId}`,
        projectId: project.projectId,
        userId,
        title: `学习${project.name}`,
        description: project.description || '',
        targetDate: now + 30 * 24 * 60 * 60 * 1000,
        assessmentType: 'exam' as const,
        createdAt: now,
        updatedAt: now,
        status: 'active' as const,
      },
      userPreferences: {
        projectId: project.projectId,
        userId,
        focusAreas: project.focusAreas || [],
        tutorPersonality: 'encouraging',
        feedbackDetailLevel: 'moderate',
        updatedAt: now,
      },
      documents: [],
      createdAt: now,
      updatedAt: now,
      status: 'active' as const,
    });

    // 创建对话
    const conversations = generateMockConversations(finalConfig.conversationLength);
    const convId = `conv_${project.projectId}`;
    store.setCurrentConversation(convId);
    conversations.forEach((msg) => {
      const chatMessage: ChatMessage = {
        id: msg.id,
        role: msg.role as 'user' | 'assistant',
        content: msg.content,
        timestamp: msg.timestamp,
      };
      store.addChatMessage(convId, chatMessage);
    });
  }

  console.log('✅ 模拟数据已初始化');

  return {
    learnerProfile,
    projectCount: finalConfig.projectCount,
  };
}

/**
 * 清空所有模拟数据
 */
export function clearMockData() {
  localStorage.clear();
  sessionStorage.clear();
  console.log('🗑️  所有模拟数据已清空');
}

/**
 * 导出数据为 JSON
 */
export function exportDataAsJSON() {
  const store = useAppStore.getState();

  const data = {
    learnerProfile: store.learnerProfile,
    projects: store.projects,
    annotations: store.annotations,
    conversations: store.conversations,
    breadcrumbs: ('breadcrumbs' in store) ? (store as { breadcrumbs: unknown[] }).breadcrumbs : [],
    exportTime: new Date().toISOString(),
  };

  const json = JSON.stringify(data, null, 2);
  const blob = new Blob([json], { type: 'application/json' });
  const url = URL.createObjectURL(blob);

  const a = document.createElement('a');
  a.href = url;
  a.download = `wayfare-data-${Date.now()}.json`;
  a.click();

  URL.revokeObjectURL(url);
  console.log('📥 数据已导出');
}

/**
 * 从 JSON 导入数据
 */
export async function importDataFromJSON(file: File) {
  try {
    const content = await file.text();
    const data = JSON.parse(content) as Record<string, unknown>;

    const store = useAppStore.getState();

    // 恢复数据
    if (data.learnerProfile && typeof data.learnerProfile === 'object') {
      store.setLearnerProfile({...(data.learnerProfile as Record<string, unknown>), updatedAt: Date.now()} as unknown as LearnerProfile);
    }

    if (Array.isArray(data.projects)) {
      data.projects.forEach((project: unknown) => {
        // Using type assertion since this is imported data
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        store.addProject(project as any);
      });
    }

    if (Array.isArray(data.annotations)) {
      data.annotations.forEach((anno: unknown) => {
        // Using type assertion since this is imported data
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        store.addAnnotation(anno as any);
      });
    }

    console.log('✅ 数据已导入');
  } catch (error) {
    console.error('❌ 导入失败:', error);
    throw error;
  }
}
