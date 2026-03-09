"""
通知系统 API - Flask 应用

提供 RESTful API 端点供 Tauri 中枢调用。
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import importlib.util
from pathlib import Path

# 使用 importlib 直接加载 notification_manager，避免触发 wayfare/__init__.py
_manager_module_path = Path(__file__).parent / 'notification_manager.py'
_spec = importlib.util.spec_from_file_location("notification_manager_module", _manager_module_path)
_manager_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_manager_module)
NotificationManager = _manager_module.NotificationManager

# 导入 logging，但避免通过 wayfare 包
try:
    from logging import get_logger
except ImportError:
    # 如果 wayfare.logging 不可用，使用标准 logging
    import logging
    def get_logger(name):
        return logging.getLogger(name)

logger = get_logger(__name__)

# 创建 Flask 应用
app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 延迟初始化数据库和通知管理器
db = None
notification_manager = None
db_path = os.getenv('DATABASE_PATH', '.wayfare/wayfare.db')


def get_notification_manager():
    """获取 NotificationManager 实例（延迟初始化）"""
    global db, notification_manager
    if notification_manager is None:
        # 使用 importlib 直接加载 db 模块，完全避免包导入
        import importlib.util
        db_module_path = Path(__file__).parent / 'db.py'
        spec = importlib.util.spec_from_file_location("db_module", db_module_path)
        db_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(db_module)
        
        db = db_module.SQLiteDB(db_path=db_path)
        notification_manager = NotificationManager(db)
    return notification_manager


@app.route('/api/notifications/fetch', methods=['POST'])
def fetch_notifications():
    """获取通知列表"""
    import asyncio
    
    try:
        manager = get_notification_manager()
        data = request.get_json()
        
        # 验证必需参数
        if 'user_id' not in data:
            return jsonify({'error': 'Missing user_id'}), 400
        
        user_id = data['user_id']
        project_id = data.get('project_id')
        limit = data.get('limit', 20)
        offset = data.get('offset', 0)
        types = data.get('types', [])
        unread_only = data.get('unread_only', False)
        sort_by = data.get('sort_by', 'recent')
        
        # 调用 NotificationManager
        batch = asyncio.run(manager.get_notifications(
            user_id=user_id,
            project_id=project_id,
            limit=limit,
            offset=offset,
            types=types if types else None,
            unread_only=unread_only,
            sort_by=sort_by
        ))
        
        return jsonify(batch), 200
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/notifications/<notification_id>/read', methods=['POST'])
def mark_as_read(notification_id):
    """标记通知为已读"""
    import asyncio
    
    try:
        manager = get_notification_manager()
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Missing user_id'}), 400
        
        notification = asyncio.run(manager.mark_as_read(
            notification_id=notification_id,
            user_id=user_id
        ))
        
        if not notification:
            return jsonify({'error': 'Notification not found'}), 404
        
        return jsonify(notification), 200
        
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/notifications/<notification_id>', methods=['DELETE'])
def dismiss_notification(notification_id):
    """关闭通知"""
    import asyncio
    
    try:
        manager = get_notification_manager()
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Missing user_id'}), 400
        
        success = asyncio.run(manager.dismiss_notification(
            notification_id=notification_id,
            user_id=user_id
        ))
        
        if not success:
            return jsonify({'error': 'Notification not found'}), 404
        
        return jsonify({'dismissed': True}), 200
        
    except Exception as e:
        logger.error(f"Error dismissing notification: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/notifications/batch-dismiss', methods=['POST'])
def batch_dismiss():
    """批量关闭通知"""
    import asyncio
    
    try:
        manager = get_notification_manager()
        data = request.get_json()
        notification_ids = data.get('notification_ids', [])
        user_id = data.get('user_id')
        
        if not user_id or not notification_ids:
            return jsonify({'error': 'Missing required parameters'}), 400
        
        asyncio.run(manager.batch_dismiss(
            notification_ids=notification_ids,
            user_id=user_id
        ))
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        logger.error(f"Error batch dismissing: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/notifications/preferences', methods=['GET'])
def get_preferences():
    """获取通知偏好设置"""
    import asyncio
    
    try:
        manager = get_notification_manager()
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Missing user_id'}), 400
        
        prefs = asyncio.run(manager.get_preferences(user_id))
        
        return jsonify(prefs), 200
        
    except Exception as e:
        logger.error(f"Error getting preferences: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/notifications/preferences', methods=['PUT'])
def update_preferences():
    """更新通知偏好设置"""
    import asyncio
    
    try:
        manager = get_notification_manager()
        prefs = request.get_json()
        
        if 'user_id' not in prefs:
            return jsonify({'error': 'Missing user_id'}), 400
        
        asyncio.run(manager.update_preferences(prefs))
        
        return jsonify({'status': 'success'}), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error updating preferences: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/notifications/test', methods=['POST'])
def send_test_notification():
    """发送测试通知（仅开发环境）"""
    import asyncio
    
    if os.getenv('ENABLE_TEST_NOTIFICATIONS') != 'true':
        return jsonify({'error': 'Test notifications disabled'}), 403
    
    try:
        manager = get_notification_manager()
        data = request.get_json()
        user_id = data.get('user_id')
        notification_type = data.get('notification_type', 'learning_progress')
        
        if not user_id:
            return jsonify({'error': 'Missing user_id'}), 400
        
        notification = asyncio.run(manager.create_test_notification(
            user_id=user_id,
            notification_type=notification_type
        ))
        
        return jsonify(notification), 200
        
    except Exception as e:
        logger.error(f"Error creating test notification: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    import asyncio
    from datetime import datetime, timezone
    
    try:
        # 检查数据库连接
        import aiosqlite
        
        async def check_db():
            async with aiosqlite.connect(db_path) as conn:
                await conn.execute("SELECT 1")
        
        asyncio.run(check_db())
        
        return jsonify({
            'status': 'healthy',
            'timestamp': int(datetime.now(timezone.utc).timestamp())
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503


# 错误处理器
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Resource not found'}), 404


@app.errorhandler(500)
def internal_error(e):
    logger.error(f"Internal server error: {e}", exc_info=True)
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    import asyncio
    from datetime import datetime, timezone
    
    # 初始化数据库
    async def init():
        from db import SQLiteDB
        from init_notification_db import init_notification_tables
        
        db = SQLiteDB(db_path=db_path)
        await db.initialize()
        await init_notification_tables(db_path)
    
    asyncio.run(init())
    
    # 启动 Flask 应用
    port = int(os.getenv('BACKEND_PORT', 3001))
    app.run(host='0.0.0.0', port=port, debug=True)
