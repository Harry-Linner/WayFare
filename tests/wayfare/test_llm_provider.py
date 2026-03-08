"""
LLM Provider模块测试

测试WayFareLLMProvider的功能，包括：
- 基本的LLM调用
- 错误处理和重试机制
- 配置更新
- 超时控制
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from wayfare.llm_provider import WayFareLLMProvider, create_llm_provider
from nanobot.providers.base import LLMResponse


class TestWayFareLLMProvider:
    """测试WayFareLLMProvider类"""
    
    @pytest.fixture
    def mock_api_key(self):
        """模拟API密钥"""
        return "test_api_key_12345"
    
    @pytest.fixture
    def provider(self, mock_api_key):
        """创建测试用的provider实例"""
        return WayFareLLMProvider(
            api_key=mock_api_key,
            model="deepseek-chat",
            max_retries=2,
            retry_delay=0.1,  # 测试时使用短延迟
            timeout=5.0
        )
    
    def test_initialization(self, provider, mock_api_key):
        """测试初始化"""
        assert provider.api_key == mock_api_key
        assert provider.model == "deepseek-chat"
        assert provider.max_retries == 2
        assert provider.retry_delay == 0.1
        assert provider.timeout == 5.0
        assert provider.provider is not None
    
    def test_initialization_without_api_key(self):
        """测试没有API密钥的初始化"""
        with patch.dict('os.environ', {}, clear=True):
            provider = WayFareLLMProvider()
            assert provider.api_key is None
    
    def test_initialization_from_env(self):
        """测试从环境变量读取API密钥"""
        test_key = "env_api_key_67890"
        with patch.dict('os.environ', {'SILICONFLOW_API_KEY': test_key}):
            provider = WayFareLLMProvider()
            assert provider.api_key == test_key
    
    @pytest.mark.asyncio
    async def test_generate_success(self, provider):
        """测试成功的LLM调用"""
        # Mock LiteLLMProvider的chat方法
        mock_response = LLMResponse(
            content="这是测试响应",
            finish_reason="stop",
            usage={"total_tokens": 100}
        )
        
        with patch.object(provider.provider, 'chat', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_response
            
            messages = [{"role": "user", "content": "测试消息"}]
            response = await provider.generate(messages)
            
            assert response.content == "这是测试响应"
            assert response.finish_reason == "stop"
            assert response.usage["total_tokens"] == 100
            
            # 验证调用参数
            mock_chat.assert_called_once()
            call_kwargs = mock_chat.call_args[1]
            assert call_kwargs["messages"] == messages
            assert call_kwargs["max_tokens"] == 4096
            assert call_kwargs["temperature"] == 0.7
    
    @pytest.mark.asyncio
    async def test_generate_with_custom_params(self, provider):
        """测试使用自定义参数的LLM调用"""
        mock_response = LLMResponse(content="响应", finish_reason="stop")
        
        with patch.object(provider.provider, 'chat', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_response
            
            messages = [{"role": "user", "content": "测试"}]
            tools = [{"type": "function", "function": {"name": "test"}}]
            
            await provider.generate(
                messages=messages,
                max_tokens=1000,
                temperature=0.5,
                tools=tools
            )
            
            call_kwargs = mock_chat.call_args[1]
            assert call_kwargs["max_tokens"] == 1000
            assert call_kwargs["temperature"] == 0.5
            assert call_kwargs["tools"] == tools
    
    @pytest.mark.asyncio
    async def test_generate_retry_on_failure(self, provider):
        """测试失败时的重试机制"""
        # 第一次调用失败，第二次成功
        mock_response = LLMResponse(content="成功响应", finish_reason="stop")
        
        with patch.object(provider.provider, 'chat', new_callable=AsyncMock) as mock_chat:
            mock_chat.side_effect = [
                Exception("第一次失败"),
                mock_response
            ]
            
            messages = [{"role": "user", "content": "测试"}]
            response = await provider.generate(messages)
            
            # 应该重试1次后成功
            assert mock_chat.call_count == 2
            assert response.content == "成功响应"
    
    @pytest.mark.asyncio
    async def test_generate_all_retries_failed(self, provider):
        """测试所有重试都失败的情况"""
        with patch.object(provider.provider, 'chat', new_callable=AsyncMock) as mock_chat:
            mock_chat.side_effect = Exception("持续失败")
            
            messages = [{"role": "user", "content": "测试"}]
            response = await provider.generate(messages)
            
            # 应该尝试max_retries次
            assert mock_chat.call_count == provider.max_retries
            
            # 应该返回错误响应
            assert response.finish_reason == "error"
            assert "AI服务暂时不可用" in response.content
    
    @pytest.mark.asyncio
    async def test_generate_timeout(self, provider):
        """测试超时处理"""
        async def slow_response(*args, **kwargs):
            await asyncio.sleep(10)  # 超过timeout时间
            return LLMResponse(content="不应该返回", finish_reason="stop")
        
        with patch.object(provider.provider, 'chat', new_callable=AsyncMock) as mock_chat:
            mock_chat.side_effect = slow_response
            
            messages = [{"role": "user", "content": "测试"}]
            response = await provider.generate(messages)
            
            # 应该返回超时错误
            assert response.finish_reason == "error"
            assert "AI服务暂时不可用" in response.content
    
    @pytest.mark.asyncio
    async def test_generate_error_response(self, provider):
        """测试LLM返回错误响应"""
        mock_response = LLMResponse(
            content="API错误: 配额超限",
            finish_reason="error"
        )
        
        with patch.object(provider.provider, 'chat', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_response
            
            messages = [{"role": "user", "content": "测试"}]
            
            # 应该返回错误响应（不抛出异常）
            response = await provider.generate(messages)
            
            # 验证返回了错误响应
            assert response.finish_reason == "error"
            assert "AI服务暂时不可用" in response.content
    
    @pytest.mark.asyncio
    async def test_generate_simple(self, provider):
        """测试简化的生成接口"""
        mock_response = LLMResponse(
            content="简单响应",
            finish_reason="stop"
        )
        
        with patch.object(provider.provider, 'chat', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_response
            
            content = await provider.generate_simple(
                prompt="测试提示",
                system_prompt="系统提示"
            )
            
            assert content == "简单响应"
            
            # 验证消息格式
            call_kwargs = mock_chat.call_args[1]
            messages = call_kwargs["messages"]
            assert len(messages) == 2
            assert messages[0]["role"] == "system"
            assert messages[0]["content"] == "系统提示"
            assert messages[1]["role"] == "user"
            assert messages[1]["content"] == "测试提示"
    
    @pytest.mark.asyncio
    async def test_generate_simple_without_system_prompt(self, provider):
        """测试没有系统提示的简化接口"""
        mock_response = LLMResponse(content="响应", finish_reason="stop")
        
        with patch.object(provider.provider, 'chat', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_response
            
            content = await provider.generate_simple(prompt="测试")
            
            # 应该只有一条用户消息
            call_kwargs = mock_chat.call_args[1]
            messages = call_kwargs["messages"]
            assert len(messages) == 1
            assert messages[0]["role"] == "user"
    
    def test_get_model_name(self, provider):
        """测试获取模型名称"""
        assert provider.get_model_name() == "deepseek-chat"
    
    def test_update_config(self, provider):
        """测试更新配置"""
        provider.update_config(
            model="deepseek-v3",
            max_retries=5,
            retry_delay=2.0,
            timeout=120.0
        )
        
        assert provider.model == "deepseek-v3"
        assert provider.max_retries == 5
        assert provider.retry_delay == 2.0
        assert provider.timeout == 120.0
    
    def test_update_config_partial(self, provider):
        """测试部分更新配置"""
        original_model = provider.model
        original_timeout = provider.timeout
        
        provider.update_config(max_retries=10)
        
        # 只有max_retries应该改变
        assert provider.model == original_model
        assert provider.timeout == original_timeout
        assert provider.max_retries == 10


class TestCreateLLMProvider:
    """测试工厂函数"""
    
    def test_create_with_defaults(self):
        """测试使用默认参数创建"""
        with patch.dict('os.environ', {'SILICONFLOW_API_KEY': 'test_key'}):
            provider = create_llm_provider()
            
            assert isinstance(provider, WayFareLLMProvider)
            assert provider.model == "deepseek-chat"
            assert provider.max_retries == 3
    
    def test_create_with_custom_params(self):
        """测试使用自定义参数创建"""
        provider = create_llm_provider(
            api_key="custom_key",
            model="custom-model",
            max_retries=5,
            retry_delay=2.0,
            timeout=90.0
        )
        
        assert provider.api_key == "custom_key"
        assert provider.model == "custom-model"
        assert provider.max_retries == 5
        assert provider.retry_delay == 2.0
        assert provider.timeout == 90.0


class TestIntegration:
    """集成测试（需要真实的API密钥）"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_llm_call(self):
        """测试真实的LLM调用（需要API密钥）"""
        import os
        
        api_key = os.getenv("SILICONFLOW_API_KEY")
        if not api_key:
            pytest.skip("需要设置SILICONFLOW_API_KEY环境变量")
        
        provider = create_llm_provider(api_key=api_key)
        
        response = await provider.generate_simple(
            prompt="说'你好'",
            system_prompt="你是一个友好的助手。"
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        print(f"LLM响应: {response}")


def pytest_configure(config):
    """配置pytest"""
    config.addinivalue_line(
        "markers",
        "integration: 标记为集成测试（需要真实的API密钥）"
    )
