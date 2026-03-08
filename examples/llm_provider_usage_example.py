"""
LLM Provider使用示例

演示如何使用WayFare的LLM Provider模块进行各种LLM调用。
"""

import asyncio
import os
from wayfare.llm_provider import create_llm_provider, WayFareLLMProvider
from wayfare.config import ConfigManager


async def example_1_basic_usage():
    """示例1: 基本使用"""
    print("=" * 60)
    print("示例1: 基本使用")
    print("=" * 60)
    
    # 创建provider（从环境变量读取API密钥）
    provider = create_llm_provider()
    
    # 简单的单轮对话
    response = await provider.generate_simple(
        prompt="用一句话解释什么是费曼技巧",
        system_prompt="你是一个学习助手，用简洁的语言解释概念。"
    )
    
    print(f"问题: 用一句话解释什么是费曼技巧")
    print(f"回答: {response}")
    print()


async def example_2_multi_turn_conversation():
    """示例2: 多轮对话"""
    print("=" * 60)
    print("示例2: 多轮对话")
    print("=" * 60)
    
    provider = create_llm_provider()
    
    # 构建对话历史
    messages = [
        {"role": "system", "content": "你是一个学习助手。"},
        {"role": "user", "content": "什么是费曼技巧？"}
    ]
    
    # 第一轮
    print("用户: 什么是费曼技巧？")
    response1 = await provider.generate(messages, max_tokens=500)
    print(f"助手: {response1.content}")
    print(f"Token使用: {response1.usage.get('total_tokens', 'N/A')}")
    print()
    
    # 添加助手回复到历史
    messages.append({
        "role": "assistant",
        "content": response1.content
    })
    
    # 第二轮
    messages.append({
        "role": "user",
        "content": "能举个具体的例子吗？"
    })
    
    print("用户: 能举个具体的例子吗？")
    response2 = await provider.generate(messages, max_tokens=500)
    print(f"助手: {response2.content}")
    print(f"Token使用: {response2.usage.get('total_tokens', 'N/A')}")
    print()


async def example_3_with_config():
    """示例3: 使用配置文件"""
    print("=" * 60)
    print("示例3: 使用配置文件")
    print("=" * 60)
    
    # 从配置文件加载配置
    config_manager = ConfigManager()
    config = config_manager.get_config()
    
    # 使用配置创建provider
    provider = create_llm_provider(
        api_key=config.llm_api_key or os.getenv("SILICONFLOW_API_KEY"),
        model=config.llm_model,
        max_retries=config.llm_max_retries,
        retry_delay=config.llm_retry_delay,
        timeout=config.llm_timeout
    )
    
    print(f"配置的模型: {provider.get_model_name()}")
    print(f"最大重试次数: {provider.max_retries}")
    print(f"超时时间: {provider.timeout}秒")
    print()
    
    # 使用配置的参数生成
    response = await provider.generate_simple(
        prompt="解释一下主动学习的概念",
        max_tokens=config.llm_max_tokens,
        temperature=config.llm_temperature
    )
    
    print(f"回答: {response}")
    print()


async def example_4_error_handling():
    """示例4: 错误处理"""
    print("=" * 60)
    print("示例4: 错误处理")
    print("=" * 60)
    
    # 使用无效的API密钥测试错误处理
    provider = create_llm_provider(
        api_key="invalid_key_for_testing",
        max_retries=2,
        retry_delay=0.5
    )
    
    print("使用无效API密钥测试错误处理...")
    response = await provider.generate_simple(
        prompt="测试",
        system_prompt="测试系统"
    )
    
    # 检查是否是错误响应
    if "错误" in response or "error" in response.lower():
        print(f"✓ 错误被正确处理: {response[:100]}...")
    else:
        print(f"响应: {response}")
    print()


async def example_5_batch_generation():
    """示例5: 批量生成"""
    print("=" * 60)
    print("示例5: 批量生成")
    print("=" * 60)
    
    provider = create_llm_provider()
    
    # 准备多个提示
    prompts = [
        "用一句话解释什么是费曼技巧",
        "用一句话解释什么是间隔重复",
        "用一句话解释什么是主动回忆"
    ]
    
    print("批量生成3个解释...")
    
    # 并发执行
    tasks = [
        provider.generate_simple(
            prompt=prompt,
            system_prompt="你是一个学习助手，用一句话简洁地解释概念。",
            max_tokens=100
        )
        for prompt in prompts
    ]
    
    results = await asyncio.gather(*tasks)
    
    for prompt, result in zip(prompts, results):
        print(f"\n问题: {prompt}")
        print(f"回答: {result}")
    print()


async def example_6_temperature_comparison():
    """示例6: 不同temperature的对比"""
    print("=" * 60)
    print("示例6: 不同temperature的对比")
    print("=" * 60)
    
    provider = create_llm_provider()
    
    prompt = "用一句话描述学习的本质"
    system_prompt = "你是一个哲学家。"
    
    temperatures = [0.0, 0.5, 1.0]
    
    for temp in temperatures:
        print(f"\nTemperature = {temp}:")
        response = await provider.generate_simple(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temp,
            max_tokens=100
        )
        print(f"回答: {response}")
    print()


async def example_7_annotation_generation():
    """示例7: 批注生成场景"""
    print("=" * 60)
    print("示例7: 批注生成场景（模拟）")
    print("=" * 60)
    
    provider = create_llm_provider()
    
    # 模拟用户选中的文本
    selected_text = """
    费曼技巧是一种学习方法，通过用简单的语言解释复杂的概念来检验自己是否真正理解。
    """
    
    # 模拟RAG检索到的相关上下文
    context = """
    [片段1] 理查德·费曼是著名的物理学家，他提出了一种独特的学习方法。
    [片段2] 这种方法的核心是"教学相长"，通过教别人来加深自己的理解。
    [片段3] 如果你不能用简单的语言解释一个概念，说明你还没有真正理解它。
    """
    
    # 构建批注生成的prompt
    prompt = f"""用户选中的文本：
{selected_text}

相关上下文：
{context}

请用简单易懂的语言解释这段内容，包括：
1. 核心概念是什么
2. 用类比或例子说明
3. 为什么这个概念重要

保持简洁，不超过200字。"""
    
    print("生成批注...")
    annotation = await provider.generate_simple(
        prompt=prompt,
        system_prompt="你是WayFare学习助手，使用费曼技巧帮助学生理解概念。",
        max_tokens=300,
        temperature=0.7
    )
    
    print(f"\n批注内容:\n{annotation}")
    print()


async def example_8_dynamic_config_update():
    """示例8: 动态更新配置"""
    print("=" * 60)
    print("示例8: 动态更新配置")
    print("=" * 60)
    
    provider = create_llm_provider(
        model="deepseek-chat",
        max_retries=3,
        timeout=60.0
    )
    
    print(f"初始配置:")
    print(f"  模型: {provider.get_model_name()}")
    print(f"  最大重试: {provider.max_retries}")
    print(f"  超时: {provider.timeout}秒")
    print()
    
    # 更新配置
    provider.update_config(
        model="deepseek-chat",
        max_retries=5,
        timeout=120.0
    )
    
    print(f"更新后的配置:")
    print(f"  模型: {provider.get_model_name()}")
    print(f"  最大重试: {provider.max_retries}")
    print(f"  超时: {provider.timeout}秒")
    print()


async def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("WayFare LLM Provider 使用示例")
    print("=" * 60 + "\n")
    
    # 检查API密钥
    api_key = os.getenv("SILICONFLOW_API_KEY")
    if not api_key:
        print("⚠️  警告: 未设置SILICONFLOW_API_KEY环境变量")
        print("某些示例可能无法正常运行。")
        print("请设置环境变量: export SILICONFLOW_API_KEY='your_api_key'")
        print()
    
    try:
        # 运行示例（跳过需要真实API的示例）
        await example_8_dynamic_config_update()
        
        # 如果有API密钥，运行需要真实调用的示例
        if api_key:
            await example_1_basic_usage()
            await example_2_multi_turn_conversation()
            await example_3_with_config()
            await example_5_batch_generation()
            await example_6_temperature_comparison()
            await example_7_annotation_generation()
        
        # 错误处理示例（不需要真实API）
        await example_4_error_handling()
        
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("示例运行完成")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
