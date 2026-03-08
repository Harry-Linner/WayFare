"""
LLM Provider集成模块

复用nanobot的LLMProvider系统，配置SiliconFlow provider访问DeepSeek-V3.2模型。
实现错误处理和重试机制。
"""

import os
import asyncio
from typing import Optional, Dict, Any, List
from loguru import logger

# 复用nanobot的LLM Provider系统
from nanobot.providers.base import LLMProvider, LLMResponse
from nanobot.providers.litellm_provider import LiteLLMProvider


class WayFareLLMProvider:
    """
    WayFare LLM Provider封装类
    
    封装nanobot的LiteLLMProvider，提供：
    - SiliconFlow + DeepSeek-V3.2配置
    - 错误处理和重试机制
    - 统一的调用接口
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "deepseek-chat",
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: float = 60.0
    ):
        """
        初始化LLM Provider
        
        Args:
            api_key: SiliconFlow API密钥，如果为None则从环境变量SILICONFLOW_API_KEY读取
            model: 模型名称，默认为deepseek-chat
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            timeout: 请求超时时间（秒）
        """
        # 获取API密钥
        self.api_key = api_key or os.getenv("SILICONFLOW_API_KEY")
        if not self.api_key:
            logger.warning(
                "SiliconFlow API key not found. "
                "Please set SILICONFLOW_API_KEY environment variable."
            )
        
        self.model = model
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        
        # 初始化LiteLLM Provider
        # SiliconFlow使用siliconflow前缀
        self.provider: LLMProvider = LiteLLMProvider(
            api_key=self.api_key,
            default_model=f"siliconflow/{self.model}",
            provider_name="siliconflow"
        )
        
        logger.info(
            f"Initialized WayFare LLM Provider with model: {self.model}"
        )
    
    async def generate(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> LLMResponse:
        """
        生成LLM响应（带重试机制）
        
        Args:
            messages: 消息列表，格式为[{"role": "user", "content": "..."}]
            max_tokens: 最大生成token数
            temperature: 采样温度
            tools: 可选的工具定义列表
            
        Returns:
            LLMResponse对象
            
        Raises:
            Exception: 重试耗尽后仍然失败
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                # 使用asyncio.wait_for添加超时控制
                response = await asyncio.wait_for(
                    self.provider.chat(
                        messages=messages,
                        tools=tools,
                        max_tokens=max_tokens,
                        temperature=temperature
                    ),
                    timeout=self.timeout
                )
                
                # 检查响应是否包含错误
                if response.finish_reason == "error":
                    raise Exception(f"LLM returned error: {response.content}")
                
                logger.debug(
                    f"LLM generation successful. "
                    f"Tokens: {response.usage.get('total_tokens', 'N/A')}"
                )
                
                return response
                
            except asyncio.TimeoutError as e:
                last_error = e
                logger.warning(
                    f"LLM request timeout (attempt {attempt + 1}/{self.max_retries})"
                )
                
            except Exception as e:
                last_error = e
                logger.warning(
                    f"LLM request failed (attempt {attempt + 1}/{self.max_retries}): {str(e)}"
                )
            
            # 如果不是最后一次尝试，等待后重试
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay * (attempt + 1))  # 指数退避
        
        # 所有重试都失败
        error_msg = f"LLM request failed after {self.max_retries} attempts: {str(last_error)}"
        logger.error(error_msg)
        
        # 返回错误响应而不是抛出异常，让调用者决定如何处理
        return LLMResponse(
            content=f"抱歉，AI服务暂时不可用。请稍后重试。\n错误详情: {str(last_error)}",
            finish_reason="error"
        )
    
    async def generate_simple(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7
    ) -> str:
        """
        简化的生成接口（单轮对话）
        
        Args:
            prompt: 用户提示词
            system_prompt: 可选的系统提示词
            max_tokens: 最大生成token数
            temperature: 采样温度
            
        Returns:
            生成的文本内容
        """
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        response = await self.generate(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return response.content or ""
    
    def get_model_name(self) -> str:
        """
        获取当前使用的模型名称
        
        Returns:
            模型名称
        """
        return self.model
    
    def update_config(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_retries: Optional[int] = None,
        retry_delay: Optional[float] = None,
        timeout: Optional[float] = None
    ):
        """
        更新配置
        
        Args:
            api_key: 新的API密钥
            model: 新的模型名称
            max_retries: 新的最大重试次数
            retry_delay: 新的重试延迟
            timeout: 新的超时时间
        """
        if api_key is not None:
            self.api_key = api_key
        
        if model is not None:
            self.model = model
        
        if max_retries is not None:
            self.max_retries = max_retries
        
        if retry_delay is not None:
            self.retry_delay = retry_delay
        
        if timeout is not None:
            self.timeout = timeout
        
        # 重新初始化provider
        self.provider = LiteLLMProvider(
            api_key=self.api_key,
            default_model=f"siliconflow/{self.model}",
            provider_name="siliconflow"
        )
        
        logger.info(f"Updated LLM Provider configuration: model={self.model}")


def create_llm_provider(
    api_key: Optional[str] = None,
    model: str = "deepseek-chat",
    max_retries: int = 3,
    retry_delay: float = 1.0,
    timeout: float = 60.0
) -> WayFareLLMProvider:
    """
    工厂函数：创建LLM Provider实例
    
    Args:
        api_key: SiliconFlow API密钥
        model: 模型名称
        max_retries: 最大重试次数
        retry_delay: 重试延迟（秒）
        timeout: 请求超时时间（秒）
        
    Returns:
        WayFareLLMProvider实例
    """
    return WayFareLLMProvider(
        api_key=api_key,
        model=model,
        max_retries=max_retries,
        retry_delay=retry_delay,
        timeout=timeout
    )
