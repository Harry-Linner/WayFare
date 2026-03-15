import { demoAnnotatedPaper } from './demoAnnotatedPaper';
import type { DemoScenario } from '../types/sharedtypes';

export const demoScenarios: Record<string, DemoScenario> = {
  'retrieval-practice': {
    id: 'retrieval-practice',
    triggerFiles: ['为什么检索练习能显著提升学习效果.md'],
    detectedTitle: '检测到可分析学习资料',
    detectedDescription:
      '当前文件夹中包含《为什么检索练习能显著提升学习效果》。你希望 WayFare 如何处理这份资料？',
    options: [
      {
        id: 'layered-annotation',
        label: '生成分层批注（推荐）',
        description: '适合深度理解论文、教材与读书材料',
        processingMode: 'layered-annotation',
        processingLabel: '已生成分层批注'
      },
      {
        id: 'study-brief',
        label: '提炼汇报与复习重点',
        description: '自动提取核心观点、证据与可复述表达',
        processingMode: 'study-brief',
        processingLabel: '已提炼汇报与复习重点'
      },
      {
        id: 'raw-only',
        label: '仅导入原文件，不做处理',
        description: '只保存原始资料到知识库中',
        processingMode: 'raw-only',
        processingLabel: '仅导入原文件'
      },
      {
        id: 'custom',
        label: '其他（自定义）',
        description: '输入你希望 WayFare 对这份资料执行的处理方式',
        processingMode: 'custom',
        processingLabel: '自定义处理方式'
      }
    ],
    processingSteps: [
      '解析文档结构',
      '识别核心观点与概念',
      '生成分层批注',
      '建立可对话知识索引'
    ],
    annotatedDocument: demoAnnotatedPaper,
    assistant: {
      initialMessages: [
        {
          id: 'retrieval-init-1',
          role: 'assistant',
          content:
            '我已经预处理完这篇关于“检索练习提升学习效果”的文章。你现在可以直接问我：作者的核心观点、18% 的实验结果、文章的限制条件，或者如何把它讲成一段 3 分钟读书报告。'
        }
      ],
      quickActions: ['生成 3 分钟读书报告', '总结论文结构', '解释 18% 实验结果'],
      rules: [
        {
          id: 'report-3min',
          keywords: ['3 分钟', '读书报告', '怎么讲', '汇报'],
          thinkingSteps: ['检索核心观点', '提取实验结果', '组织读书报告结构'],
          streamChunks: [
            '如果你要把这篇文章讲成 3 分钟读书报告，可以先从问题切入：很多学生花了很多时间复习，却依然很难在考试或延迟测试中稳定回忆知识。 ',
            '接着说明作者的核心观点：比起单纯重复阅读，主动进行检索练习更能促进长期记忆保持。 ',
            '第三步讲证据。文章用课堂实验说明，进行两轮自测的学生在一周后的延迟测试中平均高出 18%，这是最关键的实证支撑。 ',
            '最后补上限制与总结：检索练习并不是无条件有效，它需要和理解、反馈以及合理难度结合。你可以按“问题—观点—证据—限制”这四步完成整段汇报。'
          ]
        },
        {
          id: 'paper-structure',
          keywords: ['结构', '逻辑', '总结'],
          thinkingSteps: ['回溯论证链条', '定位结构节点', '压缩为易讲述版本'],
          streamChunks: [
            '这篇文章的结构可以概括为：先提出学习困境，说明学生常常误以为自己已经学会；',
            '再提出核心论点——主动检索优于被动重复；',
            '随后给出概念界定和机制解释，再用实验中“高出 18%”的数据支撑；',
            '最后补充限制与应用建议。整体是非常清晰的“问题—论点—证据—限制—建议”结构。'
          ]
        },
        {
          id: 'evidence-18',
          keywords: ['18%', '实验', '证据', '数据'],
          thinkingSteps: ['定位实验段落', '提取关键数字', '生成解释'],
          streamChunks: [
            '18% 这个数字是文章中最醒目的证据。 ',
            '它说明进行两轮自测的学生，在一周后的延迟测试中平均比重复阅读组高出 18%。 ',
            '这个结果的重要性不只是“成绩更高”，而是说明主动提取更有助于长期保持和稳定回忆。'
          ]
        }
      ],
      defaultThinkingSteps: ['检索知识片段', '组织回答结构', '生成学习表达'],
      defaultStreamChunks: [
        '我已经基于这篇文章的批注内容完成了检索。 ',
        '如果你愿意，我们可以继续从核心观点、实验结果、限制条件，或者读书报告表达这几个方向继续展开。'
      ]
    }
  }
};

export function getDemoScenarioByFileNames(fileNames: string[]) {
  return Object.values(demoScenarios).find((scenario) =>
    scenario.triggerFiles.every((targetFile) => fileNames.includes(targetFile))
  );
}

export function getDemoScenarioById(scenarioId?: string | null) {
  if (!scenarioId) return null;
  return demoScenarios[scenarioId] ?? null;
}
