"""
Context Builder使用示例

演示如何使用WayFare Context Builder构建批注生成的LLM上下文。
"""

import asyncio
from wayfare.context_builder import create_context_builder
from wayfare.llm_provider import create_llm_provider


async def example_explanation_annotation():
    """示例：生成explanation类型的批注"""
    print("=" * 60)
    print("示例1: 生成explanation类型的批注")
    print("=" * 60)
    
    # 创建Context Builder
    builder = create_context_builder()
    
    # 用户选中的文本
    selected_text = "费曼技巧是一种学习方法，通过用简单语言解释复杂概念来检验理解程度。"
    
    # RAG检索到的相关上下文
    context_docs = [
        "费曼技巧由诺贝尔物理学奖得主理查德·费曼提出，他以能够用简单语言解释复杂物理概念而闻名。",
        "这种方法的核心是：如果你不能用简单的语言解释一个概念，说明你还没有真正理解它。",
        "费曼技巧包括四个步骤：选择概念、教授他人、识别知识盲区、简化和类比。"
    ]
    
    # 构建消息
    messages = builder.build_messages(
        selected_text=selected_text,
        annotation_type="explanation",
        context_docs=context_docs
    )
    
    print("\n构建的消息:")
    print(f"系统提示词: {messages[0]['content'][:100]}...")
    print(f"\n用户消息: {messages[1]['content'][:200]}...")
    
    # 如果有LLM provider，可以直接调用
    # llm = create_llm_provider()
    # response = await llm.generate(messages)
    # print(f"\nLLM响应: {response.content}")


async def example_question_annotation():
    """示例：生成question类型的批注"""
    print("\n" + "=" * 60)
    print("示例2: 生成question类型的批注")
    print("=" * 60)
    
    builder = create_context_builder()
    
    selected_text = "机器学习是人工智能的一个分支，它使计算机能够从数据中学习而无需显式编程。"
    
    context_docs = [
        "机器学习算法可以分为监督学习、无监督学习和强化学习三大类。",
        "深度学习是机器学习的一个子领域，使用多层神经网络来学习数据的层次化表示。"
    ]
    
    messages = builder.build_messages(
        selected_text=selected_text,
        annotation_type="question",
        context_docs=context_docs
    )
    
    print("\n构建的消息:")
    print(f"批注类型: question")
    print(f"上下文文档数量: {len(context_docs)}")
    print(f"用户消息长度: {len(messages[1]['content'])} 字符")


async def example_summary_annotation():
    """示例：生成summary类型的批注"""
    print("\n" + "=" * 60)
    print("示例3: 生成summary类型的批注")
    print("=" * 60)
    
    builder = create_context_builder()
    
    selected_text = """
    深度学习是机器学习的一个子领域，它使用多层神经网络来学习数据的层次化表示。
    深度学习在图像识别、自然语言处理、语音识别等领域取得了突破性进展。
    卷积神经网络（CNN）特别适合处理图像数据，而循环神经网络（RNN）适合处理序列数据。
    """
    
    context_docs = [
        "深度学习的成功得益于大规模数据集、强大的计算能力和改进的算法。",
        "Transformer架构的出现进一步推动了自然语言处理领域的发展。"
    ]
    
    messages = builder.build_messages(
        selected_text=selected_text,
        annotation_type="summary",
        context_docs=context_docs
    )
    
    print("\n构建的消息:")
    print(f"批注类型: summary")
    print(f"选中文本长度: {len(selected_text)} 字符")


async def example_custom_system_prompt():
    """示例：使用自定义系统提示词"""
    print("\n" + "=" * 60)
    print("示例4: 使用自定义系统提示词")
    print("=" * 60)
    
    builder = create_context_builder()
    
    custom_system_prompt = """你是一个专业的数学老师，擅长用生动的例子解释抽象的数学概念。
你的回答应该：
- 使用日常生活中的例子
- 避免使用过于专业的术语
- 循序渐进地引导学生理解"""
    
    selected_text = "导数表示函数在某一点的瞬时变化率。"
    context_docs = ["导数的几何意义是曲线在该点的切线斜率。"]
    
    messages = builder.build_messages(
        selected_text=selected_text,
        annotation_type="explanation",
        context_docs=context_docs,
        system_prompt=custom_system_prompt
    )
    
    print("\n使用了自定义系统提示词")
    print(f"系统提示词: {messages[0]['content'][:100]}...")


async def example_simple_message():
    """示例：构建简单消息"""
    print("\n" + "=" * 60)
    print("示例5: 构建简单消息（单轮对话）")
    print("=" * 60)
    
    builder = create_context_builder()
    
    prompt = "请解释什么是机器学习，并举一个简单的例子。"
    
    messages = builder.build_simple_message(prompt)
    
    print("\n构建的简单消息:")
    print(f"消息数量: {len(messages)}")
    print(f"用户提示词: {messages[1]['content']}")


async def example_update_template():
    """示例：更新Prompt模板"""
    print("\n" + "=" * 60)
    print("示例6: 更新Prompt模板")
    print("=" * 60)
    
    builder = create_context_builder()
    
    # 查看原始模板
    original_template = builder.get_prompt_template("explanation")
    print(f"\n原始explanation模板:\n{original_template[:100]}...")
    
    # 更新模板
    new_template = """用户选中的文本：
{selected_text}

相关上下文：
{context}

请用通俗易懂的语言解释这段内容，要求：
1. 使用生活中的例子
2. 避免专业术语
3. 不超过150字

开始解释："""
    
    builder.update_prompt_template("explanation", new_template)
    
    # 验证更新
    updated_template = builder.get_prompt_template("explanation")
    print(f"\n更新后的模板:\n{updated_template[:100]}...")


async def example_get_available_types():
    """示例：获取可用的批注类型"""
    print("\n" + "=" * 60)
    print("示例7: 获取可用的批注类型")
    print("=" * 60)
    
    builder = create_context_builder()
    
    types = builder.get_available_types()
    print(f"\n可用的批注类型: {types}")
    
    # 查看每种类型的模板
    for annotation_type in types:
        template = builder.get_prompt_template(annotation_type)
        print(f"\n{annotation_type} 模板预览:")
        print(template[:150] + "...")


async def example_empty_context():
    """示例：处理空上下文"""
    print("\n" + "=" * 60)
    print("示例8: 处理空上下文文档")
    print("=" * 60)
    
    builder = create_context_builder()
    
    selected_text = "这是一段没有相关上下文的文本。"
    context_docs = []  # 空上下文
    
    messages = builder.build_messages(
        selected_text=selected_text,
        annotation_type="explanation",
        context_docs=context_docs
    )
    
    print("\n当上下文为空时:")
    print(f"用户消息中包含: '（无相关上下文）'")
    print(f"验证: {'（无相关上下文）' in messages[1]['content']}")


async def example_integration_with_llm():
    """示例：与LLM Provider集成"""
    print("\n" + "=" * 60)
    print("示例9: 与LLM Provider集成（完整流程）")
    print("=" * 60)
    
    # 创建Context Builder和LLM Provider
    builder = create_context_builder()
    
    # 注意：需要设置SILICONFLOW_API_KEY环境变量
    # llm = create_llm_provider()
    
    selected_text = "Python是一种高级编程语言。"
    context_docs = [
        "Python由Guido van Rossum于1991年创建。",
        "Python以其简洁的语法和强大的库生态系统而闻名。"
    ]
    
    # 构建消息
    messages = builder.build_messages(
        selected_text=selected_text,
        annotation_type="explanation",
        context_docs=context_docs
    )
    
    print("\n准备调用LLM:")
    print(f"消息数量: {len(messages)}")
    print(f"系统提示词长度: {len(messages[0]['content'])} 字符")
    print(f"用户消息长度: {len(messages[1]['content'])} 字符")
    
    # 调用LLM（需要API key）
    # response = await llm.generate(messages)
    # print(f"\nLLM响应: {response.content}")
    
    print("\n注意: 实际调用LLM需要设置SILICONFLOW_API_KEY环境变量")


async def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("WayFare Context Builder 使用示例")
    print("=" * 60)
    
    await example_explanation_annotation()
    await example_question_annotation()
    await example_summary_annotation()
    await example_custom_system_prompt()
    await example_simple_message()
    await example_update_template()
    await example_get_available_types()
    await example_empty_context()
    await example_integration_with_llm()
    
    print("\n" + "=" * 60)
    print("所有示例运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
