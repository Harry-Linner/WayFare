"""
通知系统使用示例

演示如何使用 NotificationManager 创建、查询和管理通知。
"""

import asyncio
from wayfare.db import SQLiteDB
from wayfare.notification_manager import NotificationManager


async def main():
    # 初始化数据库和通知管理器
    db = SQLiteDB(db_path='.wayfare/wayfare.db')
    await db.initialize()
    
    notification_manager = NotificationManager(db)
    
    user_id = 'demo_user_123'
    
    print("=== 通知系统使用示例 ===\n")
    
    # 1. 创建通知
    print("1. 创建学习进度通知...")
    notification = await notification_manager.create_notification(
        user_id=user_id,
        notification_type='learning_progress',
        title='学习进度更新',
        message='您在认知心理学的进度已达到 75%',
        priority='normal',
        metadata={
            'documentId': 'doc_123',
            'currentProgress': 75,
            'targetProgress': 100
        }
    )
    print(f"   创建成功: {notification['id']}\n")
    
    # 2. 创建高优先级通知
    print("2. 创建高优先级通知...")
    urgent_notification = await notification_manager.create_notification(
        user_id=user_id,
        notification_type='confusion_detected',
        title='需要帮助？',
        message='您在导数定义这里停留了很久',
        priority='high',
        action_url='/document/doc_123#section_5',
        action_label='查看解释',
        metadata={'topic': '导数定义'}
    )
    print(f"   创建成功: {urgent_notification['id']}\n")
    
    # 3. 获取通知列表
    print("3. 获取所有通知...")
    batch = await notification_manager.get_notifications(
        user_id=user_id,
        limit=10,
        offset=0,
        sort_by='recent'
    )
    print(f"   总数: {batch['total_count']}")
    print(f"   未读: {batch['unread_count']}")
    print(f"   本次返回: {len(batch['notifications'])} 条\n")
    
    # 4. 获取未读通知
    print("4. 获取未读通知...")
    unread_batch = await notification_manager.get_notifications(
        user_id=user_id,
        unread_only=True,
        limit=10
    )
    print(f"   未读通知: {len(unread_batch['notifications'])} 条\n")
    
    # 5. 标记通知为已读
    print("5. 标记第一条通知为已读...")
    updated = await notification_manager.mark_as_read(
        notification_id=notification['id'],
        user_id=user_id
    )
    if updated:
        print(f"   已读状态: {updated['is_read']}\n")
    
    # 6. 按类型过滤
    print("6. 获取学习进度类型的通知...")
    filtered_batch = await notification_manager.get_notifications(
        user_id=user_id,
        types=['learning_progress'],
        limit=10
    )
    print(f"   学习进度通知: {len(filtered_batch['notifications'])} 条\n")
    
    # 7. 关闭通知
    print("7. 关闭第一条通知...")
    success = await notification_manager.dismiss_notification(
        notification_id=notification['id'],
        user_id=user_id
    )
    print(f"   关闭成功: {success}\n")
    
    # 8. 批量关闭
    print("8. 批量关闭所有通知...")
    all_notifications = await notification_manager.get_notifications(
        user_id=user_id,
        limit=100
    )
    notification_ids = [n['id'] for n in all_notifications['notifications']]
    if notification_ids:
        await notification_manager.batch_dismiss(
            notification_ids=notification_ids,
            user_id=user_id
        )
        print(f"   已关闭 {len(notification_ids)} 条通知\n")
    
    # 9. 获取偏好设置
    print("9. 获取偏好设置...")
    prefs = await notification_manager.get_preferences(user_id)
    print(f"   启用的通知类型: {prefs['enabled_types']}")
    print(f"   最低优先级: {prefs['min_priority_level']}\n")
    
    # 10. 更新偏好设置
    print("10. 更新偏好设置...")
    prefs['enabled_types'] = ['learning_progress', 'task_completed']
    prefs['min_priority_level'] = 'high'
    prefs['enable_browser_notifications'] = False
    await notification_manager.update_preferences(prefs)
    print("   更新成功\n")
    
    # 11. 验证更新
    print("11. 验证偏好设置更新...")
    updated_prefs = await notification_manager.get_preferences(user_id)
    print(f"   启用的通知类型: {updated_prefs['enabled_types']}")
    print(f"   最低优先级: {updated_prefs['min_priority_level']}")
    print(f"   浏览器通知: {updated_prefs['enable_browser_notifications']}\n")
    
    print("=== 示例完成 ===")


if __name__ == '__main__':
    asyncio.run(main())
