#!/usr/bin/env python3
"""
通知系统后端启动脚本

快速启动 Flask API 服务器，用于开发和测试。
"""

import os
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def initialize_database():
    """初始化数据库和通知表"""
    # 使用 importlib 直接加载模块，完全避免包导入
    import importlib.util
    
    init_db_path = project_root / 'wayfare' / 'init_notification_db.py'
    spec = importlib.util.spec_from_file_location("init_notification_db", init_db_path)
    init_db_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(init_db_module)
    
    db_path = os.getenv('DATABASE_PATH', '.wayfare/wayfare.db')
    
    print(f"初始化数据库: {db_path}")
    
    # 确保目录存在
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    # 创建通知表
    await init_db_module.init_notification_tables(db_path)
    
    print("数据库初始化完成")


def main():
    """启动通知系统后端"""
    print("=== Wayfare 通知系统后端 ===\n")
    
    # 设置环境变量
    os.environ.setdefault('DATABASE_PATH', '.wayfare/wayfare.db')
    os.environ.setdefault('BACKEND_PORT', '3001')
    os.environ.setdefault('LOG_LEVEL', 'INFO')
    
    # 开发环境启用测试通知
    if '--enable-test' in sys.argv:
        os.environ['ENABLE_TEST_NOTIFICATIONS'] = 'true'
        print("✓ 测试通知功能已启用\n")
    
    # 初始化数据库
    try:
        asyncio.run(initialize_database())
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        sys.exit(1)
    
    # 启动 Flask 应用
    # 使用 importlib 直接加载模块，完全避免包导入
    import importlib.util
    api_module_path = project_root / 'wayfare' / 'notification_api.py'
    spec = importlib.util.spec_from_file_location("notification_api", api_module_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    
    port = int(os.getenv('BACKEND_PORT', 3001))
    print(f"\n启动 Flask 服务器在端口 {port}...")
    print(f"健康检查: http://localhost:{port}/health")
    print(f"API 基础路径: http://localhost:{port}/api/notifications/\n")
    
    api_module.app.run(host='0.0.0.0', port=port, debug=True)


if __name__ == '__main__':
    main()
