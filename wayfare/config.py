"""
配置管理模块

实现WayFareConfig类（继承nanobot的BaseConfig）和ConfigManager类，
支持YAML配置文件加载、保存和环境变量覆盖。
"""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import Field, ConfigDict

# 复用nanobot的配置系统
from nanobot.config.schema import Base


class WayFareConfig(Base):
    """
    WayFare配置类，继承nanobot的BaseConfig
    
    支持通过环境变量覆盖配置（WAYFARE_*前缀）
    """
    
    # LLM配置
    llm_model: str = Field(
        default="deepseek-chat",
        description="LLM模型名称"
    )
    llm_api_key: Optional[str] = Field(
        default=None,
        description="LLM API密钥（SiliconFlow）"
    )
    llm_max_retries: int = Field(
        default=3,
        description="LLM请求最大重试次数"
    )
    llm_retry_delay: float = Field(
        default=1.0,
        description="LLM请求重试延迟（秒）"
    )
    llm_timeout: float = Field(
        default=60.0,
        description="LLM请求超时时间（秒）"
    )
    llm_max_tokens: int = Field(
        default=4096,
        description="LLM生成最大token数"
    )
    llm_temperature: float = Field(
        default=0.7,
        description="LLM采样温度"
    )
    
    # Embedding配置
    embedding_model: str = Field(
        default="bge-small-zh-v1.5",
        description="Embedding模型名称"
    )
    embedding_model_path: str = Field(
        default="./models/bge-small-zh-v1.5.onnx",
        description="ONNX模型路径"
    )
    
    # Qdrant配置
    qdrant_url: str = Field(
        default="http://localhost:6333",
        description="Qdrant服务地址"
    )
    qdrant_collection: str = Field(
        default="documents",
        description="Qdrant collection名称"
    )
    
    # 检索配置
    retrieval_top_k: int = Field(
        default=5,
        description="检索返回的top-k结果数"
    )
    chunk_size: int = Field(
        default=300,
        description="文档分块大小（字符数）"
    )
    chunk_overlap: int = Field(
        default=50,
        description="分块重叠大小（字符数）"
    )
    
    # 行为分析配置
    intervention_threshold: int = Field(
        default=120,
        description="主动干预阈值（秒）"
    )
    
    # 数据库配置
    db_path: str = Field(
        default=".wayfare/wayfare.db",
        description="SQLite数据库路径"
    )
    
    model_config = ConfigDict(
        env_prefix="WAYFARE_",
        case_sensitive=False
    )


class ConfigManager:
    """
    配置管理器
    
    负责加载、保存和更新配置文件，支持环境变量覆盖。
    """
    
    def __init__(self, config_path: str = ".wayfare/config.yaml"):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，默认为.wayfare/config.yaml
        """
        self.config_path = Path(config_path)
        self.config: Optional[WayFareConfig] = None
        
        # 加载配置
        self.load_config()
    
    def load_config(self):
        """
        加载配置文件
        
        如果配置文件存在，从文件加载；否则使用默认配置并创建配置文件。
        环境变量会覆盖文件中的配置。
        """
        if self.config_path.exists():
            # 从文件加载配置
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_dict = yaml.safe_load(f) or {}
            
            # 应用环境变量覆盖
            config_dict = self._apply_env_overrides(config_dict)
            
            # 创建配置对象
            self.config = WayFareConfig(**config_dict)
        else:
            # 使用默认配置
            self.config = WayFareConfig()
            
            # 应用环境变量覆盖
            self._apply_env_to_config()
            
            # 保存默认配置到文件
            self.save_config()
    
    def _apply_env_overrides(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        应用环境变量覆盖
        
        Args:
            config_dict: 配置字典
            
        Returns:
            应用环境变量后的配置字典
        """
        # 获取所有WAYFARE_*环境变量
        env_prefix = "WAYFARE_"
        
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                # 转换环境变量名为配置键名
                # 例如: WAYFARE_LLM_MODEL -> llm_model
                config_key = key[len(env_prefix):].lower()
                
                # 尝试转换类型
                if config_key in config_dict:
                    original_type = type(config_dict[config_key])
                    try:
                        if original_type == int:
                            config_dict[config_key] = int(value)
                        elif original_type == float:
                            config_dict[config_key] = float(value)
                        elif original_type == bool:
                            config_dict[config_key] = value.lower() in ('true', '1', 'yes')
                        else:
                            config_dict[config_key] = value
                    except (ValueError, TypeError):
                        config_dict[config_key] = value
                else:
                    # 新的配置项，直接添加
                    config_dict[config_key] = value
        
        return config_dict
    
    def _apply_env_to_config(self):
        """
        将环境变量应用到已创建的配置对象
        """
        env_prefix = "WAYFARE_"
        
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                config_key = key[len(env_prefix):].lower()
                
                if hasattr(self.config, config_key):
                    # 获取字段类型 (Pydantic V2 - 从类访问model_fields)
                    field_info = self.config.__class__.model_fields.get(config_key)
                    if field_info:
                        field_type = field_info.annotation
                        
                        try:
                            if field_type == int:
                                setattr(self.config, config_key, int(value))
                            elif field_type == float:
                                setattr(self.config, config_key, float(value))
                            elif field_type == bool:
                                setattr(self.config, config_key, value.lower() in ('true', '1', 'yes'))
                            else:
                                setattr(self.config, config_key, value)
                        except (ValueError, TypeError):
                            setattr(self.config, config_key, value)
    
    def save_config(self):
        """
        保存配置到文件
        
        确保目录存在,然后将配置序列化为YAML格式保存。
        """
        # 确保目录存在
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 将配置转换为字典 (Pydantic V2)
        config_dict = self.config.model_dump()
        
        # 保存到YAML文件
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(
                config_dict,
                f,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False
            )
    
    async def update_config(self, updates: Dict[str, Any]):
        """
        更新配置
        
        Args:
            updates: 要更新的配置项字典
        """
        # 更新配置对象
        for key, value in updates.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        
        # 保存到文件
        self.save_config()
    
    def get_config(self) -> WayFareConfig:
        """
        获取当前配置
        
        Returns:
            当前的WayFareConfig对象
        """
        return self.config
