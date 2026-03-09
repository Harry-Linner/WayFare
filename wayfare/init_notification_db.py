#!/usr/bin/env python3
"""
通知系统数据库初始化脚本

创建通知相关的数据库表和索引：
- notifications 表：存储所有通知
- notification_preferences 表：存储用户的通知偏好设置
"""

import asyncio
import aiosqlite
from pathlib import Path


async def init_notification_tables(db_path: str = ".wayfare/wayfare.db"):
    """
    初始化通知相关的数据库表
    
    Args:
        db_path: 数据库文件路径
    """
    # 确保目录存在
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    
    async with aiosqlite.connect(db_path) as db:
        # 启用外键约束
        await db.execute("PRAGMA foreign_keys = ON")
        
        # 创建 notifications 表
        await db.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                priority TEXT NOT NULL DEFAULT 'normal',
                icon TEXT,
                action_url TEXT,
                action_label TEXT,
                action_type TEXT,
                action_payload TEXT,
                metadata TEXT,
                created_at INTEGER NOT NULL,
                scheduled_at INTEGER,
                expires_at INTEGER,
                is_read BOOLEAN NOT NULL DEFAULT 0,
                read_at INTEGER,
                is_dismissed BOOLEAN NOT NULL DEFAULT 0,
                dismissed_at INTEGER
            )
        """)
        
        # 创建索引
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_notifications_user_id 
            ON notifications(user_id)
        """)
        
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_notifications_created_at 
            ON notifications(created_at DESC)
        """)
        
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_notifications_read_dismissed 
            ON notifications(is_read, is_dismissed)
        """)
        
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_notifications_type 
            ON notifications(type)
        """)
        
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_notifications_expires_at 
            ON notifications(expires_at)
        """)
        
        # 创建 notification_preferences 表
        await db.execute("""
            CREATE TABLE IF NOT EXISTS notification_preferences (
                user_id TEXT PRIMARY KEY,
                enabled_types TEXT NOT NULL,
                enable_browser_notifications BOOLEAN NOT NULL DEFAULT 1,
                enable_in_app_notifications BOOLEAN NOT NULL DEFAULT 1,
                enable_email_notifications BOOLEAN NOT NULL DEFAULT 0,
                min_priority_level TEXT NOT NULL DEFAULT 'normal',
                quiet_hours TEXT,
                max_notifications_per_hour INTEGER,
                updated_at INTEGER NOT NULL
            )
        """)
        
        await db.commit()
        print(f"✅ Notification tables initialized successfully at {db_path}")


if __name__ == '__main__':
    asyncio.run(init_notification_tables())
