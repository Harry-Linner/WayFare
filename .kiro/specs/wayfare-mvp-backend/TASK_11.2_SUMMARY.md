# Task 11.2 Summary: 创建依赖管理文件

## 任务概述
创建了WayFare MVP Backend项目的依赖管理文件，包括生产环境依赖（requirements.txt）和开发环境依赖（requirements-dev.txt）。

## 完成的工作

### 1. 创建 requirements.txt（生产依赖）
包含以下依赖类别：

#### 核心框架依赖（复用nanobot）
- `typer>=0.20.0,<1.0.0` - CLI框架
- `litellm>=1.81.5,<2.0.0` - LLM统一接口
- `pydantic>=2.12.0,<3.0.0` - 数据验证
- `pydantic-settings>=2.12.0,<3.0.0` - 配置管理
- `loguru>=0.7.3,<1.0.0` - 日志系统
- `openai>=2.8.0` - OpenAI API客户端

#### 数据库
- `aiosqlite>=0.20.0,<1.0.0` - 异步SQLite数据库

#### 文档解析
- `PyMuPDF>=1.24.0,<2.0.0` - PDF解析（fitz）
- `markdown-it-py>=3.0.0,<4.0.0` - Markdown解析

#### 向量化与向量存储
- `onnxruntime>=1.20.0,<2.0.0` - ONNX模型推理
- `transformers>=4.50.0,<5.0.0` - Tokenizer支持
- `qdrant-client>=1.12.0,<2.0.0` - Qdrant向量数据库客户端
- `numpy>=1.26.0,<2.0.0` - 数值计算

#### 哈希算法
- `blake3>=0.4.0,<1.0.0` - BLAKE3哈希算法

#### 配置文件
- `pyyaml>=6.0.0,<7.0.0` - YAML配置文件解析

#### HTTP客户端
- `httpx>=0.28.0,<1.0.0` - 异步HTTP客户端（用于LLM API调用）

#### 异步支持
- `asyncio-compat>=0.1.0` - Python 3.11及以下版本的异步兼容性

### 2. 创建 requirements-dev.txt（开发依赖）
包含所有生产依赖（通过 `-r requirements.txt` 引用）以及：

#### 测试框架
- `pytest>=9.0.0,<10.0.0` - 单元测试框架
- `pytest-asyncio>=1.3.0,<2.0.0` - 异步测试支持
- `pytest-cov>=6.0.0,<7.0.0` - 测试覆盖率

#### 属性测试
- `hypothesis>=6.130.0,<7.0.0` - 属性测试框架

#### 代码质量工具
- `ruff>=0.1.0,<1.0.0` - 快速Python linter
- `black>=24.0.0,<25.0.0` - 代码格式化
- `mypy>=1.14.0,<2.0.0` - 静态类型检查
- `pylint>=3.3.0,<4.0.0` - 代码质量检查

#### 类型存根
- `types-PyYAML>=6.0.0,<7.0.0` - PyYAML类型提示
- `types-aiofiles>=24.0.0,<25.0.0` - aiofiles类型提示

#### 测试覆盖率
- `coverage>=7.6.0,<8.0.0` - 代码覆盖率工具

#### 开发工具
- `ipython>=8.30.0,<9.0.0` - 增强的Python交互式shell

## 依赖版本策略

### 版本约束原则
1. **使用范围约束**: 采用 `>=x.y.z,<major+1.0.0` 格式
   - 允许小版本和补丁版本更新
   - 防止破坏性的主版本更新

2. **与nanobot保持一致**: 核心依赖版本与nanobot框架保持一致
   - 确保兼容性
   - 便于复用nanobot组件

3. **最小版本要求**: 指定已测试的最小版本
   - 确保功能可用性
   - 避免已知的bug

## 关键依赖说明

### nanobot框架复用
项目最大化复用nanobot框架的能力：
- **LLMProvider**: 通过litellm和openai实现
- **配置系统**: 通过pydantic和pydantic-settings实现
- **日志系统**: 通过loguru实现

### 文档处理
- **PyMuPDF**: 用于PDF文档解析，提取文本、页码和边界框
- **markdown-it-py**: 用于Markdown文档解析

### 向量化系统
- **onnxruntime**: 本地ONNX模型推理，保护隐私
- **transformers**: 提供BAAI/bge-small-zh-v1.5的tokenizer
- **qdrant-client**: 连接Qdrant向量数据库

### 数据存储
- **aiosqlite**: 异步SQLite操作，支持文档元数据、片段、批注和行为数据存储
- **blake3**: 高性能哈希算法，用于文档唯一标识

## 安装说明

### 生产环境安装
```bash
pip install -r requirements.txt
```

### 开发环境安装
```bash
pip install -r requirements-dev.txt
```

### 使用pyproject.toml安装（推荐）
```bash
# 生产环境
pip install -e .

# 开发环境
pip install -e ".[dev]"
```

## 与pyproject.toml的关系

项目同时维护两种依赖管理方式：

1. **pyproject.toml**: 
   - 用于包开发和分发
   - 定义项目元数据和依赖
   - 支持可选依赖组（dev, matrix等）

2. **requirements.txt/requirements-dev.txt**:
   - 用于部署和环境复制
   - 提供精确的版本锁定
   - 便于CI/CD和Docker构建

## 部署建议

### Docker部署
在Dockerfile中使用：
```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

### 虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 依赖更新
定期更新依赖以获取安全补丁：
```bash
pip install --upgrade -r requirements.txt
```

## 验证依赖完整性

可以通过以下方式验证依赖是否满足项目需求：

```bash
# 检查依赖冲突
pip check

# 查看已安装的依赖
pip list

# 生成当前环境的精确依赖
pip freeze > requirements.lock
```

## 注意事项

1. **ONNX模型**: onnxruntime需要下载BAAI/bge-small-zh-v1.5的ONNX模型文件
2. **Qdrant服务**: 需要单独启动Qdrant向量数据库服务
3. **Python版本**: 项目要求Python >= 3.11
4. **系统依赖**: PyMuPDF可能需要系统级别的依赖（如libmupdf）

## 满足的需求

本任务满足以下需求：
- **部署需求**: 提供清晰的依赖列表，便于部署
- **开发需求**: 包含完整的开发工具链
- **nanobot复用**: 包含所有必要的nanobot框架依赖
- **文档处理**: 包含PDF和Markdown解析依赖
- **向量化**: 包含ONNX推理和向量存储依赖
- **测试**: 包含单元测试和属性测试框架

## 后续工作

1. 在CI/CD流程中集成依赖安装
2. 定期更新依赖版本
3. 监控依赖的安全漏洞
4. 考虑使用poetry或pipenv进行更高级的依赖管理
