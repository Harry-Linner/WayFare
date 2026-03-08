# Implementation Plan: WayFare MVP Backend

## Overview

本实现计划将WayFare MVP Backend的设计转换为可执行的开发任务。系统采用Python开发，最大化复用nanobot框架，作为Tauri应用的Sidecar进程运行。实现分为6个阶段，每个阶段包含具体的编码任务和测试任务。

## Tasks

- [ ] 1. Phase 1: 核心基础设施搭建
  - [x] 1.1 创建项目结构和配置系统
    - 创建wayfare包目录结构（wayfare/、tests/、models/）
    - 实现WayFareConfig类，继承nanobot的BaseConfig
    - 实现ConfigManager类，支持YAML配置文件加载和保存
    - 添加环境变量覆盖支持（WAYFARE_*前缀）
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_
  
  - [ ]* 1.2 编写配置系统的属性测试
    - **Property 25: 配置更新持久化**
    - **Property 26: 配置加载**
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**
  
  - [x] 1.3 实现SQLite数据库层
    - 创建SQLiteDB类，实现数据库连接管理
    - 实现initialize()方法，创建所有表和索引
    - 实现documents表的CRUD操作
    - 实现segments表的CRUD操作
    - 实现annotations表的CRUD操作
    - 实现behaviors表的CRUD操作
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_
  
  - [ ]* 1.4 编写数据库层的单元测试
    - 测试数据库初始化和schema创建
    - 测试各表的CRUD操作
    - 测试外键约束和级联删除
    - 测试索引创建
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_
  
  - [x] 1.5 实现IPC Handler基础框架
    - 创建IPCRequest和IPCResponse数据模型（Pydantic）
    - 实现IPCHandler类的基本结构
    - 实现请求解析和验证逻辑
    - 实现请求队列和按seq排序机制
    - 实现错误处理和标准错误响应格式
    - _Requirements: 5.1, 5.2, 5.3_
  
  - [ ]* 1.6 编写IPC Handler的属性测试
    - **Property 17: IPC请求格式验证**
    - **Property 18: IPC请求序列化处理**
    - **Property 20: IPC响应格式**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.5, 5.6**
  
  - [x] 1.7 实现日志系统和错误处理框架
    - 配置logging模块，支持文件和控制台输出
    - 实现RotatingFileHandler，日志文件自动轮转
    - 定义自定义异常类（DocumentParseError、VectorSearchError等）
    - 实现错误监控器ErrorMonitor类
    - 实现用户友好的错误消息转换函数
    - _Requirements: 所有需求的错误处理部分_

- [ ] 2. Checkpoint - 基础设施验证
  - 确保所有测试通过，配置系统和数据库正常工作，询问用户是否有问题

- [x] 3. Phase 2: 文档处理实现
  - [x] 3.1 实现Embedding Service
    - 创建EmbeddingService类
    - 实现ONNX模型加载（使用onnxruntime）
    - 实现tokenizer加载（使用transformers库）
    - 实现embed_texts()批量向量生成方法
    - 实现embed_single()单文本向量生成方法
    - 添加向量L2归一化处理
    - _Requirements: 3.1, 3.2_
  
  - [ ]* 3.2 编写Embedding Service的属性测试
    - **Property 8: Embedding向量维度**
    - **Validates: Requirements 3.2**
  
  - [x] 3.3 实现Vector Store
    - 创建VectorStore类，封装Qdrant客户端
    - 实现initialize()方法，创建collection
    - 实现upsert_vectors()批量向量存储方法
    - 实现search()向量相似度搜索方法
    - 实现按doc_hash过滤的搜索功能
    - 实现delete_document()删除文档向量方法
    - _Requirements: 3.3, 3.4, 3.5_
  
  - [ ]* 3.4 编写Vector Store的属性测试
    - **Property 9: 向量存储round-trip**
    - **Property 10: Top-K检索结果数量**
    - **Property 11: 文档hash过滤有效性**
    - **Validates: Requirements 3.3, 3.4, 3.5**
  
  - [x] 3.5 实现Document Parser - PDF解析
    - 创建DocumentParser类
    - 实现compute_hash()方法（使用BLAKE3）
    - 实现compute_version_hash()方法
    - 实现parse_pdf()方法（使用PyMuPDF）
    - 提取PDF文本、页码和边界框信息
    - _Requirements: 2.1, 2.4, 2.5, 9.1_
  
  - [x] 3.6 实现Document Parser - Markdown解析
    - 实现parse_markdown()方法（使用markdown-it-py）
    - 提取Markdown结构化内容（标题、段落）
    - 为Markdown内容生成虚拟页码和边界框
    - _Requirements: 2.2, 9.2_
  
  - [x] 3.7 实现文档分块逻辑
    - 实现chunk_text()方法
    - 实现滑动窗口分块算法（chunk_size=300, overlap=50）
    - 在句子边界优先分割（支持中英文标点）
    - 确保分块大小在200-500字符范围内
    - _Requirements: 2.3_
  
  - [ ]* 3.8 编写文档分块的属性测试
    - **Property 3: 文档分块大小约束**
    - **Validates: Requirements 2.3**
  
  - [x] 3.9 实现文档解析完整流程
    - 实现parse_document()主方法
    - 集成文档解析、分块、向量生成和存储
    - 实现异步处理和进度跟踪
    - 实现文档状态管理（pending/processing/completed/failed）
    - 添加错误处理和恢复机制
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_
  
  - [ ]* 3.10 编写文档解析的属性测试
    - **Property 1: PDF文档解析完整性**
    - **Property 2: Markdown文档解析完整性**
    - **Property 4: 文档hash唯一性和一致性**
    - **Property 5: 版本hash变更检测**
    - **Property 6: 片段持久化**
    - **Property 7: 解析错误处理**
    - **Validates: Requirements 2.1, 2.2, 2.4, 2.5, 2.6, 2.7, 9.1, 9.2, 9.5**
  
  - [x] 3.11 集成parse方法到IPC Handler
    - 实现IPCHandler.handle_parse()方法
    - 实现异步文档解析任务调度
    - 实现解析完成后的主动推送通知
    - 添加parse请求的错误处理
    - _Requirements: 5.4, 5.7_
  
  - [ ]* 3.12 编写parse方法的属性测试
    - **Property 21: Parse请求异步处理**
    - **Validates: Requirements 5.7**

- [x] 4. Checkpoint - 文档处理验证
  - 确保所有测试通过，文档解析和向量化流程正常工作，询问用户是否有问题

- [x] 5. Phase 3: 批注生成实现
  - [x] 5.1 集成nanobot的LLM Provider
    - 从nanobot导入LLMProvider基类
    - 从nanobot导入SiliconFlowProvider
    - 配置DeepSeek-V3.2模型
    - 实现LLM调用的错误处理和重试机制
    - _Requirements: 1.1_
  
  - [x] 5.2 集成nanobot的Context Builder
    - 从nanobot导入ContextBuilder
    - 配置系统提示词
    - 实现上下文文档的格式化
    - _Requirements: 1.2_
  
  - [x] 5.3 设计批注Prompt模板
    - 创建explanation类型的Prompt模板（费曼技巧）
    - 创建question类型的Prompt模板（启发性问题）
    - 创建summary类型的Prompt模板（要点总结）
    - 确保Prompt包含RAG上下文和用户选中文本
    - _Requirements: 4.2, 4.7_
  
  - [x] 5.4 实现Annotation Generator核心逻辑
    - 创建AnnotationGenerator类
    - 注入LLMProvider、ContextBuilder、VectorStore、EmbeddingService
    - 实现generate_annotation()主方法
    - 实现RAG检索逻辑（查询向量生成 + top-5检索）
    - 实现Prompt构建逻辑（选择模板 + 填充上下文）
    - 实现LLM调用和响应处理
    - _Requirements: 4.1, 4.2_
  
  - [x] 5.5 实现批注存储和位置关联
    - 创建Annotation数据模型（Pydantic）
    - 实现批注与文档位置（page、bbox）的关联
    - 实现批注与version_hash的绑定
    - 实现批注存储到SQLite数据库
    - _Requirements: 4.3, 4.4, 4.5_
  
  - [ ]* 5.6 编写批注生成的属性测试
    - **Property 12: 批注生成包含RAG上下文**
    - **Property 13: 批注位置关联**
    - **Property 14: 批注版本绑定**
    - **Property 15: 批注持久化和返回**
    - **Property 16: 批注类型支持**
    - **Validates: Requirements 4.1, 4.3, 4.4, 4.5, 4.6, 4.7**
  
  - [x] 5.7 实现批注生成的降级策略
    - 实现LLM调用失败时的fallback机制
    - 为每种批注类型提供预设的降级文本
    - 添加降级事件的日志记录
    - _Requirements: 4.2_
  
  - [x] 5.8 集成annotate方法到IPC Handler
    - 实现IPCHandler.handle_annotate()方法
    - 解析annotate请求参数（docHash、page、bbox、type、context）
    - 调用AnnotationGenerator生成批注
    - 返回批注ID和内容
    - 添加annotate请求的错误处理
    - _Requirements: 5.4, 5.5, 5.6_
  
  - [x] 5.9 集成query方法到IPC Handler
    - 实现IPCHandler.handle_query()方法
    - 实现VectorStore.search_documents()辅助方法
    - 集成EmbeddingService生成查询向量
    - 返回检索结果（segmentId、text、page、score）
    - 添加query请求的错误处理
    - _Requirements: 5.4_
  
  - [ ]* 5.10 编写IPC方法的属性测试
    - **Property 19: IPC方法支持**
    - **Validates: Requirements 5.4**

- [x] 6. Checkpoint - 批注生成验证
  - 确保所有测试通过，批注生成和RAG检索正常工作，询问用户是否有问题

- [x] 7. Phase 4: 行为分析实现
  - [x] 7.1 实现Behavior Analyzer基础功能
    - 创建BehaviorAnalyzer类
    - 创建BehaviorEvent数据模型（Pydantic）
    - 实现record_behavior()方法，存储行为数据到SQLite
    - 实现get_behaviors()查询方法
    - _Requirements: 6.1, 6.2_
  
  - [ ]* 7.2 编写行为数据存储的属性测试
    - **Property 22: 行为数据持久化**
    - **Validates: Requirements 6.1, 6.2**
  
  - [x] 7.3 实现停留时间触发逻辑
    - 实现_track_page_view()方法，记录页面浏览开始时间
    - 实现check_intervention_trigger()方法，检查停留时间是否超过阈值
    - 使用字典跟踪当前页面的停留时间
    - 实现触发后的计时器重置逻辑
    - _Requirements: 6.3_
  
  - [ ]* 7.4 编写停留时间触发的属性测试
    - **Property 23: 停留时间触发干预**
    - **Validates: Requirements 6.3**
  
  - [x] 7.5 实现主动干预推送机制
    - 实现send_intervention()方法
    - 通过IPC Handler的_send_notification()发送主动消息
    - 实现get_page_statistics()方法，生成页面统计信息
    - _Requirements: 6.4_
  
  - [ ]* 7.6 编写主动干预的属性测试
    - **Property 24: 主动干预推送**
    - **Validates: Requirements 6.4**
  
  - [x] 7.7 集成行为分析到IPC Handler
    - 在IPC Handler中添加behavior事件处理
    - 调用BehaviorAnalyzer记录行为
    - 定期检查干预触发条件
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 8. Checkpoint - 行为分析验证
  - 确保所有测试通过，行为分析和主动干预正常工作，询问用户是否有问题

- [x] 9. Phase 5: 集成测试和性能优化
  - [x] 9.1 编写完整的文档解析流程集成测试
    - 测试从IPC请求到数据库存储的完整流程
    - 测试异步解析和主动推送通知
    - 测试多文档并发解析
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_
  
  - [x] 9.2 编写完整的批注生成流程集成测试
    - 测试从IPC请求到批注返回的完整流程
    - 测试RAG检索和LLM调用集成
    - 测试三种批注类型的生成
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_
  
  - [x] 9.3 编写完整的查询检索流程集成测试
    - 测试从IPC请求到检索结果返回的完整流程
    - 测试文档hash过滤功能
    - 测试top-k参数控制
    - _Requirements: 3.4, 3.5_
  
  - [x] 9.4 编写序列化round-trip属性测试
    - **Property 27: DocumentSegment序列化round-trip**
    - **Validates: Requirements 9.3, 9.4**
  
  - [ ]* 9.5 实现性能优化 - 批量处理
    - 优化embedding生成的批处理（batch_size=32）
    - 优化数据库批量插入（使用executemany）
    - 优化向量批量存储
    - _Requirements: 性能目标_
  
  - [ ]* 9.6 实现性能优化 - 异步处理
    - 使用asyncio.gather并发处理多个任务
    - 使用线程池处理CPU密集型任务（PDF解析）
    - 实现TaskLimiter限制并发数
    - _Requirements: 性能目标_
  
  - [ ]* 9.7 实现性能优化 - 缓存策略
    - 为EmbeddingService添加LRU缓存
    - 缓存最近的embedding结果（cache_size=1000）
    - 实现缓存过期和清理机制
    - _Requirements: 性能目标_
  
  - [ ]* 9.8 编写性能测试
    - 测试文档解析性能（1MB PDF在5秒内完成）
    - 测试向量检索性能（10000片段数据集在200ms内完成）
    - 测试批注生成性能（单次批注在3秒内完成）
    - _Requirements: 性能目标_
  
  - [ ]* 9.9 实现资源限制和优雅关闭
    - 实现TaskLimiter限制并发任务数
    - 实现GracefulShutdown处理关闭信号
    - 实现cleanup_partial_data()清理失败数据
    - 添加信号处理器（SIGINT、SIGTERM）
    - _Requirements: 系统稳定性_

- [x] 10. Checkpoint - 集成测试和性能验证
  - 确保所有测试通过，系统性能满足目标，询问用户是否有问题

- [x] 11. Phase 6: 部署准备和主程序
  - [x] 11.1 实现主程序入口
    - 创建wayfare/main.py
    - 实现命令行参数解析（--workspace）
    - 实现所有组件的初始化流程
    - 实现IPC服务器（监听stdin，输出到stdout）
    - 添加启动和关闭日志
    - _Requirements: 所有需求的集成_
  
  - [x] 11.2 创建依赖管理文件
    - 创建requirements.txt（生产依赖）
    - 创建requirements-dev.txt（开发依赖）
    - 指定所有依赖的版本号
    - 添加nanobot框架依赖
    - _Requirements: 部署需求_
  
  - [x] 11.3 配置PyInstaller打包
    - 创建build.spec文件
    - 配置ONNX模型和配置文件的打包
    - 配置hiddenimports（onnxruntime、qdrant_client等）
    - 测试打包后的可执行文件
    - _Requirements: 部署需求_
  
  - [x] 11.4 创建开发环境设置脚本
    - 创建setup.sh（Linux/Mac）和setup.bat（Windows）
    - 自动创建虚拟环境
    - 自动安装依赖
    - 自动下载ONNX模型
    - 自动启动Qdrant Docker容器
    - _Requirements: 开发体验_
  
  - [x] 11.5 编写README和开发文档
    - 创建README.md，包含项目介绍和快速开始
    - 创建DEVELOPMENT.md，包含开发环境设置
    - 创建API.md，包含IPC接口文档
    - 创建ARCHITECTURE.md，包含架构说明
    - _Requirements: 文档需求_
  
  - [x] 11.6 配置CI/CD流程
    - 创建.github/workflows/test.yml
    - 配置单元测试、属性测试、集成测试的自动运行
    - 配置代码覆盖率报告上传
    - 配置代码质量检查（black、mypy、pylint）
    - _Requirements: 质量保证_
  
  - [x] 11.7 创建示例配置和测试数据
    - 创建config.example.yaml示例配置文件
    - 创建tests/fixtures/sample_documents/目录
    - 添加示例PDF和Markdown文件
    - 创建mock_data.py生成测试数据
    - _Requirements: 测试需求_

- [x] 12. Final Checkpoint - 完整系统验证
  - 运行完整的测试套件，确保所有功能正常工作
  - 测试打包后的可执行文件
  - 验证与Tauri前端的IPC通信
  - 询问用户是否有问题或需要调整

## Notes

- 任务标记`*`的为可选任务，可以跳过以加快MVP开发
- 每个任务都引用了具体的需求编号，确保可追溯性
- Checkpoint任务用于阶段性验证，确保增量开发的质量
- 属性测试验证通用的正确性属性，单元测试验证具体示例和边缘情况
- 集成测试验证端到端的用户流程
- 性能优化任务标记为可选，可以在MVP后期或后续版本实现
