"""BehaviorAnalyzer使用示例

演示如何使用BehaviorAnalyzer记录和分析用户学习行为。

使用场景：
1. 记录用户浏览、选择、滚动行为
2. 查询特定页面的行为数据
3. 检测是否需要主动干预
4. 获取页面统计信息
"""

import asyncio
from wayfare.behavior_analyzer import BehaviorAnalyzer
from wayfare.db import SQLiteDB


async def example_basic_usage():
    """基础使用示例"""
    print("=== 基础使用示例 ===\n")
    
    # 初始化数据库和分析器
    db = SQLiteDB(".wayfare/example.db")
    await db.initialize()
    
    analyzer = BehaviorAnalyzer(db, intervention_threshold=120)
    
    # 1. 记录页面浏览
    print("1. 记录页面浏览事件")
    event = await analyzer.record_behavior(
        doc_hash="doc_abc123",
        page=1,
        event_type="page_view"
    )
    print(f"   事件ID: {event.id}")
    print(f"   时间戳: {event.timestamp}\n")
    
    # 2. 记录文本选择
    print("2. 记录文本选择事件")
    event = await analyzer.record_behavior(
        doc_hash="doc_abc123",
        page=1,
        event_type="text_select",
        metadata={"selected_text": "费曼技巧是一种学习方法"}
    )
    print(f"   选中文本: {event.metadata['selected_text']}\n")
    
    # 3. 记录滚动
    print("3. 记录滚动事件")
    event = await analyzer.record_behavior(
        doc_hash="doc_abc123",
        page=1,
        event_type="scroll",
        metadata={"scroll_position": 0.5}
    )
    print(f"   滚动位置: {event.metadata['scroll_position']}\n")


async def example_query_behaviors():
    """查询行为数据示例"""
    print("=== 查询行为数据示例 ===\n")
    
    db = SQLiteDB(".wayfare/example.db")
    await db.initialize()
    analyzer = BehaviorAnalyzer(db)
    
    # 记录一些行为
    await analyzer.record_behavior("doc_abc123", 1, "page_view")
    await analyzer.record_behavior("doc_abc123", 1, "text_select")
    await analyzer.record_behavior("doc_abc123", 2, "page_view")
    await analyzer.record_behavior("doc_abc123", 2, "scroll")
    
    # 1. 查询所有行为
    print("1. 查询文档的所有行为")
    behaviors = await analyzer.get_behaviors("doc_abc123")
    print(f"   总共 {len(behaviors)} 个行为事件\n")
    
    # 2. 按页码过滤
    print("2. 查询第1页的行为")
    page1_behaviors = await analyzer.get_behaviors("doc_abc123", page=1)
    for b in page1_behaviors:
        print(f"   - {b.event_type} at {b.timestamp}")
    print()
    
    # 3. 按事件类型过滤
    print("3. 查询所有文本选择事件")
    select_behaviors = await analyzer.get_behaviors(
        "doc_abc123",
        event_type="text_select"
    )
    print(f"   找到 {len(select_behaviors)} 个文本选择事件\n")


async def example_intervention_trigger():
    """主动干预触发示例"""
    print("=== 主动干预触发示例 ===\n")
    
    db = SQLiteDB(".wayfare/example.db")
    await db.initialize()
    
    # 设置较短的阈值用于演示（5秒）
    analyzer = BehaviorAnalyzer(db, intervention_threshold=5)
    
    # 记录页面浏览
    print("1. 用户打开页面")
    await analyzer.record_behavior("doc_abc123", 1, "page_view")
    
    # 检查当前停留时间
    print("2. 检查当前停留时间")
    dwell_time = analyzer.get_current_dwell_time("doc_abc123", 1)
    print(f"   当前停留: {dwell_time:.1f} 秒\n")
    
    # 等待一段时间
    print("3. 等待3秒...")
    await asyncio.sleep(3)
    
    # 再次检查
    dwell_time = analyzer.get_current_dwell_time("doc_abc123", 1)
    print(f"   当前停留: {dwell_time:.1f} 秒")
    
    # 检查是否触发干预
    should_trigger = await analyzer.check_intervention_trigger("doc_abc123", 1)
    print(f"   是否触发干预: {should_trigger}\n")
    
    # 再等待3秒
    print("4. 再等待3秒...")
    await asyncio.sleep(3)
    
    # 再次检查
    dwell_time = analyzer.get_current_dwell_time("doc_abc123", 1)
    print(f"   当前停留: {dwell_time:.1f} 秒")
    
    should_trigger = await analyzer.check_intervention_trigger("doc_abc123", 1)
    print(f"   是否触发干预: {should_trigger}")
    
    if should_trigger:
        print("   ✓ 触发主动干预！可以向用户推送帮助信息\n")


async def example_page_statistics():
    """页面统计示例"""
    print("=== 页面统计示例 ===\n")
    
    db = SQLiteDB(".wayfare/example.db")
    await db.initialize()
    analyzer = BehaviorAnalyzer(db)
    
    # 模拟用户行为
    print("1. 模拟用户在第1页的学习行为")
    await analyzer.record_behavior("doc_abc123", 1, "page_view")
    await asyncio.sleep(1)
    
    await analyzer.record_behavior("doc_abc123", 1, "text_select",
                                   metadata={"selected_text": "概念A"})
    await asyncio.sleep(1)
    
    await analyzer.record_behavior("doc_abc123", 1, "text_select",
                                   metadata={"selected_text": "概念B"})
    await asyncio.sleep(1)
    
    await analyzer.record_behavior("doc_abc123", 1, "scroll",
                                   metadata={"scroll_position": 0.3})
    await asyncio.sleep(1)
    
    await analyzer.record_behavior("doc_abc123", 1, "page_view")
    
    # 获取统计信息
    print("\n2. 获取页面统计信息")
    stats = await analyzer.get_page_statistics("doc_abc123", 1)
    
    print(f"   页面浏览次数: {stats.total_views}")
    print(f"   文本选择次数: {stats.total_selects}")
    print(f"   滚动次数: {stats.total_scrolls}")
    print(f"   平均停留时间: {stats.avg_duration:.1f} 秒\n")


async def example_multiple_pages():
    """多页面跟踪示例"""
    print("=== 多页面跟踪示例 ===\n")
    
    db = SQLiteDB(".wayfare/example.db")
    await db.initialize()
    analyzer = BehaviorAnalyzer(db, intervention_threshold=3)
    
    # 用户浏览多个页面
    print("1. 用户浏览多个页面")
    await analyzer.record_behavior("doc_abc123", 1, "page_view")
    print("   - 打开第1页")
    
    await asyncio.sleep(2)
    
    await analyzer.record_behavior("doc_abc123", 2, "page_view")
    print("   - 打开第2页")
    
    await asyncio.sleep(2)
    
    await analyzer.record_behavior("doc_abc123", 3, "page_view")
    print("   - 打开第3页\n")
    
    # 检查各页面的停留时间
    print("2. 检查各页面的停留时间")
    for page in [1, 2, 3]:
        dwell_time = analyzer.get_current_dwell_time("doc_abc123", page)
        print(f"   第{page}页: {dwell_time:.1f} 秒")
    
    print()
    
    # 等待触发
    await asyncio.sleep(2)
    
    # 检查哪些页面需要干预
    print("3. 检查哪些页面需要干预")
    for page in [1, 2, 3]:
        should_trigger = await analyzer.check_intervention_trigger("doc_abc123", page)
        if should_trigger:
            print(f"   ✓ 第{page}页需要干预")
        else:
            print(f"   - 第{page}页不需要干预")
    
    print()


async def example_reset_timer():
    """重置计时器示例"""
    print("=== 重置计时器示例 ===\n")
    
    db = SQLiteDB(".wayfare/example.db")
    await db.initialize()
    analyzer = BehaviorAnalyzer(db, intervention_threshold=5)
    
    # 记录页面浏览
    print("1. 用户打开页面")
    await analyzer.record_behavior("doc_abc123", 1, "page_view")
    
    await asyncio.sleep(3)
    
    dwell_time = analyzer.get_current_dwell_time("doc_abc123", 1)
    print(f"   停留时间: {dwell_time:.1f} 秒\n")
    
    # 用户表示理解，重置计时器
    print("2. 用户表示已理解，重置计时器")
    analyzer.reset_page_timer("doc_abc123", 1)
    
    dwell_time = analyzer.get_current_dwell_time("doc_abc123", 1)
    print(f"   停留时间: {dwell_time:.1f} 秒")
    print("   ✓ 计时器已重置\n")


async def example_complete_workflow():
    """完整工作流示例"""
    print("=== 完整工作流示例 ===\n")
    
    db = SQLiteDB(".wayfare/example.db")
    await db.initialize()
    analyzer = BehaviorAnalyzer(db, intervention_threshold=5)
    
    doc_hash = "learning_doc_001"
    
    print("场景：用户正在学习一篇文档\n")
    
    # 第1页
    print("1. 用户打开第1页")
    await analyzer.record_behavior(doc_hash, 1, "page_view")
    
    await asyncio.sleep(2)
    
    print("2. 用户选择了一段文本")
    await analyzer.record_behavior(
        doc_hash, 1, "text_select",
        metadata={"selected_text": "机器学习的定义"}
    )
    
    await asyncio.sleep(2)
    
    print("3. 用户滚动页面")
    await analyzer.record_behavior(
        doc_hash, 1, "scroll",
        metadata={"scroll_position": 0.6}
    )
    
    await asyncio.sleep(2)
    
    # 检查是否需要干预
    print("\n4. 检查是否需要主动干预")
    should_trigger = await analyzer.check_intervention_trigger(doc_hash, 1)
    
    if should_trigger:
        print("   ✓ 用户在此页停留较久，触发主动干预")
        print("   → 可以推送：'需要帮助理解这部分内容吗？'\n")
    
    # 获取统计
    print("5. 获取学习行为统计")
    stats = await analyzer.get_page_statistics(doc_hash, 1)
    print(f"   - 浏览次数: {stats.total_views}")
    print(f"   - 选择次数: {stats.total_selects}")
    print(f"   - 滚动次数: {stats.total_scrolls}")
    print(f"   - 平均停留: {stats.avg_duration:.1f}秒\n")
    
    # 查询所有行为
    print("6. 查询所有行为记录")
    behaviors = await analyzer.get_behaviors(doc_hash, page=1)
    for i, b in enumerate(behaviors, 1):
        print(f"   {i}. {b.event_type} - {b.timestamp}")
    
    print()


async def example_intervention_push():
    """主动干预推送示例"""
    print("=== 主动干预推送示例 ===\n")
    
    db = SQLiteDB(".wayfare/example.db")
    await db.initialize()
    analyzer = BehaviorAnalyzer(db, intervention_threshold=5)
    
    doc_hash = "learning_doc_002"
    
    print("场景：演示主动干预推送机制\n")
    
    # 模拟用户行为
    print("1. 用户打开页面并进行学习")
    await analyzer.record_behavior(doc_hash, 1, "page_view")
    await asyncio.sleep(1)
    
    await analyzer.record_behavior(
        doc_hash, 1, "text_select",
        metadata={"selected_text": "深度学习"}
    )
    await asyncio.sleep(1)
    
    await analyzer.record_behavior(
        doc_hash, 1, "scroll",
        metadata={"scroll_position": 0.4}
    )
    
    print("   ✓ 记录了3个行为事件\n")
    
    # 创建模拟的IPC Handler
    class MockIPCHandler:
        def __init__(self):
            self.notifications = []
        
        async def _send_notification(self, data):
            self.notifications.append(data)
            print(f"   📤 发送通知: {data['type']}")
            print(f"      消息: {data['message']}")
            print(f"      统计: 浏览{data['statistics']['totalViews']}次, "
                  f"选择{data['statistics']['totalSelects']}次, "
                  f"滚动{data['statistics']['totalScrolls']}次")
    
    mock_handler = MockIPCHandler()
    
    # 发送干预推送
    print("2. 发送主动干预推送")
    await analyzer.send_intervention(doc_hash, 1, ipc_handler=mock_handler)
    
    print(f"\n   ✓ 共发送了 {len(mock_handler.notifications)} 条通知\n")
    
    # 不提供IPC Handler的情况
    print("3. 不提供IPC Handler时（仅记录日志）")
    await analyzer.send_intervention(doc_hash, 1, ipc_handler=None)
    print("   ✓ 干预已记录到日志\n")


async def main():
    """运行所有示例"""
    examples = [
        ("基础使用", example_basic_usage),
        ("查询行为数据", example_query_behaviors),
        ("主动干预触发", example_intervention_trigger),
        ("页面统计", example_page_statistics),
        ("多页面跟踪", example_multiple_pages),
        ("重置计时器", example_reset_timer),
        ("完整工作流", example_complete_workflow),
        ("主动干预推送", example_intervention_push),
    ]
    
    for name, func in examples:
        try:
            await func()
            print("-" * 60)
            print()
        except Exception as e:
            print(f"❌ {name} 示例出错: {e}\n")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
