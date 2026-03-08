# BehaviorAnalyzer模块文档

## 概述

BehaviorAnalyzer是WayFare后端的用户行为分析模块，负责记录和分析用户的学习行为，并在适当时机触发主动干预。

**Requirements**: 6.1, 6.2

## 核心功能

1. **行为记录**: 记录用户的页面浏览、文本选择、滚动等行为
2. **数据存储**: 将行为数据持久化到SQLite数据库
3. **主动干预**: 基于停留时间检测，触发主动干预信号
4. **行为查询**: 支持按文档、页码、事件类型查询行为数据
5. **统计分析**: 提供页面级别的行为统计信息

## 架构设计

### 数据模型

#### BehaviorEvent
```python
@dataclass
class BehaviorEvent:
    id: str                      # 事件唯一标识（UUID）
    doc_hash: str                # 文档hash
    page: int                    # 页码
    event_type: str              # 事件类型
    timestamp: str               # 时间戳（ISO 8601格式）
    metadata: Dict[str, Any]     # 额外元数据
```

**支持的事件类型**:
- `page_view`: 页面浏览事件
- `text_select`: 文本选择事件
- `scroll`: 滚动事件

#### BehaviorStatistics
```python
@dataclass
class BehaviorStatistics:
    total_views: int             # 总浏览次数
    total_selects: int           # 总选择次数
    total_scrolls: int           # 总滚动次数
    avg_duration: float          # 平均停留时间（秒）
```

### 数据库Schema

```sql
CREATE TABLE behaviors (
    id TEXT PRIMARY KEY,
    doc_hash TEXT NOT NULL,
    page INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    metadata TEXT,  -- JSON格式
    FOREIGN KEY (doc_hash) REFERENCES documents(hash)
);

CREATE INDEX idx_behaviors_doc_page ON behaviors(doc_hash, page);
CREATE INDEX idx_behaviors_timestamp ON behaviors(timestamp);
CREATE INDEX idx_behaviors_type ON behaviors(event_type);
```

## API接口

### 初始化

```python
from wayfare.behavior_analyzer import BehaviorAnalyzer
from wayfare.db import SQLiteDB

# 创建数据库实例
db = SQLiteDB(".wayfare/wayfare.db")
await db.initialize()

# 创建分析器（默认阈值120秒）
analyzer = BehaviorAnalyzer(db, intervention_threshold=120)
```

### 记录行为

```python
# 记录页面浏览
event = await analyzer.record_behavior(
    doc_hash="doc_abc123",
    page=1,
    event_type="page_view"
)

# 记录文本选择（带元数据）
event = await analyzer.record_behavior(
    doc_hash="doc_abc123",
    page=1,
    event_type="text_select",
    metadata={"selected_text": "重要概念"}
)

# 记录滚动
event = await analyzer.record_behavior(
    doc_hash="doc_abc123",
    page=1,
    event_type="scroll",
    metadata={"scroll_position": 0.5}
)
```

### 查询行为

```python
# 查询文档的所有行为
behaviors = await analyzer.get_behaviors("doc_abc123")

# 按页码过滤
behaviors = await analyzer.get_behaviors("doc_abc123", page=1)

# 按事件类型过滤
behaviors = await analyzer.get_behaviors(
    "doc_abc123",
    event_type="text_select"
)

# 组合过滤
behaviors = await analyzer.get_behaviors(
    "doc_abc123",
    page=1,
    event_type="page_view"
)
```

### 主动干预检测

```python
# 检查是否应该触发干预
should_trigger = await analyzer.check_intervention_trigger(
    doc_hash="doc_abc123",
    page=1
)

if should_trigger:
    # 向用户推送帮助信息
    print("用户在此页停留较久，可能需要帮助")

# 获取当前停留时间
dwell_time = analyzer.get_current_dwell_time("doc_abc123", 1)
print(f"当前停留: {dwell_time:.1f} 秒")

# 手动重置计时器
analyzer.reset_page_timer("doc_abc123", 1)
```

### 统计分析

```python
# 获取页面统计信息
stats = await analyzer.get_page_statistics("doc_abc123", 1)

print(f"浏览次数: {stats.total_views}")
print(f"选择次数: {stats.total_selects}")
print(f"滚动次数: {stats.total_scrolls}")
print(f"平均停留: {stats.avg_duration:.1f}秒")
```

### 主动干预推送

```python
# 提供IPC Handler时，发送推送通知
await analyzer.send_intervention(
    doc_hash="doc_abc123",
    page=1,
    ipc_handler=ipc_handler  # IPCHandler实例
)

# 不提供IPC Handler时，仅记录日志
await analyzer.send_intervention(
    doc_hash="doc_abc123",
    page=1,
    ipc_handler=None
)
```

**干预消息格式**:
```json
{
    "type": "intervention",
    "docHash": "doc_abc123",
    "page": 1,
    "message": "您在第1页停留了较长时间，需要帮助吗？",
    "statistics": {
        "totalViews": 2,
        "totalSelects": 3,
        "totalScrolls": 1,
        "avgDuration": 45.2
    }
}
```

**松耦合设计**:
- 如果提供了`ipc_handler`，则通过IPC向前端发送推送
- 如果未提供，则仅记录日志（用于测试或独立使用）

**Requirements**: 6.4 - THE Behavior_Analyzer SHALL 通过IPC向前端发送主动消息推送

## 使用场景

### 场景1: 基础行为跟踪

```python
# 用户打开文档
await analyzer.record_behavior("doc_001", 1, "page_view")

# 用户选择文本
await analyzer.record_behavior(
    "doc_001", 1, "text_select",
    metadata={"selected_text": "机器学习"}
)

# 用户滚动页面
await analyzer.record_behavior(
    "doc_001", 1, "scroll",
    metadata={"scroll_position": 0.3}
)
```

### 场景2: 主动干预触发

```python
# 记录页面浏览
await analyzer.record_behavior("doc_001", 1, "page_view")

# 定期检查是否需要干预
while True:
    await asyncio.sleep(30)  # 每30秒检查一次
    
    if await analyzer.check_intervention_trigger("doc_001", 1):
        # 触发主动干预
        await send_help_message("需要帮助理解这部分内容吗？")
        break
```

### 场景3: 学习行为分析

```python
# 获取用户在某页的学习行为
behaviors = await analyzer.get_behaviors("doc_001", page=1)

# 分析行为模式
text_selects = [b for b in behaviors if b.event_type == "text_select"]
selected_texts = [b.metadata.get("selected_text") for b in text_selects]

print(f"用户选择了 {len(selected_texts)} 段文本:")
for text in selected_texts:
    print(f"  - {text}")

# 获取统计信息
stats = await analyzer.get_page_statistics("doc_001", 1)
if stats.total_selects > 5:
    print("用户频繁选择文本，可能对此页内容感兴趣")
```

### 场景4: 多页面跟踪

```python
# 用户浏览多个页面
for page in [1, 2, 3]:
    await analyzer.record_behavior("doc_001", page, "page_view")
    await asyncio.sleep(60)  # 模拟停留

# 检查哪些页面需要干预
for page in [1, 2, 3]:
    if await analyzer.check_intervention_trigger("doc_001", page):
        print(f"第{page}页需要干预")
```

## 设计决策

### 1. 为什么使用内存跟踪停留时间？

**决策**: 使用`page_start_times`字典在内存中跟踪停留时间，而不是每次都查询数据库。

**理由**:
- 性能: 避免频繁的数据库查询
- 实时性: 可以实时计算当前停留时间
- 简单性: 逻辑清晰，易于维护

**权衡**: 进程重启会丢失跟踪状态，但这对MVP阶段可接受。

### 2. 为什么使用简单的阈值触发？

**决策**: MVP阶段仅基于停留时间阈值触发干预，不实现复杂的机器学习模型。

**理由**:
- 快速实现: 满足MVP需求
- 可解释性: 用户可以理解触发逻辑
- 可扩展性: 未来可以添加更复杂的分析

### 3. 为什么支持元数据字段？

**决策**: 每个行为事件都支持可选的`metadata`字段存储额外信息。

**理由**:
- 灵活性: 不同事件类型可以存储不同的数据
- 扩展性: 未来可以添加新的元数据字段
- 向后兼容: 不影响现有代码

## 性能考虑

### 数据库索引

为了优化查询性能，创建了以下索引：

```sql
-- 按文档和页码查询
CREATE INDEX idx_behaviors_doc_page ON behaviors(doc_hash, page);

-- 按时间排序
CREATE INDEX idx_behaviors_timestamp ON behaviors(timestamp);

-- 按事件类型过滤
CREATE INDEX idx_behaviors_type ON behaviors(event_type);
```

### 批量操作

对于高频行为记录，建议：

1. 使用异步操作避免阻塞
2. 考虑批量插入（未来优化）
3. 定期清理旧数据

### 内存管理

`page_start_times`字典会随着用户浏览增长，建议：

1. 定期清理已触发的页面
2. 限制跟踪的最大页面数
3. 进程重启时自动清空

## 测试

### 运行单元测试

```bash
pytest tests/wayfare/test_behavior_analyzer.py -v
```

### 测试覆盖

- ✅ 记录各类行为事件
- ✅ 查询和过滤行为数据
- ✅ 主动干预触发逻辑
- ✅ 页面统计计算
- ✅ 计时器管理
- ✅ 边界情况处理
- ✅ 并发操作

### 运行示例

```bash
python examples/behavior_analyzer_usage_example.py
```

## 未来扩展

### 短期（MVP后）

1. **行为模式识别**: 识别用户的学习模式（快速浏览 vs 深度学习）
2. **个性化阈值**: 根据用户历史行为调整干预阈值
3. **批量操作**: 支持批量记录行为事件

### 长期

1. **机器学习模型**: 使用ML预测用户需要帮助的时机
2. **跨文档分析**: 分析用户在多个文档间的学习路径
3. **学习效果评估**: 结合批注使用情况评估学习效果
4. **实时推荐**: 基于行为实时推荐相关内容

## 常见问题

### Q: 如何调整干预阈值？

A: 在初始化时设置`intervention_threshold`参数：

```python
# 设置为60秒
analyzer = BehaviorAnalyzer(db, intervention_threshold=60)
```

### Q: 如何避免重复触发干预？

A: `check_intervention_trigger`方法在触发后会自动重置计时器，避免重复触发。如果需要手动重置，使用`reset_page_timer`方法。

### Q: 元数据可以存储什么类型的数据？

A: 元数据会被序列化为JSON，支持字典、列表、字符串、数字等JSON兼容类型。

### Q: 如何处理进程重启？

A: 进程重启会丢失内存中的计时器状态，但历史行为数据仍保存在数据库中。重启后会重新开始跟踪。

### Q: 如何清理旧的行为数据？

A: 可以使用数据库的DELETE操作清理旧数据：

```python
# 删除文档的所有行为数据
await db.delete_behaviors("doc_hash")
```

## 相关模块

- `wayfare.db`: SQLite数据库层，提供数据持久化
- `wayfare.ipc`: IPC通信层，接收前端发送的行为数据
- `wayfare.annotation_generator`: 批注生成器，可以基于行为统计生成个性化批注

## 参考资料

- [Requirements 6.1, 6.2](../../../.kiro/specs/wayfare-mvp-backend/requirements.md)
- [Design Document](../../../.kiro/specs/wayfare-mvp-backend/design.md)
- [Database Schema](./README_DB.md)
