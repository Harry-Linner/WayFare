"""
配置系统测试

测试WayFareConfig和ConfigManager的功能，包括：
- 默认配置加载
- YAML文件加载和保存
- 环境变量覆盖
- 配置更新
"""

import os
import pytest
import tempfile
import yaml
from pathlib import Path

from wayfare.config import WayFareConfig, ConfigManager


class TestWayFareConfig:
    """测试WayFareConfig类"""
    
    def test_default_config(self):
        """测试默认配置值"""
        config = WayFareConfig()
        
        assert config.llm_model == "deepseek-chat"
        assert config.embedding_model == "bge-small-zh-v1.5"
        assert config.qdrant_url == "http://localhost:6333"
        assert config.retrieval_top_k == 5
        assert config.intervention_threshold == 120
        assert config.chunk_size == 300
        assert config.chunk_overlap == 50
    
    def test_custom_config(self):
        """测试自定义配置"""
        config = WayFareConfig(
            llm_model="gpt-4",
            retrieval_top_k=10,
            intervention_threshold=180
        )
        
        assert config.llm_model == "gpt-4"
        assert config.retrieval_top_k == 10
        assert config.intervention_threshold == 180
        # 未指定的配置应使用默认值
        assert config.embedding_model == "bge-small-zh-v1.5"
    
    def test_config_dict(self):
        """测试配置转换为字典"""
        config = WayFareConfig()
        config_dict = config.model_dump()
        
        assert isinstance(config_dict, dict)
        assert "llm_model" in config_dict
        assert "embedding_model" in config_dict
        assert config_dict["llm_model"] == "deepseek-chat"


class TestConfigManager:
    """测试ConfigManager类"""
    
    def test_load_default_config_when_file_not_exists(self):
        """测试配置文件不存在时使用默认配置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            
            manager = ConfigManager(str(config_path))
            
            # 应该创建默认配置
            assert manager.config is not None
            assert manager.config.llm_model == "deepseek-chat"
            
            # 应该创建配置文件
            assert config_path.exists()
    
    def test_load_config_from_file(self):
        """测试从文件加载配置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            
            # 创建配置文件
            config_data = {
                "llm_model": "gpt-4",
                "retrieval_top_k": 10,
                "intervention_threshold": 180
            }
            
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f)
            
            # 加载配置
            manager = ConfigManager(str(config_path))
            
            assert manager.config.llm_model == "gpt-4"
            assert manager.config.retrieval_top_k == 10
            assert manager.config.intervention_threshold == 180
            # 未指定的配置应使用默认值
            assert manager.config.embedding_model == "bge-small-zh-v1.5"
    
    def test_save_config(self):
        """测试保存配置到文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            
            manager = ConfigManager(str(config_path))
            manager.config.llm_model = "gpt-4"
            manager.config.retrieval_top_k = 10
            
            manager.save_config()
            
            # 验证文件内容
            with open(config_path, 'r', encoding='utf-8') as f:
                saved_data = yaml.safe_load(f)
            
            assert saved_data["llm_model"] == "gpt-4"
            assert saved_data["retrieval_top_k"] == 10
    
    @pytest.mark.asyncio
    async def test_update_config(self):
        """测试更新配置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            
            manager = ConfigManager(str(config_path))
            
            # 更新配置
            await manager.update_config({
                "llm_model": "claude-3",
                "retrieval_top_k": 8
            })
            
            # 验证配置已更新
            assert manager.config.llm_model == "claude-3"
            assert manager.config.retrieval_top_k == 8
            
            # 验证文件已更新
            with open(config_path, 'r', encoding='utf-8') as f:
                saved_data = yaml.safe_load(f)
            
            assert saved_data["llm_model"] == "claude-3"
            assert saved_data["retrieval_top_k"] == 8
    
    def test_env_override_on_load(self):
        """测试环境变量覆盖配置文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            
            # 创建配置文件
            config_data = {
                "llm_model": "gpt-4",
                "retrieval_top_k": 10
            }
            
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f)
            
            # 设置环境变量
            os.environ["WAYFARE_LLM_MODEL"] = "claude-3"
            os.environ["WAYFARE_RETRIEVAL_TOP_K"] = "15"
            
            try:
                # 加载配置
                manager = ConfigManager(str(config_path))
                
                # 环境变量应该覆盖文件配置
                assert manager.config.llm_model == "claude-3"
                assert manager.config.retrieval_top_k == 15
            finally:
                # 清理环境变量
                del os.environ["WAYFARE_LLM_MODEL"]
                del os.environ["WAYFARE_RETRIEVAL_TOP_K"]
    
    def test_env_override_on_default_config(self):
        """测试环境变量覆盖默认配置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            
            # 设置环境变量
            os.environ["WAYFARE_LLM_MODEL"] = "claude-3"
            os.environ["WAYFARE_INTERVENTION_THRESHOLD"] = "200"
            
            try:
                # 加载配置（文件不存在，使用默认配置）
                manager = ConfigManager(str(config_path))
                
                # 环境变量应该覆盖默认配置
                assert manager.config.llm_model == "claude-3"
                assert manager.config.intervention_threshold == 200
                # 未设置环境变量的配置应使用默认值
                assert manager.config.embedding_model == "bge-small-zh-v1.5"
            finally:
                # 清理环境变量
                del os.environ["WAYFARE_LLM_MODEL"]
                del os.environ["WAYFARE_INTERVENTION_THRESHOLD"]
    
    def test_env_override_type_conversion(self):
        """测试环境变量类型转换"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            
            # 设置不同类型的环境变量
            os.environ["WAYFARE_RETRIEVAL_TOP_K"] = "20"  # int
            os.environ["WAYFARE_QDRANT_URL"] = "http://example.com:6333"  # str
            
            try:
                manager = ConfigManager(str(config_path))
                
                # 验证类型转换
                assert manager.config.retrieval_top_k == 20
                assert isinstance(manager.config.retrieval_top_k, int)
                assert manager.config.qdrant_url == "http://example.com:6333"
                assert isinstance(manager.config.qdrant_url, str)
            finally:
                # 清理环境变量
                del os.environ["WAYFARE_RETRIEVAL_TOP_K"]
                del os.environ["WAYFARE_QDRANT_URL"]
    
    def test_get_config(self):
        """测试获取配置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            
            manager = ConfigManager(str(config_path))
            config = manager.get_config()
            
            assert isinstance(config, WayFareConfig)
            assert config.llm_model == "deepseek-chat"
    
    def test_config_directory_creation(self):
        """测试配置目录自动创建"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 使用嵌套目录路径
            config_path = Path(tmpdir) / "nested" / "dir" / "config.yaml"
            
            manager = ConfigManager(str(config_path))
            
            # 目录应该被自动创建
            assert config_path.parent.exists()
            assert config_path.exists()
