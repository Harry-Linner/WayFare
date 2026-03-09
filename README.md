# WayFare - AI 驱动的学习助手

WayFare 是一个智能学习助手应用，使用 Tauri + React + Python 构建。

## 快速启动

```bash
# 1. 初始化数据库
python init_db_simple.py

# 2. 启动后端（新终端）
python start_notification_backend.py --enable-test

# 3. 启动前端（另一个新终端）
npm run tauri:dev
```

详细说明请查看 [START_HERE.md](START_HERE.md) 或 [QUICK_START.md](QUICK_START.md)

## 项目结构

```
WayFare/
├── src/                    # React 前端代码
├── src-tauri/             # Tauri Rust 后端
├── wayfare/               # Python 核心模块
├── examples/              # 使用示例
├── tests/                 # 测试文件
└── docs/                  # 文档
```

## 主要功能

- 📚 文档解析和分析
- 🤖 AI 驱动的学习建议
- 📊 学习进度追踪
- 🔔 智能通知系统
- 📝 笔记和标注管理

## 技术栈

- **前端**: React 19 + TypeScript + Vite + Tailwind CSS
- **桌面**: Tauri 2.0 (Rust)
- **后端**: Python 3.8+ + Flask
- **数据库**: SQLite
- **AI**: 支持多种 LLM 提供商

## 文档

- [快速启动](START_HERE.md) - 3 分钟快速上手
- [开发指南](DEVELOPMENT.md) - 开发环境设置
- [架构文档](ARCHITECTURE.md) - 系统架构说明
- [API 文档](API.md) - API 接口说明
- [交接说明](HANDOVER_NOTES.md) - 项目交接文档

## 依赖要求

- Python 3.8+
- Node.js 18+
- Rust 1.70+

## 开发

```bash
# 安装依赖
npm install
pip install -r requirements.txt

# 开发模式
npm run tauri:dev

# 构建
npm run tauri:build
```

## 测试

```bash
# Python 测试
pytest

# 通知系统测试
python test_notification_system.py
python test_notification_api.py
```

## 许可证

[添加许可证信息]

## 贡献

欢迎贡献！请查看 [DEVELOPMENT.md](DEVELOPMENT.md) 了解开发指南。

## 问题反馈

如果遇到问题，请查看 [HANDOVER_NOTES.md](HANDOVER_NOTES.md) 中的常见问题部分。
