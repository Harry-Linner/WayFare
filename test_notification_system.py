#!/usr/bin/env python3
"""
通知系统集成测试脚本

测试完整的通知系统功能，包括创建、查询、更新和删除操作。
不依赖 wayfare 配置系统，直接测试核心功能。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_notification_system():
    """测试通知系统的完整功能"""
    
    print("=== 通知系统集成测试 ===\n")
    
    # 直接导入需要的模块，避免通过 wayfare/__init__.py
    import sys
    sys.path.insert(0, str(Path(__file__).parent / 'wayfare'))
    from init_notification_db import init_notification_tables
    import aiosqlite
    from datetime import datetime, timezone, timedelta
    from uuid import uuid4
    
    # 使用测试数据库
    test_db_path = '.wayfare/test_notification.db'
    
    # 初始化数据库
    print("1. 初始化测试数据库...")
    Path(test_db_path).parent.mkdir(parents=True, exist_ok=True)
    await init_notification_tables(test_db_path)
    print("   ✓ 数据库初始化成功\n")
    
    test_user = 'test_user_123'
    
    # 测试 2: 创建通知
    print("2. 测试创建通知...")
    async with aiosqlite.connect(test_db_path) as conn:
        notification_id = str(uuid4())
        now = int(datetime.now(timezone.utc).timestamp())
        expires_at = int((datetime.now(timezone.utc) + timedelta(hours=24)).timestamp())
        
        await conn.execute("""
            INSERT INTO notifications (
                id, user_id, type, title, message, priority,
                created_at, expires_at, is_read, is_dismissed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            notification_id, test_user, 'learning_progress',
            '测试通知 1', '这是一条测试通知', 'normal',
            now, expires_at, False, False
        ))
        await conn.commit()
        print(f"   ✓ 创建通知: {notification_id}\n")
    
    # 测试 3: 查询通知
    print("3. 测试查询通知...")
    async with aiosqlite.connect(test_db_path) as conn:
        cursor = await conn.execute(
            "SELECT * FROM notifications WHERE user_id = ?",
            (test_user,)
        )
        rows = await cursor.fetchall()
        print(f"   ✓ 查询到 {len(rows)} 条通知\n")
        assert len(rows) == 1, "应该有 1 条通知"
    
    # 测试 4: 更新通知（标记为已读）
    print("4. 测试标记为已读...")
    async with aiosqlite.connect(test_db_path) as conn:
        read_at = int(datetime.now(timezone.utc).timestamp())
        await conn.execute(
            "UPDATE notifications SET is_read = ?, read_at = ? WHERE id = ?",
            (True, read_at, notification_id)
        )
        await conn.commit()
        
        cursor = await conn.execute(
            "SELECT is_read FROM notifications WHERE id = ?",
            (notification_id,)
        )
        row = await cursor.fetchone()
        assert row[0] == 1, "通知应该标记为已读"
        print("   ✓ 通知已标记为已读\n")
    
    # 测试 5: 偏好设置
    print("5. 测试偏好设置...")
    async with aiosqlite.connect(test_db_path) as conn:
        import json
        prefs_data = {
            'user_id': test_user,
            'enabled_types': ['learning_progress', 'task_completed'],
            'enable_browser_notifications': True,
            'enable_in_app_notifications': True,
            'enable_email_notifications': False,
            'min_priority_level': 'normal',
            'updated_at': int(datetime.now(timezone.utc).timestamp())
        }
        
        await conn.execute("""
            INSERT OR REPLACE INTO notification_preferences (
                user_id, enabled_types, enable_browser_notifications,
                enable_in_app_notifications, enable_email_notifications,
                min_priority_level, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            prefs_data['user_id'],
            json.dumps(prefs_data['enabled_types']),
            prefs_data['enable_browser_notifications'],
            prefs_data['enable_in_app_notifications'],
            prefs_data['enable_email_notifications'],
            prefs_data['min_priority_level'],
            prefs_data['updated_at']
        ))
        await conn.commit()
        
        cursor = await conn.execute(
            "SELECT * FROM notification_preferences WHERE user_id = ?",
            (test_user,)
        )
        row = await cursor.fetchone()
        assert row is not None, "应该保存偏好设置"
        print("   ✓ 偏好设置已保存\n")
    
    # 清理测试数据库
    print("6. 清理测试数据...")
    Path(test_db_path).unlink(missing_ok=True)
    print("   ✓ 测试数据库已删除\n")
    
    print("=== 所有测试通过 ✓ ===")


if __name__ == '__main__':
    try:
        asyncio.run(test_notification_system())
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

