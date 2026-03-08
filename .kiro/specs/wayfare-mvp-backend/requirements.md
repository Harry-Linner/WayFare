# WayFare MVP 后端需求文档

## 引言

WayFare是一个智能学习助手系统，采用"感知-决策-执行"三层架构。本需求文档定义负责人B的职责范围：智能管家内核（Sidecar）、模型逻辑（RAG、Prompt工程）、数据存储系统以及与前端的API接口。

本项目的核心原则是**最大化复用nanobot现有能力**，避免重复造轮子。nanobot已经实现了完整的agent loop、LLM provider抽象、工具系统、会话管理、记忆系统等核心功能，这些能力将通过导入、继承或配置的方式直接复用。

## 术语表

- **WayFare_Backend**: 智能管家内核，负责文档处理、RAG检索、批注生成和用户行为分析
- **Nanobot_Framework**: 现有的agent框架，提供LLM调用、工具系统、会话管理等基础能力
- **Document_Parser**: 文档解析引擎，将PDF/Markdown转换为结构化片段
- **Vector_Store**: 向量数据库（Qdrant），存储文档片段的embedding向量
- **Annotation_Generator**: 批注生成器，基于RAG和LLM生成学习辅助批注
- **IPC_Handler**: IPC通信处理器，处理与Tauri前端的消息交互
- **Behavior_Analyzer**: 用户行为分析器，分析学习行为并触发主动干预
- **Embedding_Service**: 向量化服务，使用ONNX模型生成文本embedding
- **Session_Store**: 会话存储，管理用户学习会话和上下文

## 需求

### 需求 1: 复用Nanobot核心框架

**用户故事:** 作为后端开发者，我希望复用nanobot的核心能力，以便快速构建WayFare后端而不需要从零开发基础设施。

#### 验收标准

1. THE WayFare_Backend SHALL 导入并使用 Nanobot_Framework 的 LLMProvider 抽象层进行所有LLM调用
2. THE WayFare_Backend SHALL 复用 Nanobot_Framework 的 ContextBuilder 来构建LLM上下文
3. THE WayFare_Backend SHALL 继承 Nanobot_Framework 的 ToolRegistry 机制来注册自定义工具
4. THE WayFare_Backend SHALL 使用 Nanobot_Framework 的配置系统（Pydantic schema）来管理配置
5. THE WayFare_Backend SHALL 复用 Nanobot_Framework 的 SessionManager 来管理用户会话状态

### 需求 2: 文档解析与结构化

**用户故事:** 作为学习者，我希望系统能够解析我的PDF和Markdown文档，以便AI能够理解文档内容并提供帮助。

#### 验收标准

1. WHEN 用户通过IPC发送parse请求，THE Document_Parser SHALL 解析PDF文件并提取文本、页码和边界框信息
2. WHEN 用户通过IPC发送parse请求，THE Document_Parser SHALL 解析Markdown文件并提取结构化内容
3. THE Document_Parser SHALL 将文档分割为语义连贯的片段（每个片段200-500字符）
4. THE Document_Parser SHALL 为每个文档生成唯一的hash标识（使用BLAKE3算法）
5. THE Document_Parser SHALL 为每个文档生成versionHash以检测内容变更
6. WHEN 文档解析完成，THE Document_Parser SHALL 将片段信息存储到SQLite数据库
7. IF 文档解析失败，THEN THE Document_Parser SHALL 返回描述性错误信息

### 需求 3: 向量化与检索系统

**用户故事:** 作为学习者，我希望系统能够快速检索相关文档内容，以便AI能够基于我的资料回答问题。

#### 验收标准

1. THE Embedding_Service SHALL 使用BAAI/bge-small-zh-v1.5 ONNX模型生成文本向量
2. WHEN 文档片段被解析，THE Embedding_Service SHALL 为每个片段生成512维向量
3. THE Vector_Store SHALL 将向量数据存储到Qdrant向量数据库
4. WHEN 用户发送query请求，THE Vector_Store SHALL 执行向量相似度搜索并返回top-k相关片段
5. THE Vector_Store SHALL 支持按文档hash过滤检索结果
6. THE Vector_Store SHALL 在200ms内完成单次检索操作（针对10000个片段的数据集）

### 需求 4: 批注生成与管理

**用户故事:** 作为学习者，我希望AI能够在文档的特定位置生成批注，以便我理解难点内容。

#### 验收标准

1. WHEN 用户通过IPC发送annotate请求，THE Annotation_Generator SHALL 使用RAG检索相关上下文
2. THE Annotation_Generator SHALL 调用LLM生成批注内容（使用费曼技巧和认知支架模板）
3. THE Annotation_Generator SHALL 将批注与文档位置（page和bbox）关联
4. THE Annotation_Generator SHALL 将批注绑定到文档的versionHash
5. THE Annotation_Generator SHALL 将批注存储到SQLite数据库
6. WHEN 批注生成完成，THE Annotation_Generator SHALL 返回批注ID和内容
7. THE Annotation_Generator SHALL 支持三种批注类型：explanation（解释）、question（提问）、summary（总结）

### 需求 5: IPC通信接口

**用户故事:** 作为前端开发者，我希望通过标准化的IPC协议与后端通信，以便实现前后端解耦。

#### 验收标准

1. THE IPC_Handler SHALL 接收符合api-contract.yaml规范的请求消息
2. THE IPC_Handler SHALL 验证请求消息的id、seq、method和params字段
3. THE IPC_Handler SHALL 按照seq序列号顺序处理请求，防止"先发后到"问题
4. THE IPC_Handler SHALL 支持四种方法：parse、annotate、query、config
5. WHEN 请求处理完成，THE IPC_Handler SHALL 返回包含id、seq、success和data的响应消息
6. IF 请求处理失败，THEN THE IPC_Handler SHALL 返回success=false和错误描述
7. THE IPC_Handler SHALL 在处理parse请求时异步执行，不阻塞其他请求

### 需求 6: 用户行为分析（MVP简化版）

**用户故事:** 作为学习者，我希望系统能够感知我的学习行为，以便在适当时机提供帮助。

#### 验收标准

1. THE Behavior_Analyzer SHALL 接收前端发送的用户行为数据（停留时间、划词频率）
2. THE Behavior_Analyzer SHALL 将行为数据存储到SQLite数据库
3. WHEN 用户在同一页面停留超过阈值（默认120秒），THE Behavior_Analyzer SHALL 触发主动干预信号
4. THE Behavior_Analyzer SHALL 通过IPC向前端发送主动消息推送
5. WHERE MVP阶段，THE Behavior_Analyzer SHALL 仅实现基于停留时间的简单触发逻辑

### 需求 7: 数据存储系统

**用户故事:** 作为系统管理员，我希望所有数据安全存储在本地，以便保护用户隐私。

#### 验收标准

1. THE WayFare_Backend SHALL 使用SQLite作为主数据库存储文档元数据、片段、批注和行为数据
2. THE WayFare_Backend SHALL 在用户工作区创建.wayfare隐藏文件夹存储数据库文件
3. THE WayFare_Backend SHALL 为documents表定义schema：hash、path、status、updatedAt、versionHash
4. THE WayFare_Backend SHALL 为segments表定义schema：id、docHash、text、page、bbox
5. THE WayFare_Backend SHALL 为annotations表定义schema：id、docHash、versionHash、type、content、bbox
6. THE WayFare_Backend SHALL 为behaviors表定义schema：id、docHash、page、eventType、timestamp、metadata
7. THE WayFare_Backend SHALL 将向量数据存储为BLOB格式以优化性能

### 需求 8: 配置管理

**用户故事:** 作为用户，我希望能够配置系统参数，以便个性化我的学习体验。

#### 验收标准

1. THE WayFare_Backend SHALL 通过config方法接收配置更新请求
2. THE WayFare_Backend SHALL 支持配置以下参数：LLM模型、embedding模型、检索top-k、主动干预阈值
3. THE WayFare_Backend SHALL 将配置持久化到config.yaml文件
4. THE WayFare_Backend SHALL 在启动时加载配置文件
5. WHERE 配置文件不存在，THE WayFare_Backend SHALL 使用默认配置并创建配置文件

### 需求 9: 文档解析器与Pretty Printer（关键质量保证）

**用户故事:** 作为开发者，我希望文档解析和序列化是可靠的，以便确保数据完整性。

#### 验收标准

1. THE Document_Parser SHALL 解析PDF文档并生成结构化的DocumentSegment对象
2. THE Document_Parser SHALL 解析Markdown文档并生成结构化的DocumentSegment对象
3. THE WayFare_Backend SHALL 实现Pretty_Printer将DocumentSegment对象序列化为JSON格式
4. FOR ALL 有效的DocumentSegment对象，解析后序列化再解析 SHALL 产生等价的对象（round-trip property）
5. THE Document_Parser SHALL 在解析失败时返回详细的错误位置和原因

### 需求 10: MVP功能边界

**用户故事:** 作为项目经理，我希望明确MVP阶段的功能范围，以便控制开发周期。

#### 验收标准

1. THE WayFare_Backend SHALL 在MVP阶段仅支持PDF和Markdown两种文档格式
2. THE WayFare_Backend SHALL 在MVP阶段不实现联网增强检索功能
3. THE WayFare_Backend SHALL 在MVP阶段不实现复杂的用户画像系统
4. THE WayFare_Backend SHALL 在MVP阶段不实现知识图谱构建功能
5. THE WayFare_Backend SHALL 在MVP阶段不实现多用户支持
6. THE WayFare_Backend SHALL 在MVP阶段使用固定的Prompt模板，不实现动态Prompt优化
7. THE WayFare_Backend SHALL 在MVP阶段使用本地ONNX模型，不支持在线embedding服务

## 复用策略总结

### 直接复用的Nanobot组件

1. **LLMProvider系统**: 通过`from nanobot.providers.base import LLMProvider`导入，使用现有的DeepSeek/SiliconFlow provider
2. **ContextBuilder**: 通过`from nanobot.agent.context import ContextBuilder`导入，用于构建LLM上下文
3. **ToolRegistry**: 通过`from nanobot.agent.tools.registry import ToolRegistry`导入，注册自定义工具
4. **配置系统**: 继承`nanobot.config.schema.Base`创建WayFare配置schema
5. **SessionManager**: 通过`from nanobot.session.manager import SessionManager`导入，管理用户会话

### 需要新开发的组件（参考Nanobot设计模式）

1. **Document_Parser**: 新开发，但参考nanobot的工具设计模式（继承BaseTool）
2. **Embedding_Service**: 新开发，使用ONNX Runtime
3. **Vector_Store**: 新开发，封装Qdrant客户端
4. **Annotation_Generator**: 新开发，但复用ContextBuilder和LLMProvider
5. **IPC_Handler**: 新开发，处理Tauri IPC协议
6. **Behavior_Analyzer**: 新开发，MVP简化版

### 不需要的Nanobot组件

1. **AgentLoop**: WayFare使用IPC驱动而非消息总线，不需要完整的agent loop
2. **ChannelManager**: WayFare不需要多渠道支持
3. **CronService**: MVP阶段不需要定时任务
4. **SubagentManager**: MVP阶段不需要子agent

## 技术架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    Tauri Frontend (负责人A)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ PDF Viewer   │  │ MD Editor    │  │ Behavior     │      │
│  │ (pdf.js)     │  │ (Milkdown)   │  │ Tracker      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │ IPC (JSON-RPC)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              WayFare Backend (负责人B - 本需求)               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              IPC_Handler (新开发)                      │  │
│  │  - parse()  - annotate()  - query()  - config()      │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                                │
│  ┌─────────────────────────┴─────────────────────────┐    │
│  │                                                     │    │
│  ▼                          ▼                         ▼    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Document     │  │ Annotation   │  │ Behavior     │    │
│  │ Parser       │  │ Generator    │  │ Analyzer     │    │
│  │ (新开发)      │  │ (新开发)      │  │ (新开发)      │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│         │                  │                  │            │
│         ▼                  ▼                  ▼            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Embedding    │  │ Vector_Store │  │ SQLite DB    │    │
│  │ Service      │  │ (Qdrant)     │  │              │    │
│  │ (ONNX)       │  │              │  │              │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                            │
│  ┌────────────────────────────────────────────────────┐  │
│  │         复用Nanobot组件                              │  │
│  │  - LLMProvider (DeepSeek via SiliconFlow)          │  │
│  │  - ContextBuilder (构建LLM上下文)                   │  │
│  │  - SessionManager (会话管理)                        │  │
│  │  - Config System (Pydantic schema)                 │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 数据模型

### SQLite Schema

```sql
-- 文档表
CREATE TABLE documents (
    hash TEXT PRIMARY KEY,
    path TEXT NOT NULL,
    status TEXT NOT NULL,  -- 'pending', 'processing', 'completed', 'failed'
    updated_at TEXT NOT NULL,
    version_hash TEXT NOT NULL
);

-- 片段表
CREATE TABLE segments (
    id TEXT PRIMARY KEY,
    doc_hash TEXT NOT NULL,
    text TEXT NOT NULL,
    page INTEGER NOT NULL,
    bbox_x REAL NOT NULL,
    bbox_y REAL NOT NULL,
    bbox_width REAL NOT NULL,
    bbox_height REAL NOT NULL,
    FOREIGN KEY (doc_hash) REFERENCES documents(hash)
);

-- 批注表
CREATE TABLE annotations (
    id TEXT PRIMARY KEY,
    doc_hash TEXT NOT NULL,
    version_hash TEXT NOT NULL,
    type TEXT NOT NULL,  -- 'explanation', 'question', 'summary'
    content TEXT NOT NULL,
    bbox_x REAL NOT NULL,
    bbox_y REAL NOT NULL,
    bbox_width REAL NOT NULL,
    bbox_height REAL NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (doc_hash) REFERENCES documents(hash)
);

-- 行为数据表
CREATE TABLE behaviors (
    id TEXT PRIMARY KEY,
    doc_hash TEXT NOT NULL,
    page INTEGER NOT NULL,
    event_type TEXT NOT NULL,  -- 'page_view', 'text_select', 'scroll'
    timestamp TEXT NOT NULL,
    metadata TEXT,  -- JSON格式的额外数据
    FOREIGN KEY (doc_hash) REFERENCES documents(hash)
);

-- 配置表
CREATE TABLE config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

## API接口规范

基于api-contract.yaml定义的IPC协议：

### parse方法
```json
{
  "id": "uuid",
  "seq": 1,
  "method": "parse",
  "params": {
    "path": "/path/to/document.pdf"
  }
}
```

响应：
```json
{
  "id": "uuid",
  "seq": 1,
  "success": true,
  "data": {
    "docHash": "blake3_hash",
    "versionHash": "content_hash",
    "segmentCount": 42,
    "status": "completed"
  }
}
```

### annotate方法
```json
{
  "id": "uuid",
  "seq": 2,
  "method": "annotate",
  "params": {
    "docHash": "blake3_hash",
    "page": 5,
    "bbox": {"x": 100, "y": 200, "width": 300, "height": 50},
    "type": "explanation",
    "context": "用户选中的文本"
  }
}
```

响应：
```json
{
  "id": "uuid",
  "seq": 2,
  "success": true,
  "data": {
    "annotationId": "uuid",
    "content": "AI生成的批注内容",
    "type": "explanation"
  }
}
```

### query方法
```json
{
  "id": "uuid",
  "seq": 3,
  "method": "query",
  "params": {
    "docHash": "blake3_hash",
    "query": "什么是费曼技巧？",
    "topK": 5
  }
}
```

响应：
```json
{
  "id": "uuid",
  "seq": 3,
  "success": true,
  "data": {
    "results": [
      {
        "segmentId": "uuid",
        "text": "相关片段文本",
        "page": 3,
        "score": 0.85
      }
    ]
  }
}
```

### config方法
```json
{
  "id": "uuid",
  "seq": 4,
  "method": "config",
  "params": {
    "llmModel": "deepseek-chat",
    "embeddingModel": "bge-small-zh-v1.5",
    "retrievalTopK": 5,
    "interventionThreshold": 120
  }
}
```

响应：
```json
{
  "id": "uuid",
  "seq": 4,
  "success": true,
  "data": {
    "updated": true
  }
}
```

## MVP阶段不实现的功能

1. **联网增强检索**: 不实现WebSearchTool集成
2. **复杂用户画像**: 不实现动态学习风格调整
3. **知识图谱**: 不实现概念关系图构建
4. **多用户支持**: 单用户本地部署
5. **动态Prompt优化**: 使用固定模板
6. **在线embedding服务**: 仅支持本地ONNX模型
7. **高级行为分析**: 仅实现基于停留时间的简单触发
8. **批注协作**: 不支持批注分享和讨论
9. **学习进度追踪**: 不实现复杂的进度统计
10. **多文档关联**: 不实现跨文档知识关联

## 开发优先级

### P0 (核心功能，必须实现)
- 需求1: 复用Nanobot核心框架
- 需求2: 文档解析与结构化
- 需求3: 向量化与检索系统
- 需求5: IPC通信接口
- 需求7: 数据存储系统

### P1 (重要功能，MVP必需)
- 需求4: 批注生成与管理
- 需求8: 配置管理
- 需求9: 文档解析器与Pretty Printer

### P2 (增强功能，可延后)
- 需求6: 用户行为分析
- 需求10: MVP功能边界明确化

## 技术选型理由

1. **Python作为主语言**: 复用nanobot生态，快速开发
2. **SQLite**: 轻量级、零配置、适合单用户场景
3. **Qdrant**: 高性能向量数据库，支持本地部署
4. **ONNX Runtime**: 跨平台、高性能的模型推理引擎
5. **BAAI/bge-small-zh-v1.5**: 中文优化、模型小、推理快
6. **DeepSeek-V3.2**: 性价比高、中文能力强
7. **SiliconFlow API**: 国内访问稳定、价格合理

## 性能目标

1. 文档解析: 1MB PDF文档在5秒内完成解析
2. 向量检索: 单次查询在200ms内返回结果（10000片段数据集）
3. 批注生成: 单次批注在3秒内生成（包含LLM调用）
4. IPC响应: 非LLM操作在100ms内响应
5. 内存占用: 空闲状态下不超过200MB
6. 数据库大小: 1000个文档的数据库不超过500MB

## 安全与隐私

1. 所有数据存储在用户本地，不上传云端
2. 向量数据库使用本地Qdrant实例
3. LLM调用通过SiliconFlow API，不存储用户数据
4. 配置文件不包含敏感信息（API key通过环境变量）
5. 文档路径使用相对路径，保护用户隐私
