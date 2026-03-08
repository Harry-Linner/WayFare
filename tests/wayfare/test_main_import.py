"""
简单的导入测试，验证main.py可以正常导入
"""

import pytest


def test_main_module_import():
    """测试main模块可以正常导入"""
    try:
        from wayfare import main
        assert main is not None
        assert hasattr(main, 'WayFareBackend')
        assert hasattr(main, 'main')
        assert hasattr(main, 'main_async')
    except ImportError as e:
        pytest.fail(f"Failed to import wayfare.main: {e}")


def test_wayfare_backend_class():
    """测试WayFareBackend类可以实例化"""
    from wayfare.main import WayFareBackend
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        backend = WayFareBackend(
            workspace=tmpdir,
            config_path=None,
            log_level="INFO"
        )
        
        assert backend.workspace.exists()
        assert backend.log_level == "INFO"
        assert backend.shutdown_requested is False


def test_argparse_help():
    """测试命令行参数解析（help）"""
    import subprocess
    import sys
    
    # 运行 python -m wayfare.main --help
    result = subprocess.run(
        [sys.executable, "-m", "wayfare.main", "--help"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert "WayFare MVP Backend" in result.stdout
    assert "--workspace" in result.stdout
    assert "--config" in result.stdout
    assert "--log-level" in result.stdout
