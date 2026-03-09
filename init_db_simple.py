#!/usr/bin/env python3
"""
简单的数据库初始化脚本
直接初始化通知系统数据库，不依赖其他模块
"""
import sqlite3
import os

def init_notification_tables(db_path: str):
    """初始化通知系统数据库表"""
    
    # 确保目录存在
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 创建通知表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                priority INTEGER DEFAULT 0,
                is_read INTEGER DEFAULT 0,
                created_at INTEGER NOT NULL,
                read_at INTEGER,
                metadata TEXT,
                action_url TEXT,
                expires_at INTEGER
            )
        """)
        
        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_notifications_user_id 
            ON notifications(user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_notifications_created_at 
            ON notifications(created_at DESC)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_notifications_type 
            ON notifications(type)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_notifications_is_read 
            ON notifications(is_read)
        """)
        
        # 提交更改
        conn.commit()
        print(f"✅ Notification tables initialized successfully at {db_path}")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    db_path = ".wayfare/wayfare.db"
    init_notification_tables(db_path)
