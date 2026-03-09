"""
通知清理任务

定期清理过期和已关闭的通知，保持数据库整洁。
"""

from datetime import datetime, timezone, timedelta
from wayfare.logging import get_logger
import aiosqlite

logger = get_logger(__name__)


async def cleanup_expired_notifications(db_path: str, days: int = 30):
    """
    清理过期的已关闭通知
    
    Args:
        db_path: 数据库路径
        days: 保留天数（默认 30 天）
    """
    cutoff_timestamp = int(
        (datetime.now(timezone.utc) - timedelta(days=days)).timestamp()
    )
    
    async with aiosqlite.connect(db_path) as conn:
        # 删除 30 天前的已关闭通知
        cursor = await conn.execute("""
            DELETE FROM notifications
            WHERE is_dismissed = 1
            AND dismissed_at < ?
        """, (cutoff_timestamp,))
        
        deleted_count = cursor.rowcount
        await conn.commit()
        
        logger.info(f"Cleaned up {deleted_count} expired notifications")
        return deleted_count


async def cleanup_old_read_notifications(db_path: str, days: int = 90):
    """
    清理旧的已读通知（保留更长时间）
    
    Args:
        db_path: 数据库路径
        days: 保留天数（默认 90 天）
    """
    cutoff_timestamp = int(
        (datetime.now(timezone.utc) - timedelta(days=days)).timestamp()
    )
    
    async with aiosqlite.connect(db_path) as conn:
        # 删除 90 天前的已读但未关闭的通知
        cursor = await conn.execute("""
            DELETE FROM notifications
            WHERE is_read = 1
            AND is_dismissed = 0
            AND read_at < ?
        """, (cutoff_timestamp,))
        
        deleted_count = cursor.rowcount
        await conn.commit()
        
        logger.info(f"Cleaned up {deleted_count} old read notifications")
        return deleted_count


async def run_cleanup_task(db_path: str):
    """
    运行完整的清理任务
    
    Args:
        db_path: 数据库路径
    """
    logger.info("Starting notification cleanup task")
    
    dismissed_count = await cleanup_expired_notifications(db_path, days=30)
    read_count = await cleanup_old_read_notifications(db_path, days=90)
    
    total_cleaned = dismissed_count + read_count
    logger.info(f"Cleanup completed: {total_cleaned} notifications removed")
    
    return {
        'dismissed_cleaned': dismissed_count,
        'read_cleaned': read_count,
        'total_cleaned': total_cleaned
    }


if __name__ == '__main__':
    import asyncio
    import os
    
    db_path = os.getenv('DATABASE_PATH', '.wayfare/wayfare.db')
    result = asyncio.run(run_cleanup_task(db_path))
    
    print(f"清理完成:")
    print(f"  - 已关闭通知: {result['dismissed_cleaned']} 条")
    print(f"  - 已读通知: {result['read_cleaned']} 条")
    print(f"  - 总计: {result['total_cleaned']} 条")
