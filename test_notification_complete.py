#!/usr/bin/env python3
"""
完整的通知系统测试

测试后端 API 的所有功能，不需要 Tauri 应用。
"""

import requests
import time
import sys

BASE_URL = 'http://localhost:3001'
TEST_USER = 'test_user_complete'

def print_step(step, message):
    """打印测试步骤"""
    print(f"\n{'='*60}")
    print(f"{step}. {message}")
    print('='*60)

def test_health():
    """测试健康检查"""
    print_step(1, "测试健康检查")
    try:
        response = requests.get(f'{BASE_URL}/health', timeout=5)
        if response.status_code == 200:
            print("✅ 后端健康检查通过")
            print(f"   响应: {response.json()}")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端")
        print("   请确保后端正在运行:")
        print("   python start_notification_backend.py --enable-test")
        return False

def test_create_notification():
    """测试创建通知"""
    print_step(2, "测试创建测试通知")
    response = requests.post(
        f'{BASE_URL}/api/notifications/test',
        json={
            'user_id': TEST_USER,
            'notification_type': 'learning_progress'
        }
    )
    if response.status_code == 200:
        notification = response.json()
        print(f"✅ 创建通知成功")
        print(f"   ID: {notification['id']}")
        print(f"   标题: {notification['title']}")
        print(f"   消息: {notification['message']}")
        return notification['id']
    else:
        print(f"❌ 创建通知失败: {response.status_code}")
        print(f"   错误: {response.text}")
        return None

def test_fetch_notifications():
    """测试获取通知列表"""
    print_step(3, "测试获取通知列表")
    response = requests.post(
        f'{BASE_URL}/api/notifications/fetch',
        json={
            'user_id': TEST_USER,
            'limit': 20,
            'offset': 0,
            'types': [],
            'unread_only': False,
            'sort_by': 'recent'
        }
    )
    if response.status_code == 200:
        batch = response.json()
        print(f"✅ 获取通知成功")
        print(f"   总数: {batch['total_count']}")
        print(f"   未读: {batch['unread_count']}")
        print(f"   返回: {len(batch['notifications'])} 条")
        return batch
    else:
        print(f"❌ 获取通知失败: {response.status_code}")
        return None

def test_mark_as_read(notification_id):
    """测试标记为已读"""
    print_step(4, "测试标记通知为已读")
    response = requests.post(
        f'{BASE_URL}/api/notifications/{notification_id}/read',
        json={'user_id': TEST_USER}
    )
    if response.status_code == 200:
        notification = response.json()
        print(f"✅ 标记为已读成功")
        print(f"   已读状态: {notification['is_read']}")
        return True
    else:
        print(f"❌ 标记失败: {response.status_code}")
        return False

def test_get_preferences():
    """测试获取偏好设置"""
    print_step(5, "测试获取偏好设置")
    response = requests.get(
        f'{BASE_URL}/api/notifications/preferences',
        params={'user_id': TEST_USER}
    )
    if response.status_code == 200:
        prefs = response.json()
        print(f"✅ 获取偏好设置成功")
        print(f"   启用类型: {prefs['enabled_types']}")
        print(f"   最低优先级: {prefs['min_priority_level']}")
        return prefs
    else:
        print(f"❌ 获取偏好设置失败: {response.status_code}")
        return None

def test_update_preferences(prefs):
    """测试更新偏好设置"""
    print_step(6, "测试更新偏好设置")
    prefs['enabled_types'] = ['learning_progress']
    prefs['min_priority_level'] = 'high'
    response = requests.put(
        f'{BASE_URL}/api/notifications/preferences',
        json=prefs
    )
    if response.status_code == 200:
        print(f"✅ 更新偏好设置成功")
        return True
    else:
        print(f"❌ 更新失败: {response.status_code}")
        return False

def test_dismiss_notification(notification_id):
    """测试关闭通知"""
    print_step(7, "测试关闭通知")
    response = requests.delete(
        f'{BASE_URL}/api/notifications/{notification_id}',
        params={'user_id': TEST_USER}
    )
    if response.status_code == 200:
        print(f"✅ 关闭通知成功")
        return True
    else:
        print(f"❌ 关闭失败: {response.status_code}")
        return False

def test_batch_dismiss():
    """测试批量关闭"""
    print_step(8, "测试批量关闭通知")
    
    # 先创建几条通知
    ids = []
    for i in range(3):
        response = requests.post(
            f'{BASE_URL}/api/notifications/test',
            json={
                'user_id': TEST_USER,
                'notification_type': 'task_completed'
            }
        )
        if response.status_code == 200:
            ids.append(response.json()['id'])
    
    if not ids:
        print("❌ 无法创建测试通知")
        return False
    
    # 批量关闭
    response = requests.post(
        f'{BASE_URL}/api/notifications/batch-dismiss',
        json={
            'notification_ids': ids,
            'user_id': TEST_USER
        }
    )
    if response.status_code == 200:
        print(f"✅ 批量关闭 {len(ids)} 条通知成功")
        return True
    else:
        print(f"❌ 批量关闭失败: {response.status_code}")
        return False

def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("通知系统完整测试")
    print("="*60)
    
    results = []
    
    # 1. 健康检查
    if not test_health():
        print("\n❌ 后端未运行，测试终止")
        sys.exit(1)
    results.append(True)
    
    time.sleep(0.5)
    
    # 2. 创建通知
    notification_id = test_create_notification()
    results.append(notification_id is not None)
    if not notification_id:
        print("\n❌ 无法创建通知，测试终止")
        sys.exit(1)
    
    time.sleep(0.5)
    
    # 3. 获取通知列表
    batch = test_fetch_notifications()
    results.append(batch is not None)
    
    time.sleep(0.5)
    
    # 4. 标记为已读
    results.append(test_mark_as_read(notification_id))
    
    time.sleep(0.5)
    
    # 5. 获取偏好设置
    prefs = test_get_preferences()
    results.append(prefs is not None)
    
    time.sleep(0.5)
    
    # 6. 更新偏好设置
    if prefs:
        results.append(test_update_preferences(prefs))
    else:
        results.append(False)
    
    time.sleep(0.5)
    
    # 7. 关闭通知
    results.append(test_dismiss_notification(notification_id))
    
    time.sleep(0.5)
    
    # 8. 批量关闭
    results.append(test_batch_dismiss())
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("\n✅ 所有测试通过！通知系统工作正常。")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
