#!/usr/bin/env python3
"""
通知系统 API 集成测试

测试 Flask API 端点的功能，不依赖完整的 wayfare 模块。
需要先启动 Flask 服务器。
"""

import requests
import json
import time


def test_api_endpoints():
    """测试所有 API 端点"""
    
    base_url = 'http://localhost:3001'
    test_user = 'test_user_api'
    
    print("=== 通知系统 API 测试 ===\n")
    print("确保 Flask 服务器正在运行: python start_notification_backend.py --enable-test\n")
    
    # 测试 1: 健康检查
    print("1. 测试健康检查...")
    try:
        response = requests.get(f'{base_url}/health', timeout=5)
        if response.status_code == 200:
            print(f"   ✓ 服务器健康: {response.json()}\n")
        else:
            print(f"   ✗ 健康检查失败: {response.status_code}\n")
            return
    except requests.exceptions.ConnectionError:
        print("   ✗ 无法连接到服务器，请先启动后端\n")
        print("   运行: python start_notification_backend.py --enable-test")
        return
    
    # 测试 2: 发送测试通知
    print("2. 测试发送测试通知...")
    response = requests.post(
        f'{base_url}/api/notifications/test',
        json={
            'user_id': test_user,
            'notification_type': 'learning_progress'
        }
    )
    if response.status_code == 200:
        notification = response.json()
        notification_id = notification['id']
        print(f"   ✓ 创建通知: {notification_id}")
        print(f"   标题: {notification['title']}\n")
    else:
        print(f"   ✗ 创建失败: {response.status_code} - {response.text}\n")
        return
    
    # 测试 3: 获取通知列表
    print("3. 测试获取通知列表...")
    response = requests.post(
        f'{base_url}/api/notifications/fetch',
        json={
            'user_id': test_user,
            'limit': 20,
            'offset': 0,
            'types': [],
            'unread_only': False,
            'sort_by': 'recent'
        }
    )
    if response.status_code == 200:
        batch = response.json()
        print(f"   ✓ 总数: {batch['total_count']}")
        print(f"   ✓ 未读: {batch['unread_count']}")
        print(f"   ✓ 返回: {len(batch['notifications'])} 条\n")
    else:
        print(f"   ✗ 获取失败: {response.status_code}\n")
        return
    
    # 测试 4: 标记为已读
    print("4. 测试标记为已读...")
    response = requests.post(
        f'{base_url}/api/notifications/{notification_id}/read',
        json={'user_id': test_user}
    )
    if response.status_code == 200:
        updated = response.json()
        print(f"   ✓ 已读状态: {updated['is_read']}\n")
    else:
        print(f"   ✗ 标记失败: {response.status_code}\n")
    
    # 测试 5: 获取未读通知
    print("5. 测试获取未读通知...")
    response = requests.post(
        f'{base_url}/api/notifications/fetch',
        json={
            'user_id': test_user,
            'limit': 20,
            'offset': 0,
            'types': [],
            'unread_only': True,
            'sort_by': 'recent'
        }
    )
    if response.status_code == 200:
        batch = response.json()
        print(f"   ✓ 未读通知: {batch['unread_count']} 条\n")
    else:
        print(f"   ✗ 获取失败: {response.status_code}\n")
    
    # 测试 6: 获取偏好设置
    print("6. 测试获取偏好设置...")
    response = requests.get(
        f'{base_url}/api/notifications/preferences',
        params={'user_id': test_user}
    )
    if response.status_code == 200:
        prefs = response.json()
        print(f"   ✓ 启用类型: {prefs['enabled_types']}")
        print(f"   ✓ 最低优先级: {prefs['min_priority_level']}\n")
    else:
        print(f"   ✗ 获取失败: {response.status_code}\n")
    
    # 测试 7: 更新偏好设置
    print("7. 测试更新偏好设置...")
    prefs['enabled_types'] = ['learning_progress']
    prefs['min_priority_level'] = 'high'
    response = requests.put(
        f'{base_url}/api/notifications/preferences',
        json=prefs
    )
    if response.status_code == 200:
        print("   ✓ 更新成功\n")
    else:
        print(f"   ✗ 更新失败: {response.status_code}\n")
    
    # 测试 8: 关闭通知
    print("8. 测试关闭通知...")
    response = requests.delete(
        f'{base_url}/api/notifications/{notification_id}',
        params={'user_id': test_user}
    )
    if response.status_code == 200:
        print("   ✓ 关闭成功\n")
    else:
        print(f"   ✗ 关闭失败: {response.status_code}\n")
    
    # 测试 9: 批量关闭
    print("9. 测试批量关闭...")
    # 先创建几条通知
    ids = []
    for i in range(3):
        response = requests.post(
            f'{base_url}/api/notifications/test',
            json={
                'user_id': test_user,
                'notification_type': 'task_completed'
            }
        )
        if response.status_code == 200:
            ids.append(response.json()['id'])
    
    if ids:
        response = requests.post(
            f'{base_url}/api/notifications/batch-dismiss',
            json={
                'notification_ids': ids,
                'user_id': test_user
            }
        )
        if response.status_code == 200:
            print(f"   ✓ 批量关闭 {len(ids)} 条通知\n")
        else:
            print(f"   ✗ 批量关闭失败: {response.status_code}\n")
    
    print("=== API 测试完成 ✓ ===")


if __name__ == '__main__':
    try:
        test_api_endpoints()
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
