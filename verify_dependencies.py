#!/usr/bin/env python3
"""
依赖验证脚本

验证WayFare MVP Backend的所有依赖是否正确安装。
运行此脚本以确保环境配置正确。

Usage:
    python verify_dependencies.py
"""

import sys
from typing import List, Tuple


def check_import(module_name: str, package_name: str = None) -> Tuple[bool, str]:
    """
    检查模块是否可以导入
    
    Args:
        module_name: 要导入的模块名
        package_name: pip包名（如果与模块名不同）
    
    Returns:
        (成功标志, 消息)
    """
    if package_name is None:
        package_name = module_name
    
    try:
        __import__(module_name)
        return True, f"✓ {package_name}"
    except ImportError as e:
        return False, f"✗ {package_name} - 未安装或导入失败: {e}"


def main():
    """主函数：检查所有依赖"""
    print("=" * 60)
    print("WayFare MVP Backend - 依赖验证")
    print("=" * 60)
    print()
    
    # 定义要检查的依赖
    dependencies = [
        # 核心框架
        ("typer", "typer"),
        ("litellm", "litellm"),
        ("pydantic", "pydantic"),
        ("pydantic_settings", "pydantic-settings"),
        ("loguru", "loguru"),
        ("openai", "openai"),
        
        # 数据库
        ("aiosqlite", "aiosqlite"),
        
        # 文档解析
        ("fitz", "PyMuPDF"),
        ("markdown_it", "markdown-it-py"),
        
        # 向量化与向量存储
        ("onnxruntime", "onnxruntime"),
        ("transformers", "transformers"),
        ("qdrant_client", "qdrant-client"),
        ("numpy", "numpy"),
        
        # 哈希
        ("blake3", "blake3"),
        
        # 配置
        ("yaml", "pyyaml"),
        
        # HTTP客户端
        ("httpx", "httpx"),
    ]
    
    print("检查生产依赖:")
    print("-" * 60)
    
    results: List[Tuple[bool, str]] = []
    for module_name, package_name in dependencies:
        success, message = check_import(module_name, package_name)
        results.append((success, message))
        print(message)
    
    print()
    print("检查开发依赖:")
    print("-" * 60)
    
    dev_dependencies = [
        ("pytest", "pytest"),
        ("hypothesis", "hypothesis"),
        ("black", "black"),
        ("mypy", "mypy"),
        ("pylint", "pylint"),
        ("coverage", "coverage"),
    ]
    
    for module_name, package_name in dev_dependencies:
        success, message = check_import(module_name, package_name)
        results.append((success, message))
        print(message)
    
    print()
    print("=" * 60)
    
    # 统计结果
    total = len(results)
    success_count = sum(1 for success, _ in results if success)
    failed_count = total - success_count
    
    print(f"总计: {total} 个依赖")
    print(f"成功: {success_count} 个")
    print(f"失败: {failed_count} 个")
    
    if failed_count > 0:
        print()
        print("⚠️  部分依赖未安装！")
        print()
        print("请运行以下命令安装缺失的依赖:")
        print("  生产环境: pip install -r requirements.txt")
        print("  开发环境: pip install -r requirements-dev.txt")
        print()
        sys.exit(1)
    else:
        print()
        print("✓ 所有依赖已正确安装！")
        print()
        sys.exit(0)


if __name__ == "__main__":
    main()
