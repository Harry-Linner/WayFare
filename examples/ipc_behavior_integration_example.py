"""
IPC Behavior Integration Example

演示IPC Handler与BehaviorAnalyzer的集成使用，展示完整的行为分析工作流。

这个示例展示了：
1. 如何通过IPC发送用户行为数据
2. 如何自动触发主动干预
3. 如何查询行为统计信息
"""

import asyncio
import json
import tempfile
from pathlib import Path

from wayfare.ipc import IPCHandler
from wayfare.behavior_analyzer import BehaviorAnalyzer
from wayfare.db import SQLiteDB


async def main():
    """主函数"""
    print("=" * 60)
    print("IPC Behavior Integration Example")
    print("=" * 60)
    
    # 1. 初始化组件
    print("\n1. 初始化组件...")
    
    # 创建临时数据库
    tmpdir = tempfile.mkdtemp()
    db_path = Path(tmpdir) / "wayfare.db"
    db = SQLiteDB(str(db_path))
    await db.initialize()
    print(f"   ✓ 数据库初始化完成: {db_path}")
    
    # 创建BehaviorAnalyzer（设置较短的干预阈值用于演示）
    behavior_analyzer = BehaviorAnalyzer(
        db=db,
        intervention_threshold=10  # 10秒触发干预
    )
    print("   ✓ BehaviorAnalyzer初始化完成")
    
    # 创建IPCHandler
    handler = IPCHandler(behavior_analyzer=behavior_analyzer)
    # 设置较短的检查间隔用于演示
    handler._intervention_check_interval = 3  # 每3秒检查一次
    print("   ✓ IPCHandler初始化完成")
    
    # 2. 模拟用户浏览文档
    print("\n2. 模拟用户浏览文档...")
    
    doc_hash = "example_doc_hash"
    page = 1
    
    # 发送page_view事件（开始跟踪停留时间）
    print(f"\n   发送page_view事件: docHash={doc_hash}, page={page}")
    request = {
        "id": "req-1",
        "seq": 0,
        "method": "behavior",
        "params": {
            "docHash": doc_hash,
            "page": page,
            "eventType": "page_view",
            "metadata": {"source": "example"}
        }
    }
    
    response_str = await handler.handle_request(json.dumps(request))
    response = json.loads(response_str)
    
    if response["success"]:
        print(f"   ✓ 行为记录成功: eventId={response['data']['eventId']}")
        print(f"   ✓ 页面跟踪已启动，将在{behavior_analyzer.intervention_threshold}秒后触发干预")
    else:
        print(f"   ✗ 行为记录失败: {response['error']}")
        return
    
    # 3. 模拟用户交互
    print("\n3. 模拟用户交互...")
    
    # 等待2秒，模拟用户阅读
    await asyncio.sleep(2)
    
    # 发送text_select事件
    print(f"\n   发送text_select事件")
    request = {
        "id": "req-2",
        "seq": 1,
        "method": "behavior",
        "params": {
            "docHash": doc_hash,
            "page": page,
            "eventType": "text_select",
            "metadata": {"text": "用户选中的文本"}
        }
    }
    
    response_str = await handler.handle_request(json.dumps(request))
    response = json.loads(response_str)
    
    if response["success"]:
        print(f"   ✓ 文本选择记录成功")
    
    # 等待3秒
    await asyncio.sleep(3)
    
    # 发送scroll事件
    print(f"\n   发送scroll事件")
    request = {
        "id": "req-3",
        "seq": 2,
        "method": "behavior",
        "params": {
            "docHash": doc_hash,
            "page": page,
            "eventType": "scroll",
            "metadata": {"position": 0.5}
        }
    }
    
    response_str = await handler.handle_request(json.dumps(request))
    response = json.loads(response_str)
    
    if response["success"]:
        print(f"   ✓ 滚动事件记录成功")
    
    # 4. 查询行为统计
    print("\n4. 查询行为统计...")
    
    stats = await behavior_analyzer.get_page_statistics(doc_hash, page)
    print(f"\n   页面统计信息:")
    print(f"   - 浏览次数: {stats.total_views}")
    print(f"   - 选择次数: {stats.total_selects}")
    print(f"   - 滚动次数: {stats.total_scrolls}")
    print(f"   - 平均停留时间: {stats.avg_duration:.2f}秒")
    
    # 5. 等待干预触发
    print("\n5. 等待干预触发...")
    print(f"   (需要等待约{behavior_analyzer.intervention_threshold}秒)")
    
    # 获取当前停留时间
    current_dwell = behavior_analyzer.get_current_dwell_time(doc_hash, page)
    print(f"   当前停留时间: {current_dwell:.2f}秒")
    
    # 等待足够长的时间以触发干预
    remaining_time = behavior_analyzer.intervention_threshold - current_dwell + 3
    if remaining_time > 0:
        print(f"   等待{remaining_time:.0f}秒...")
        await asyncio.sleep(remaining_time)
    
    # 检查是否触发了干预
    print("\n   检查干预触发状态...")
    key = f"{doc_hash}_{page}"
    if key not in handler._active_pages:
        print("   ✓ 干预已触发，页面已从活跃列表中移除")
    else:
        print("   ⚠ 干预尚未触发，可能需要更长时间")
    
    # 6. 模拟用户切换到新页面
    print("\n6. 模拟用户切换到新页面...")
    
    new_page = 2
    print(f"\n   发送page_view事件: page={new_page}")
    request = {
        "id": "req-4",
        "seq": 3,
        "method": "behavior",
        "params": {
            "docHash": doc_hash,
            "page": new_page,
            "eventType": "page_view"
        }
    }
    
    response_str = await handler.handle_request(json.dumps(request))
    response = json.loads(response_str)
    
    if response["success"]:
        print(f"   ✓ 新页面跟踪已启动")
    
    # 7. 查询所有行为记录
    print("\n7. 查询所有行为记录...")
    
    all_behaviors = await behavior_analyzer.get_behaviors(doc_hash)
    print(f"\n   文档 {doc_hash} 的所有行为记录:")
    print(f"   总计: {len(all_behaviors)} 条记录")
    
    for i, behavior in enumerate(all_behaviors[:5], 1):  # 只显示前5条
        print(f"\n   记录 {i}:")
        print(f"   - 事件类型: {behavior.event_type}")
        print(f"   - 页码: {behavior.page}")
        print(f"   - 时间: {behavior.timestamp}")
        if behavior.metadata:
            print(f"   - 元数据: {behavior.metadata}")
    
    if len(all_behaviors) > 5:
        print(f"\n   ... 还有 {len(all_behaviors) - 5} 条记录")
    
    # 8. 清理
    print("\n8. 清理资源...")
    
    handler.stop_intervention_check()
    print("   ✓ 干预检查任务已停止")
    
    # 等待任务完成
    if handler._intervention_task:
        try:
            await handler._intervention_task
        except asyncio.CancelledError:
            pass
    
    print("\n" + "=" * 60)
    print("示例完成！")
    print("=" * 60)
    
    print("\n关键要点:")
    print("1. 通过IPC的behavior方法可以记录用户行为")
    print("2. page_view事件会自动启动停留时间跟踪")
    print("3. 超过阈值后会自动触发主动干预推送")
    print("4. 可以查询行为统计信息用于分析")
    print("5. 系统会自动管理活跃页面和后台检查任务")


if __name__ == "__main__":
    asyncio.run(main())
