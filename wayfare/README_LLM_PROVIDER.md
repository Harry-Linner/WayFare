# LLM Provider模块文档

## 概述

LLM Provider模块封装了nanobot的LLMProvider系统，提供统一的LLM调用接口。本模块配置SiliconFlow API访问DeepSeek-V3.2模型，并实现了完善的错误处理和重试机制。

## 架构设计

### 复用策略

本模块**完全复用**nanobot的LLM Provider系统：

```python
from nanobot.providers.base import LLMProvider, LLMResponse
from nanobot.providers.litellm_provider import LiteLLMProvider
```

- **LLMProvider**: nanobot的抽象基类，定义统一的LLM调用接口
- **LiteLLMProvider**: nanobot的LiteLLM实现，支持多种LLM提供商
- **LLMResponse**: 标准化的响应格式

### WayFareLLMProvider封装

`WayFareLLMProvider`类在nanobot的基础上提供：

1. **SiliconFlow配置**: 自动配置SiliconFlow provider访问DeepSeek模型
2. **错误处理**: 捕获并处理各种LLM调用错误
3. **重试机制**: 指数退避的自动重试
4. **超时控制**: 防止请求无限等待
5. **简化接口**: 提供便捷的单轮对话接口

## 核心类

### WayFareLLMProvider

主要的LLM Provider封装类。

#### 初始化

```python
from wayfare.llm_provider import WayFareLLMProvider

provider = WayFareLLMProvider(
    api_key="your_siliconflow_api_key",  # 可选，默认从环境变量读取
    model="deepseek-chat",                # DeepSeek模型
    max_retries=3,                        # 最大重试次数
    retry_delay=1.0,                      # 重试延迟（秒）
    timeout=60.0                          # 请求超时（秒）
)
```

#### 方法

##### generate()

生成LLM响应（多轮对话）。

```python
async def generate(
    messages: List[Dict[str, Any]],
    max_tokens: int = 4096,
    temperature: float = 0.7,
    tools: Optional[List[Dict[str, Any]]] = None
) -> LLMResponse
```

**参数**:
- `messages`: 消息列表，格式为`[{"role": "user", "content": "..."}]`
- `max_tokens`: 最大生成token数
- `temperature`: 采样温度（0.0-1.0）
- `tools`: 可选的工具定义列表（用于function calling）

**返回**:
- `LLMResponse`: 包含生成内容、工具调用、使用统计等信息

**示例**:

```python
messages = [
    {"role": "system", "content": "你是一个学习助手"},
    {"role": "user", "content": "解释什么是费曼技巧"}
]

response = await provider.generate(
    messages=messages,
    max_tokens=500,
    temperature=0.7
)

print(response.content)
print(f"使用token数: {response.usage['total_tokens']}")
```

##### generate_simple()

简化的单轮对话接口。

```python
async def generate_simple(
    prompt: str,
    system_prompt: Optional[str] = None,
    max_tokens: int = 4096,
    temperature: float = 0.7
) -> str
```

**参数**:
- `prompt`: 用户提示词
- `system_prompt`: 可选的系统提示词
- `max_tokens`: 最大生成token数
- `temperature`: 采样温度

**返回**:
- `str`: 生成的文本内容

**示例**:

```python
content = await provider.generate_simple(
    prompt="解释什么是费曼技巧",
    system_prompt="你是一个学习助手，用简单的语言解释概念。",
    max_tokens=500
)

print(content)
```

##### update_config()

动态更新配置。

```python
def update_config(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    max_retries: Optional[int] = None,
    retry_delay: Optional[float] = None,
    timeout: Optional[float] = None
)
```

**示例**:

```python
provider.update_config(
    model="deepseek-chat",
    max_retries=5,
    timeout=90.0
)
```

## 工厂函数

### create_llm_provider()

便捷的工厂函数，用于创建LLM Provider实例。

```python
from wayfare.llm_provider import create_llm_provider

provider = create_llm_provider(
    api_key="your_api_key",
    model="deepseek-chat",
    max_retries=3
)
```

## 错误处理

### 重试机制

当LLM请求失败时，自动进行重试：

1. **指数退避**: 每次重试的延迟时间递增（1s, 2s, 3s...）
2. **最大重试次数**: 默认3次，可配置
3. **超时控制**: 每次请求有独立的超时限制

### 错误类型

模块处理以下错误：

1. **网络错误**: 连接超时、网络中断
2. **API错误**: 认证失败、配额超限
3. **超时错误**: 请求超过timeout时间
4. **响应错误**: LLM返回错误状态

### 错误响应

当所有重试都失败时，返回包含错误信息的`LLMResponse`：

```python
response = await provider.generate(messages)

if response.finish_reason == "error":
    print(f"LLM调用失败: {response.content}")
    # 处理错误...
```

## 配置管理

### 环境变量

推荐使用环境变量配置API密钥：

```bash
export SILICONFLOW_API_KEY="your_api_key"
```

### 配置文件

在`config.yaml`中配置LLM参数：

```yaml
llm_model: deepseek-chat
llm_max_retries: 3
llm_retry_delay: 1.0
llm_timeout: 60.0
llm_max_tokens: 4096
llm_temperature: 0.7
```

### 从ConfigManager加载

```python
from wayfare.config import ConfigManager
from wayfare.llm_provider import create_llm_provider

config_manager = ConfigManager()
config = config_manager.get_config()

provider = create_llm_provider(
    api_key=config.llm_api_key,
    model=config.llm_model,
    max_retries=config.llm_max_retries,
    retry_delay=config.llm_retry_delay,
    timeout=config.llm_timeout
)
```

## 使用示例

### 基本使用

```python
import asyncio
from wayfare.llm_provider import create_llm_provider

async def main():
    # 创建provider
    provider = create_llm_provider()
    
    # 简单对话
    response = await provider.generate_simple(
        prompt="什么是费曼技巧？",
        system_prompt="你是一个学习助手。"
    )
    
    print(response)

asyncio.run(main())
```

### 多轮对话

```python
async def chat_example():
    provider = create_llm_provider()
    
    messages = [
        {"role": "system", "content": "你是一个学习助手"},
        {"role": "user", "content": "什么是费曼技巧？"},
    ]
    
    # 第一轮
    response1 = await provider.generate(messages)
    print(f"助手: {response1.content}")
    
    # 添加助手回复到历史
    messages.append({
        "role": "assistant",
        "content": response1.content
    })
    
    # 第二轮
    messages.append({
        "role": "user",
        "content": "能举个例子吗？"
    })
    
    response2 = await provider.generate(messages)
    print(f"助手: {response2.content}")
```

### 与AnnotationGenerator集成

```python
from wayfare.llm_provider import create_llm_provider
from wayfare.vector_store import VectorStore
from wayfare.embedding import EmbeddingService

class AnnotationGenerator:
    def __init__(self):
        self.llm_provider = create_llm_provider()
        self.vector_store = VectorStore()
        self.embedding_service = EmbeddingService()
    
    async def generate_annotation(
        self,
        selected_text: str,
        doc_hash: str,
        annotation_type: str = "explanation"
    ):
        # 1. RAG检索
        query_vector = await self.embedding_service.embed_single(selected_text)
        contexts = await self.vector_store.search(
            query_vector=query_vector,
            top_k=5,
            doc_hash=doc_hash
        )
        
        # 2. 构建prompt
        context_str = "\n\n".join([c.text for c in contexts])
        
        prompt = f"""用户选中的文本：
{selected_text}

相关上下文：
{context_str}

请用简单易懂的语言解释这段内容。"""
        
        # 3. 调用LLM
        response = await self.llm_provider.generate_simple(
            prompt=prompt,
            system_prompt="你是WayFare学习助手，使用费曼技巧帮助学生理解概念。"
        )
        
        return response
```

## 性能优化

### 批量请求

对于批量生成任务，使用`asyncio.gather`并发执行：

```python
async def batch_generate(prompts: List[str]):
    provider = create_llm_provider()
    
    tasks = [
        provider.generate_simple(prompt)
        for prompt in prompts
    ]
    
    results = await asyncio.gather(*tasks)
    return results
```

### 超时控制

根据任务类型调整超时时间：

```python
# 短文本生成：30秒
provider = create_llm_provider(timeout=30.0)

# 长文本生成：120秒
provider = create_llm_provider(timeout=120.0)
```

## 日志

模块使用`loguru`记录日志：

```python
from loguru import logger

# 配置日志级别
logger.add("wayfare.log", level="DEBUG")
```

日志内容包括：
- Provider初始化信息
- 请求成功/失败
- 重试尝试
- Token使用统计

## 测试

### 单元测试

```python
import pytest
from wayfare.llm_provider import create_llm_provider

@pytest.mark.asyncio
async def test_generate_simple():
    provider = create_llm_provider()
    
    response = await provider.generate_simple(
        prompt="Hello",
        system_prompt="You are a helpful assistant."
    )
    
    assert isinstance(response, str)
    assert len(response) > 0

@pytest.mark.asyncio
async def test_retry_on_failure():
    # 测试重试机制
    provider = create_llm_provider(
        api_key="invalid_key",
        max_retries=2
    )
    
    response = await provider.generate_simple("test")
    
    # 应该返回错误响应而不是抛出异常
    assert "错误" in response or "error" in response.lower()
```

## 注意事项

1. **API密钥安全**: 
   - 不要在代码中硬编码API密钥
   - 使用环境变量或配置文件
   - 不要将包含密钥的配置文件提交到版本控制

2. **成本控制**:
   - 设置合理的`max_tokens`限制
   - 监控API使用量
   - 使用缓存减少重复请求

3. **错误处理**:
   - 始终检查`response.finish_reason`
   - 为用户提供友好的错误提示
   - 记录错误日志用于调试

4. **性能优化**:
   - 对于批量任务使用并发
   - 合理设置超时时间
   - 避免不必要的重试

## 相关文档

- [nanobot LLM Provider文档](../nanobot/providers/)
- [SiliconFlow API文档](https://siliconflow.cn/docs)
- [DeepSeek模型文档](https://platform.deepseek.com/docs)
- [WayFare配置管理](./README_CONFIG.md)
