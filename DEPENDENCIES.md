# WayFare MVP Backend - 依赖管理指南

## 概述

本项目使用两种依赖管理方式：
1. **pyproject.toml** - 用于包开发和分发
2. **requirements.txt / requirements-dev.txt** - 用于部署和环境复制

## 快速开始

### 生产环境安装

```bash
# 使用requirements.txt
pip install -r requirements.txt

# 或使用pyproject.toml
pip install -e .
```

### 开发环境安装

```bash
# 使用requirements-dev.txt（推荐）
pip install -r requirements-dev.txt

# 或使用pyproject.toml
pip install -e ".[dev]"
```

### 验证依赖安装

运行依赖验证脚本：

```bash
python verify_dependencies.py
```

## 依赖分类

### 核心框架依赖（复用nanobot）

| 包名 | 版本 | 用途 |
|------|------|------|
| typer | >=0.20.0,<1.0.0 | CLI框架 |
| litellm | >=1.81.5,<2.0.0 | LLM统一接口 |
| pydantic | >=2.12.0,<3.0.0 | 数据验证 |
| pydantic-settings | >=2.12.0,<3.0.0 | 配置管理 |
| loguru | >=0.7.3,<1.0.0 | 日志系统 |
| openai | >=2.8.0 | OpenAI API客户端 |

### 数据存储

| 包名 | 版本 | 用途 |
|------|------|------|
| aiosqlite | >=0.20.0,<1.0.0 | 异步SQLite数据库 |

### 文档解析

| 包名 | 版本 | 用途 |
|------|------|------|
| PyMuPDF | >=1.24.0,<2.0.0 | PDF文档解析 |
| markdown-it-py | >=3.0.0,<4.0.0 | Markdown文档解析 |

### 向量化与向量存储

| 包名 | 版本 | 用途 |
|------|------|------|
| onnxruntime | >=1.20.0,<2.0.0 | ONNX模型推理 |
| transformers | >=4.50.0,<5.0.0 | Tokenizer支持 |
| qdrant-client | >=1.12.0,<2.0.0 | Qdrant向量数据库客户端 |
| numpy | >=1.26.0,<2.0.0 | 数值计算 |

### 其他依赖

| 包名 | 版本 | 用途 |
|------|------|------|
| blake3 | >=0.4.0,<1.0.0 | BLAKE3哈希算法 |
| pyyaml | >=6.0.0,<7.0.0 | YAML配置文件解析 |
| httpx | >=0.28.0,<1.0.0 | 异步HTTP客户端 |

### 开发依赖

| 包名 | 版本 | 用途 |
|------|------|------|
| pytest | >=9.0.0,<10.0.0 | 单元测试框架 |
| pytest-asyncio | >=1.3.0,<2.0.0 | 异步测试支持 |
| pytest-cov | >=6.0.0,<7.0.0 | 测试覆盖率 |
| hypothesis | >=6.130.0,<7.0.0 | 属性测试框架 |
| ruff | >=0.1.0,<1.0.0 | Python linter |
| black | >=24.0.0,<25.0.0 | 代码格式化 |
| mypy | >=1.14.0,<2.0.0 | 静态类型检查 |
| pylint | >=3.3.0,<4.0.0 | 代码质量检查 |
| coverage | >=7.6.0,<8.0.0 | 代码覆盖率工具 |
| ipython | >=8.30.0,<9.0.0 | 增强的Python shell |

## 系统要求

- **Python版本**: >= 3.11
- **操作系统**: Linux, macOS, Windows
- **外部服务**: Qdrant向量数据库（可选，用于向量存储）

## 外部依赖

### ONNX模型

项目使用BAAI/bge-small-zh-v1.5 ONNX模型进行文本向量化。需要单独下载：

```bash
# 下载模型（示例）
mkdir -p models
cd models
# 从HuggingFace下载ONNX模型文件
# https://huggingface.co/BAAI/bge-small-zh-v1.5
```

### Qdrant向量数据库

使用Docker启动Qdrant服务：

```bash
docker run -p 6333:6333 qdrant/qdrant
```

或使用docker-compose（如果项目包含docker-compose.yml）：

```bash
docker-compose up -d qdrant
```

## 虚拟环境设置

### 使用venv

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安装依赖
pip install -r requirements-dev.txt
```

### 使用conda

```bash
# 创建conda环境
conda create -n wayfare python=3.11

# 激活环境
conda activate wayfare

# 安装依赖
pip install -r requirements-dev.txt
```

## Docker部署

### Dockerfile示例

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 运行应用
CMD ["python", "wayfare/main.py"]
```

### 构建和运行

```bash
# 构建镜像
docker build -t wayfare-backend .

# 运行容器
docker run -p 8000:8000 wayfare-backend
```

## 依赖更新

### 更新所有依赖

```bash
# 更新到最新兼容版本
pip install --upgrade -r requirements.txt
```

### 生成锁定文件

```bash
# 生成精确的依赖版本
pip freeze > requirements.lock
```

### 检查过期依赖

```bash
pip list --outdated
```

## 常见问题

### Q: PyMuPDF安装失败

**A**: PyMuPDF可能需要系统级别的依赖。在Linux上：

```bash
sudo apt-get install libmupdf-dev
```

在macOS上：

```bash
brew install mupdf
```

### Q: onnxruntime性能问题

**A**: 默认使用CPU推理。如果需要GPU加速，安装GPU版本：

```bash
pip install onnxruntime-gpu
```

### Q: transformers警告"PyTorch was not found"

**A**: 这是正常的。项目只使用transformers的tokenizer功能，不需要PyTorch。

### Q: Qdrant连接失败

**A**: 确保Qdrant服务正在运行：

```bash
# 检查Qdrant是否运行
curl http://localhost:6333/health

# 如果未运行，启动Qdrant
docker run -p 6333:6333 qdrant/qdrant
```

## 依赖安全

### 检查安全漏洞

```bash
# 使用pip-audit
pip install pip-audit
pip-audit

# 或使用safety
pip install safety
safety check
```

### 定期更新

建议每月检查并更新依赖，特别是安全补丁：

```bash
pip list --outdated
pip install --upgrade <package-name>
```

## CI/CD集成

### GitHub Actions示例

```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt
      - name: Verify dependencies
        run: |
          python verify_dependencies.py
      - name: Run tests
        run: |
          pytest
```

## 贡献指南

如果需要添加新的依赖：

1. 在pyproject.toml中添加依赖
2. 同步更新requirements.txt或requirements-dev.txt
3. 更新本文档的依赖列表
4. 运行`python verify_dependencies.py`确保依赖可用
5. 提交PR并说明添加依赖的原因

## 许可证

所有依赖的许可证信息请参考各自的项目页面。本项目使用MIT许可证。

## 支持

如有依赖相关问题，请：
1. 查看本文档的常见问题部分
2. 运行`python verify_dependencies.py`诊断问题
3. 在项目issue中报告问题
