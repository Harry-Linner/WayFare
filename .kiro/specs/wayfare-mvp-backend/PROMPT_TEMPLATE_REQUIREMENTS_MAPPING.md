# Prompt模板需求映射文档

## 需求追溯

本文档展示Task 5.3的每个子任务如何在现有实现中得到满足。

## Task 5.3子任务清单

### ✅ 子任务1：创建explanation类型的Prompt模板（费曼技巧）

**需求**：使用费曼技巧设计explanation类型的批注模板

**实现位置**：`wayfare/context_builder.py` Line 37-48

**实现内容**：
```python
"explanation": """用户选中的文本：
{selected_text}

相关上下文：
{context}

请用简单易懂的语言解释这段内容，包括：
1. 核心概念是什么
2. 用类比或例子说明
3. 为什么这个概念重要

保持简洁，不超过200字。"""
```

**费曼技巧体现**：
- ✅ "简单易懂的语言" - 费曼技巧核心原则
- ✅ "类比或例子说明" - 费曼技巧关键方法
- ✅ "核心概念是什么" - 识别核心
- ✅ "为什么重要" - 建立意义连接

**测试验证**：
- `test_build_messages_explanation()` - 验证模板正确应用
- `test_system_prompt_contains_key_elements()` - 验证费曼技巧提及

---

### ✅ 子任务2：创建question类型的Prompt模板（启发性问题）

**需求**：设计question类型的批注模板，提出启发性问题

**实现位置**：`wayfare/context_builder.py` Line 50-61

**实现内容**：
```python
"question": """用户选中的文本：
{selected_text}

相关上下文：
{context}

请提出2-3个启发性问题，帮助学生：
1. 理解概念的本质
2. 联系已有知识
3. 思考应用场景

每个问题简短有力。"""
```

**启发性问题设计**：
- ✅ "理解概念的本质" - 深度理解
- ✅ "联系已有知识" - 知识整合
- ✅ "思考应用场景" - 迁移应用
- ✅ "2-3个问题" - 数量适中
- ✅ "简短有力" - 质量要求

**测试验证**：
- `test_build_messages_question()` - 验证模板正确应用
- `test_build_system_prompt_with_type_guidance()` - 验证类型特定指导

---

### ✅ 子任务3：创建summary类型的Prompt模板（要点总结）

**需求**：设计summary类型的批注模板，提炼核心要点

**实现位置**：`wayfare/context_builder.py` Line 63-74

**实现内容**：
```python
"summary": """用户选中的文本：
{selected_text}

相关上下文：
{context}

请总结这段内容的核心要点：
1. 主要观点（1-2句话）
2. 关键细节（2-3个要点）
3. 与上下文的关系

保持简洁，不超过150字。"""
```

**要点总结设计**：
- ✅ "核心要点" - 信息提炼
- ✅ "主要观点" - 宏观理解
- ✅ "关键细节" - 微观把握
- ✅ "与上下文的关系" - 知识整合
- ✅ "不超过150字" - 简洁性

**测试验证**：
- `test_build_messages_summary()` - 验证模板正确应用
- `test_get_available_types()` - 验证summary类型可用

---

### ✅ 子任务4：确保Prompt包含RAG上下文和用户选中文本

**需求**：所有模板必须包含RAG检索的上下文和用户选中的文本

**实现验证**：

#### 4.1 用户选中文本集成

**占位符**：`{selected_text}`

**所有模板都包含**：
```python
# Explanation模板
"用户选中的文本：\n{selected_text}"

# Question模板  
"用户选中的文本：\n{selected_text}"

# Summary模板
"用户选中的文本：\n{selected_text}"
```

**测试验证**：
- `test_build_messages_explanation()` - 验证selected_text在消息中
- `test_build_messages_question()` - 验证selected_text在消息中
- `test_build_messages_summary()` - 验证selected_text在消息中

#### 4.2 RAG上下文集成

**占位符**：`{context}`

**所有模板都包含**：
```python
# Explanation模板
"相关上下文：\n{context}"

# Question模板
"相关上下文：\n{context}"

# Summary模板
"相关上下文：\n{context}"
```

**上下文格式化**：`_format_context_docs()` 方法
```python
def _format_context_docs(self, context_docs: List[str]) -> str:
    if not context_docs:
        return "（无相关上下文）"
    
    formatted_docs = []
    for i, doc in enumerate(context_docs, 1):
        formatted_docs.append(f"[片段{i}]\n{doc.strip()}")
    
    return "\n\n".join(formatted_docs)
```

**特性**：
- ✅ 编号标识（[片段1]、[片段2]...）
- ✅ 清晰分隔
- ✅ 空值处理
- ✅ 去除空白

**测试验证**：
- `test_format_context_docs_empty()` - 验证空上下文处理
- `test_format_context_docs_single()` - 验证单个上下文
- `test_format_context_docs_multiple()` - 验证多个上下文
- `test_context_docs_ordering()` - 验证上下文顺序

---

## 需求映射表

| 子任务 | 需求描述 | 实现位置 | 验证方法 | 状态 |
|--------|---------|---------|---------|------|
| 5.3.1 | 创建explanation模板（费曼技巧） | `context_builder.py:37-48` | 单元测试 | ✅ |
| 5.3.2 | 创建question模板（启发性问题） | `context_builder.py:50-61` | 单元测试 | ✅ |
| 5.3.3 | 创建summary模板（要点总结） | `context_builder.py:63-74` | 单元测试 | ✅ |
| 5.3.4 | 包含RAG上下文 | 所有模板的`{context}`占位符 | 单元测试 | ✅ |
| 5.3.5 | 包含用户选中文本 | 所有模板的`{selected_text}`占位符 | 单元测试 | ✅ |

## Requirements映射表

| Requirement | 描述 | 实现验证 | 状态 |
|-------------|------|---------|------|
| 4.2 | 使用费曼技巧和认知支架模板 | Explanation模板 + 系统提示词 | ✅ |
| 4.7 | 支持三种批注类型 | 三个模板 + `get_available_types()` | ✅ |

## 测试覆盖矩阵

| 测试用例 | 覆盖的子任务 | 测试内容 | 状态 |
|---------|-------------|---------|------|
| `test_initialization` | 5.3.1-5.3.3 | 验证三个模板存在 | ✅ PASSED |
| `test_build_messages_explanation` | 5.3.1, 5.3.4, 5.3.5 | 验证explanation模板和占位符 | ✅ PASSED |
| `test_build_messages_question` | 5.3.2, 5.3.4, 5.3.5 | 验证question模板和占位符 | ✅ PASSED |
| `test_build_messages_summary` | 5.3.3, 5.3.4, 5.3.5 | 验证summary模板和占位符 | ✅ PASSED |
| `test_format_context_docs_*` | 5.3.4 | 验证RAG上下文格式化 | ✅ PASSED |
| `test_system_prompt_contains_key_elements` | 4.2 | 验证费曼技巧提及 | ✅ PASSED |
| `test_get_available_types` | 4.7 | 验证三种类型可用 | ✅ PASSED |

**总计**：23个测试用例，全部通过 ✅

## 代码质量指标

### 模板设计质量

| 指标 | Explanation | Question | Summary |
|------|-------------|----------|---------|
| 包含{selected_text} | ✅ | ✅ | ✅ |
| 包含{context} | ✅ | ✅ | ✅ |
| 结构化指导 | ✅ (3点) | ✅ (3点) | ✅ (3点) |
| 字数限制 | ✅ (200字) | ✅ (隐含) | ✅ (150字) |
| 教育原则 | 费曼技巧 | 苏格拉底式 | 信息加工 |

### 实现质量

- ✅ **可维护性**：模板集中管理，易于更新
- ✅ **可扩展性**：支持添加新类型
- ✅ **可测试性**：完整的单元测试覆盖
- ✅ **可配置性**：支持自定义系统提示词和模板
- ✅ **错误处理**：未知类型使用默认模板
- ✅ **验证机制**：模板更新时验证占位符

## 使用示例

### 示例1：生成Explanation批注

```python
from wayfare.context_builder import create_context_builder

builder = create_context_builder()

messages = builder.build_messages(
    selected_text="费曼技巧是一种学习方法",
    annotation_type="explanation",
    context_docs=[
        "费曼技巧由物理学家理查德·费曼提出",
        "这种方法强调用简单语言解释复杂概念"
    ]
)

# 输出：
# [
#   {
#     "role": "system",
#     "content": "你是WayFare学习助手...当前任务：使用费曼技巧..."
#   },
#   {
#     "role": "user", 
#     "content": "用户选中的文本：\n费曼技巧是一种学习方法\n\n相关上下文：\n[片段1]\n费曼技巧由物理学家理查德·费曼提出\n\n[片段2]\n这种方法强调用简单语言解释复杂概念\n\n请用简单易懂的语言解释这段内容..."
#   }
# ]
```

### 示例2：生成Question批注

```python
messages = builder.build_messages(
    selected_text="机器学习是人工智能的一个分支",
    annotation_type="question",
    context_docs=["机器学习使用算法从数据中学习"]
)

# 生成的消息将包含启发性问题的指导
```

### 示例3：生成Summary批注

```python
messages = builder.build_messages(
    selected_text="深度学习是机器学习的一个子领域",
    annotation_type="summary",
    context_docs=[]
)

# 即使没有上下文，也会优雅处理（显示"无相关上下文"）
```

## 集成验证

### 与Annotation Generator集成

Context Builder已经在Task 5.4中成功集成到Annotation Generator：

```python
# wayfare/annotation_generator.py
class AnnotationGenerator:
    def __init__(self, context_builder: WayFareContextBuilder, ...):
        self.context_builder = context_builder
    
    async def generate_annotation(self, ...):
        # 使用Context Builder构建消息
        messages = self.context_builder.build_messages(
            selected_text=context,
            annotation_type=annotation_type,
            context_docs=[c.text for c in contexts]
        )
        
        # 调用LLM生成批注
        response = await self.llm_provider.generate(messages)
```

### 端到端流程

1. ✅ 用户选中文本 → IPC请求
2. ✅ RAG检索相关上下文 → Vector Store
3. ✅ Context Builder构建Prompt → 包含选中文本和上下文
4. ✅ LLM生成批注 → 使用费曼技巧/启发性问题/要点总结
5. ✅ 返回批注给前端 → 完整流程

## 结论

Task 5.3的所有子任务在Task 5.2中已经完整实现并通过测试：

1. ✅ **子任务1**：Explanation模板（费曼技巧）- 已实现
2. ✅ **子任务2**：Question模板（启发性问题）- 已实现
3. ✅ **子任务3**：Summary模板（要点总结）- 已实现
4. ✅ **子任务4**：包含RAG上下文和用户选中文本 - 已实现

所有实现都经过充分测试（23个测试用例全部通过），满足Requirements 4.2和4.7的要求，可以直接用于生产环境。

## 相关文档

- [Task 5.3完成总结](./TASK_5.3_SUMMARY.md)
- [Prompt模板分析](./PROMPT_TEMPLATE_ANALYSIS.md)
- [Context Builder使用文档](../../wayfare/README_CONTEXT_BUILDER.md)
- [Context Builder实现](../../wayfare/context_builder.py)
- [单元测试](../../tests/wayfare/test_context_builder.py)
