import type { RenderReadyAnnotationDocument } from '../types/sharedtypes';

export const demoAnnotatedPaper: RenderReadyAnnotationDocument = {
  schemaVersion: '1.0.0',
  meta: {
    documentId: 'paper-001',
    title: '为什么检索练习能显著提升学习效果',
    course: '教育心理学',
    week: '第 6 周',
    mode: 'paper_analysis',
    userGoal: '为这篇论文生成一个分层批注，让我更好理解'
  },
  legend: [
    { key: 'yellow', label: '核心观点', color: '#F4D35E' },
    { key: 'red', label: '关键概念', color: '#E76F51' },
    { key: 'blue', label: '证据/例子', color: '#5DADE2' },
    { key: 'green', label: '注意点/限制', color: '#6BBF59' },
    { key: 'purple', label: '方法/结构', color: '#9B59B6' }
  ],
  sections: [
    {
      id: 'sec-1',
      title: '一、问题提出',
      paragraphs: [
        {
          id: 'p-1',
          text: '许多大学生在复习时投入了大量时间反复阅读教材和笔记，但一到延迟测验或考试情境中，仍然很难稳定回忆出关键知识。作者指出，这种“看起来熟悉”并不等于真正掌握，学习者往往高估了自己对材料的记忆程度。',
          highlights: [
            {
              id: 'h-1',
              text: '“看起来熟悉”并不等于真正掌握',
              colorGroup: 'yellow',
              semanticType: 'main_point'
            },
            {
              id: 'h-2',
              text: '高估了自己对材料的记忆程度',
              colorGroup: 'green',
              semanticType: 'caution'
            }
          ],
          sidebarNote: {
            title: '提出学习困境',
            paragraphFunction: '引出问题',
            logicRole: '全文讨论的起点',
            layer1: '作者先点出一个大学生非常常见的问题：复习了很多，但真正考试时提不出来。',
            layer2: '这段的作用不是给答案，而是先告诉读者“为什么这个主题值得研究”。',
            layer3: '做展示时，这类“痛点句”特别能体现产品是在解决真实学习问题。',
            worthNoticing: '作者先从学习者的主观错觉切入，容易引发共鸣。',
            possibleWeakness: '这一段更像经验观察，本身还没有给出证据。'
          }
        },
        {
          id: 'p-2',
          text: '在此基础上，作者提出本文的核心主张：比起被动重复阅读，主动进行检索练习更能促进长期记忆保持。也就是说，真正有助于学习的，并不是“再看一遍”，而是努力把知识从记忆中提取出来。',
          highlights: [
            {
              id: 'h-3',
              text: '主动进行检索练习更能促进长期记忆保持',
              colorGroup: 'yellow',
              semanticType: 'thesis'
            },
            {
              id: 'h-4',
              text: '把知识从记忆中提取出来',
              colorGroup: 'red',
              semanticType: 'concept'
            }
          ],
          sidebarNote: {
            title: '给出核心论点',
            paragraphFunction: '提出核心主张',
            logicRole: '后续所有证据都围绕这一主张展开',
            layer1: '这一段就是整篇文章最重要的一句话：主动提取比被动重复更有效。',
            layer2: '作者完成了从“问题提出”到“中心论点”的推进，后文只需要不断证明它。',
            layer3: '如果你做读书报告，这句话几乎可以直接拿去写“作者核心观点”。',
            worthNoticing: '作者用对比句式增强了记忆点，读者很容易抓住差异。',
            possibleWeakness: '如果后文证据不足，这个论断会显得过强。'
          }
        }
      ]
    },
    {
      id: 'sec-2',
      title: '二、关键概念与机制',
      paragraphs: [
        {
          id: 'p-3',
          text: '文中将检索练习界定为一种主动从记忆中提取信息的学习活动，例如自测、默写、闭卷回忆提纲或对着白纸复述概念。作者强调，检索练习并不只是检测记忆状态，它本身就会强化记忆痕迹。',
          highlights: [
            {
              id: 'h-5',
              text: '主动从记忆中提取信息的学习活动',
              colorGroup: 'red',
              semanticType: 'definition'
            },
            {
              id: 'h-6',
              text: '它本身就会强化记忆痕迹',
              colorGroup: 'purple',
              semanticType: 'framework'
            }
          ],
          sidebarNote: {
            title: '界定概念并解释机制',
            paragraphFunction: '定义术语 + 说明原理',
            logicRole: '为后文的实验和建议提供概念基础',
            layer1: '作者先解释“检索练习”到底是什么，再说明它为什么有效。',
            layer2: '这段把论文从简单观点推进到更有说服力的机制说明。',
            layer3: '大学生读论文时，先抓定义，再抓原理，会比直接记结论更稳。',
            worthNoticing: '作者同时给定义和例子，降低了概念门槛。',
            possibleWeakness: '机制解释仍是概括性的，细节还需要更多研究支持。'
          }
        }
      ]
    },
    {
      id: 'sec-3',
      title: '三、证据与限制',
      paragraphs: [
        {
          id: 'p-4',
          text: '为了支持这一论点，作者报告了一项课堂实验：A 组学生在学习后进行两轮自测，B 组学生则用同样时间反复阅读材料。一周后的延迟测试显示，A 组的正确率平均高出 18%，并且在开放性问答中表现更稳定。',
          highlights: [
            {
              id: 'h-7',
              text: 'A 组的正确率平均高出 18%',
              colorGroup: 'blue',
              semanticType: 'data'
            },
            {
              id: 'h-8',
              text: '开放性问答中表现更稳定',
              colorGroup: 'blue',
              semanticType: 'evidence'
            }
          ],
          sidebarNote: {
            title: '提供实证证据',
            paragraphFunction: '用实验结果支持核心主张',
            logicRole: '论点之后的关键支撑环节',
            layer1: '这段的作用很直接：告诉你作者不是只在讲道理，而是有实验支持。',
            layer2: '从结构上说，这一段承担的是“论点 → 证据”的核心过渡。',
            layer3: '视频展示时，数字型高亮最能让观众觉得这个批注“专业、有依据”。',
            worthNoticing: '具体数字和实验分组让论证说服力明显增强。',
            possibleWeakness: '如果没有样本规模和变量控制说明，证据强度仍然有限。'
          }
        },
        {
          id: 'p-5',
          text: '不过，作者也承认检索练习并不是在任何条件下都自动有效。如果学习者在完全没有理解材料的情况下机械回忆，练习可能只会加深混乱；如果题目设置过难，也可能打击学习动机。',
          highlights: [
            {
              id: 'h-9',
              text: '并不是在任何条件下都自动有效',
              colorGroup: 'green',
              semanticType: 'limitation'
            },
            {
              id: 'h-10',
              text: '机械回忆，练习可能只会加深混乱',
              colorGroup: 'green',
              semanticType: 'counterargument'
            }
          ],
          sidebarNote: {
            title: '补充限制条件',
            paragraphFunction: '承认边界与限制',
            logicRole: '修正前文强主张，让论证更完整',
            layer1: '作者在这里提醒读者：检索练习不是无条件有效的万能方法。',
            layer2: '这一步让文章从“绝对判断”变成“有条件成立的判断”，更像真正的学术论证。',
            layer3: '对教育产品来说，这类“适用条件提醒”很重要，因为它能体现负责任的学习建议。',
            worthNoticing: '主动写限制往往会提升整篇文章的可信度。',
            possibleWeakness: '如果限制展开太少，读者仍然不知道边界在哪里。'
          }
        },
        {
          id: 'p-6',
          text: '因此，作者最后给出的结论并不是“所有复习都应被检索练习替代”，而是应将检索练习视为一种有条件生效的核心学习策略：它需要和初步理解、及时反馈以及合理难度结合。整篇文章的论证链条也因此完整呈现为：问题提出、论点确立、机制解释、实验证据、限制补充、策略建议。',
          highlights: [
            {
              id: 'h-11',
              text: '有条件生效的核心学习策略',
              colorGroup: 'yellow',
              semanticType: 'takeaway'
            },
            {
              id: 'h-12',
              text: '问题提出、论点确立、机制解释、实验证据、限制补充、策略建议',
              colorGroup: 'purple',
              semanticType: 'structure'
            }
          ],
          sidebarNote: {
            title: '总结结论与结构',
            paragraphFunction: '收束全文并总结逻辑骨架',
            logicRole: '帮助读者完成从内容理解到结构理解的提升',
            layer1: '作者最终不是给出极端结论，而是给出一个更成熟、更有边界的学习建议。',
            layer2: '这段同时完成两件事：总结最终立场，以及回顾全文结构。',
            layer3: '如果你要录制产品展示视频，这段最适合体现“AI 不只是解释内容，还能帮学生看清结构”。',
            worthNoticing: '结构总结型批注非常适合大学生的深度阅读场景。',
            possibleWeakness: '如果前文没有读透，结构总结会显得抽象。'
          }
        }
      ]
    }
  ],
  summary: {
    logicChain: ['问题提出', '核心论点', '概念界定', '机制解释', '实验支持', '限制补充', '策略建议'],
    oneSentenceClaim: '检索练习比被动重复阅读更能促进长期学习保持，但它需要与理解、反馈和合适难度结合使用。',
    strongestPoint: '核心主张不只停留在直觉层面，而是同时有概念解释和实验数据支撑。',
    weakestPoint: '对于不同学科、不同学习阶段下的适用边界，展开仍然不够充分。'
  }
};
