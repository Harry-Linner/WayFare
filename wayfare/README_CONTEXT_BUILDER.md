# WayFare Context Builder

## 概述

WayFare Context Builder是批注生成系统的核心组件，负责为LLM构建结构化的上下文。它封装了系统提示词配置、RAG上下文文档格式化和批注类型特定的Prompt模板。

## 设计理念

Context Builder的设计遵循以下原则：

1. **简洁性**: 提供简单直观的API，隐藏复杂的Prompt工程细节
2. **可配置性**: 支持自定义系统提示词和Prompt模板
3. **类型安全**: 使用明确的批注类型（explanation/question/summary）
4. **格式化**: 自动格式化RAG检索到的上下文文档

## 核心功能

### 1. 批注类型

Context Builder支持三种批注类型：

- **explanation**: 使用费曼技巧解释复杂概念
- **question**: 提出启发性问题引导思考
- **summary**: 提炼核心要点和关键信息

### 2. 系统提示词

默认系统提示词定义了WayFare学习助手的角色和行为准则：

```python
SYSTEM_PROMPT = """你是WayFare学习助手，帮助学生理解和掌握知识。

你的职责是：
1. 使用费曼技巧，用简单易懂的语言解释复杂概念
2. 通过启发性问题引导学生深入思考
3. 提炼核心要点，帮助学生建立知识框架

你的回答应该：
- 简洁明了，不超过200字
- 贴近学生的认知水平
- 结合具体例子和类比
- 鼓励主动思考和探索"""
```

### 3. Prompt模板

每种批注类型都有专门的Prompt模板，包含：

- 用户选中的文本
- RAG检索到的相关上下文
- 具体的任务指导

模板使用`{selected_text}`和`{context}`占位符，在运行时填充实际内容。

### 4. 上下文格式化

Context Builder自动格式化RAG检索到的文档：

```
[片段1]
第一个相关文档的内容

[片段2]
第二个相关文档的内容

[片段3]
第三个相关文档的内容
```

## 使用方法

### 基本使用

```python
from wayfare.context_builder import create_context_builder

# 创建Context Builder
builder = create_context_builder()

# 构建批注生成的消息
messages = builder.build_messages(
    selected_text="费曼技巧是一种学习方法",
    annotation_type="explanation",
    context_docs=[
        "费曼技巧由物理学家理查德·费曼提出",
        "这种方法强调用简单语言解释复杂概念"
    ]
)

# messages格式:
# [
#     {"role": "system", "content": "系统提示词..."},
#     {"role": "user", "content": "用户消息..."}
# ]
```

### 与LLM Provider集成

```python
from wayfare.context_builder import create_context_builder
from wayfare.llm_provider import create_llm_provider

# 创建组件
builder = create_context_builder()
llm = create_llm_provider()

# 构建消息
messages = builder.build_messages(
    selected_text="机器学习是人工智能的一个分支",
    annotation_type="explanation",
    context_docs=["相关上下文1", "相关上下文2"]
)

# 调用LLM生成批注
response = await llm.generate(messages)
annotation_content = response.content
```

### 自定义系统提示词

```python
builder = create_context_builder()

custom_prompt = "你是一个专业的数学老师，擅长用生动的例子解释抽象概念。"

messages = builder.build_messages(
    selected_text="导数表示函数的瞬时变化率",
    annotation_type="explanation",
    context_docs=["导数的几何意义是切线斜率"],
    system_prompt=custom_prompt
)
```

### 更新Prompt模板

```python
builder = create_context_builder()

# 自定义explanation模板
new_template = """用户选中的文本：
{selected_text}

相关上下文：
{context}

请用通俗易懂的语言解释，要求：
1. 使用生活中的例子
2. 避免专业术语
3. 不超过150字"""

builder.update_prompt_template("explanation", new_template)
```

### 构建简单消息

```python
builder = create_context_builder()

# 单轮对话，不需要RAG上下文
messages = builder.build_simple_message(
    prompt="请解释什么是机器学习",
    system_prompt="你是一个AI助手"  # 可选
)
```

### 查询可用类型

```python
builder = create_context_builder()

# 获取所有批注类型
types = builder.get_available_types()
# ['explanation', 'question', 'summary']

# 获取特定类型的模板
template = builder.get_prompt_template("explanation")
```

## API参考

### WayFareContextBuilder

#### `__init__()`

初始化Context Builder。

#### `build_messages(selected_text, annotation_type, context_docs, system_prompt=None)`

构建LLM消息列表。

**参数:**
- `selected_text` (str): 用户选中的文本
- `annotation_type` (str): 批注类型（explanation/question/summary）
- `context_docs` (List[str]): RAG检索到的上下文文档列表
- `system_prompt` (Optional[str]): 可选的自定义系统提示词

**返回:**
- `List[Dict[str, Any]]`: 消息列表，格式为`[{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]`

#### `build_simple_message(prompt, system_prompt=None)`

构建简单的单轮对话消息。

**参数:**
- `prompt` (str): 用户提示词
- `system_prompt` (Optional[str]): 可选的系统提示词

**返回:**
- `List[Dict[str, Any]]`: 消息列表

#### `update_prompt_template(annotation_type, template)`

更新Prompt模板。

**参数:**
- `annotation_type` (str): 批注类型
- `template` (str): 新的模板字符串，必须包含`{selected_text}`和`{context}`占位符

#### `get_prompt_template(annotation_type)`

获取Prompt模板。

**参数:**
- `annotation_type` (str): 批注类型

**返回:**
- `Optional[str]`: 模板字符串，如果类型不存在则返回None

#### `get_available_types()`

获取所有可用的批注类型。

**返回:**
- `List[str]`: 批注类型列表

### 工厂函数

#### `create_context_builder()`

创建Context Builder实例。

**返回:**
- `WayFareContextBuilder`: Context Builder实例

## 设计模式

### 1. 模板方法模式

Context Builder使用模板方法模式来构建消息：

1. 构建系统提示词（基础提示词 + 类型特定指导）
2. 格式化上下文文档（添加编号和分隔符）
3. 选择Prompt模板（根据批注类型）
4. 填充模板（替换占位符）
5. 组装消息列表（系统消息 + 用户消息）

### 2. 策略模式

不同的批注类型使用不同的Prompt策略：

- **explanation策略**: 强调简单语言和类比
- **question策略**: 强调启发性和思考引导
- **summary策略**: 强调要点提炼和结构化

### 3. 工厂模式

使用工厂函数`create_context_builder()`创建实例，便于未来扩展配置选项。

## 最佳实践

### 1. 上下文文档数量

建议RAG检索返回3-5个相关文档：

- 太少：上下文不足，批注质量下降
- 太多：上下文冗余，增加token消耗

### 2. 文档长度

每个上下文文档应该是语义完整的片段（200-500字符）：

- 太短：语义不完整
- 太长：包含无关信息

### 3. 批注类型选择

根据用户意图选择合适的批注类型：

- 用户不理解概念 → explanation
- 用户需要深入思考 → question
- 用户需要快速回顾 → summary

### 4. 系统提示词定制

针对特定学科或场景定制系统提示词：

```python
# 数学场景
math_prompt = "你是数学老师，擅长用几何直观和代数推导解释概念。"

# 编程场景
coding_prompt = "你是编程导师，擅长用代码示例和调试技巧解释概念。"

# 历史场景
history_prompt = "你是历史老师，擅长用时间线和因果关系解释历史事件。"
```

### 5. 模板更新

更新模板时确保：

- 包含必要的占位符（`{selected_text}`和`{context}`）
- 明确任务指导
- 控制输出长度
- 保持一致的格式

## 性能考虑

### Token消耗

Context Builder构建的消息包含：

- 系统提示词：约200-300 tokens
- 用户消息：约500-1000 tokens（取决于上下文数量）
- 总计：约700-1300 tokens

### 优化建议

1. **限制上下文数量**: 使用top-5而非top-10
2. **压缩上下文**: 去除冗余信息
3. **缓存系统提示词**: 避免重复构建
4. **批量处理**: 一次构建多个批注的消息

## 错误处理

Context Builder会处理以下错误情况：

1. **未知批注类型**: 使用explanation作为默认类型
2. **空上下文**: 显示"（无相关上下文）"
3. **无效模板**: 拒绝更新并记录警告
4. **缺少占位符**: 拒绝更新并记录错误

## 测试

运行单元测试：

```bash
pytest tests/wayfare/test_context_builder.py -v
```

运行使用示例：

```bash
python examples/context_builder_usage_example.py
```

## 与其他组件的集成

### 与LLM Provider集成

```python
# 1. 构建消息
messages = builder.build_messages(...)

# 2. 调用LLM
response = await llm.generate(messages)

# 3. 提取批注内容
annotation_content = response.content
```

### 与Annotation Generator集成

```python
class AnnotationGenerator:
    def __init__(self, llm_provider, context_builder, vector_store):
        self.llm = llm_provider
        self.builder = context_builder
        self.vector_store = vector_store
    
    async def generate_annotation(self, selected_text, annotation_type, doc_hash):
        # 1. RAG检索
        context_docs = await self.vector_store.search(...)
        
        # 2. 构建消息
        messages = self.builder.build_messages(
            selected_text=selected_text,
            annotation_type=annotation_type,
            context_docs=[doc.text for doc in context_docs]
        )
        
        # 3. 生成批注
        response = await self.llm.generate(messages)
        return response.content
```

## 未来扩展

### 1. 多语言支持

支持英文、日文等其他语言的系统提示词和模板。

### 2. 动态模板选择

根据用户的学习风格和历史反馈动态选择最佳模板。

### 3. 上下文压缩

使用LLM对长上下文进行智能压缩，减少token消耗。

### 4. 多模态支持

支持图片、公式等多模态内容的上下文构建。

## 相关文档

- [LLM Provider文档](README_LLM_PROVIDER.md)
- [Annotation Generator设计](../design.md#5-annotation_generator)
- [批注生成流程](../design.md#批注生成流程-annotate方法)

## 许可证

MIT License
