"""
Context Builder单元测试
"""

import pytest
from wayfare.context_builder import WayFareContextBuilder, create_context_builder


class TestWayFareContextBuilder:
    """测试WayFare Context Builder"""
    
    def test_initialization(self):
        """测试初始化"""
        builder = WayFareContextBuilder()
        assert builder is not None
        assert len(builder.PROMPT_TEMPLATES) == 3
        assert "explanation" in builder.PROMPT_TEMPLATES
        assert "question" in builder.PROMPT_TEMPLATES
        assert "summary" in builder.PROMPT_TEMPLATES
    
    def test_build_messages_explanation(self):
        """测试构建explanation类型的消息"""
        builder = WayFareContextBuilder()
        
        selected_text = "费曼技巧是一种学习方法"
        context_docs = [
            "费曼技巧由物理学家理查德·费曼提出",
            "这种方法强调用简单语言解释复杂概念"
        ]
        
        messages = builder.build_messages(
            selected_text=selected_text,
            annotation_type="explanation",
            context_docs=context_docs
        )
        
        # 验证消息结构
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        
        # 验证系统提示词
        system_content = messages[0]["content"]
        assert "WayFare学习助手" in system_content
        assert "费曼技巧" in system_content
        
        # 验证用户消息
        user_content = messages[1]["content"]
        assert selected_text in user_content
        assert "[片段1]" in user_content
        assert "[片段2]" in user_content
        assert context_docs[0] in user_content
        assert context_docs[1] in user_content
    
    def test_build_messages_question(self):
        """测试构建question类型的消息"""
        builder = WayFareContextBuilder()
        
        selected_text = "机器学习是人工智能的一个分支"
        context_docs = ["机器学习使用算法从数据中学习"]
        
        messages = builder.build_messages(
            selected_text=selected_text,
            annotation_type="question",
            context_docs=context_docs
        )
        
        assert len(messages) == 2
        user_content = messages[1]["content"]
        assert "启发性问题" in user_content
        assert selected_text in user_content
    
    def test_build_messages_summary(self):
        """测试构建summary类型的消息"""
        builder = WayFareContextBuilder()
        
        selected_text = "深度学习是机器学习的一个子领域"
        context_docs = []
        
        messages = builder.build_messages(
            selected_text=selected_text,
            annotation_type="summary",
            context_docs=context_docs
        )
        
        assert len(messages) == 2
        user_content = messages[1]["content"]
        assert "核心要点" in user_content
        assert selected_text in user_content
        assert "（无相关上下文）" in user_content
    
    def test_build_messages_unknown_type(self):
        """测试未知批注类型时使用默认模板"""
        builder = WayFareContextBuilder()
        
        selected_text = "测试文本"
        context_docs = ["上下文"]
        
        messages = builder.build_messages(
            selected_text=selected_text,
            annotation_type="unknown_type",
            context_docs=context_docs
        )
        
        # 应该使用explanation作为默认模板
        assert len(messages) == 2
        user_content = messages[1]["content"]
        assert "核心概念" in user_content
    
    def test_build_messages_custom_system_prompt(self):
        """测试自定义系统提示词"""
        builder = WayFareContextBuilder()
        
        custom_prompt = "你是一个专业的数学老师"
        messages = builder.build_messages(
            selected_text="测试",
            annotation_type="explanation",
            context_docs=[],
            system_prompt=custom_prompt
        )
        
        assert messages[0]["content"] == custom_prompt
    
    def test_format_context_docs_empty(self):
        """测试空上下文文档列表"""
        builder = WayFareContextBuilder()
        
        formatted = builder._format_context_docs([])
        assert formatted == "（无相关上下文）"
    
    def test_format_context_docs_single(self):
        """测试单个上下文文档"""
        builder = WayFareContextBuilder()
        
        docs = ["这是第一个文档"]
        formatted = builder._format_context_docs(docs)
        
        assert "[片段1]" in formatted
        assert docs[0] in formatted
    
    def test_format_context_docs_multiple(self):
        """测试多个上下文文档"""
        builder = WayFareContextBuilder()
        
        docs = [
            "第一个文档",
            "第二个文档",
            "第三个文档"
        ]
        formatted = builder._format_context_docs(docs)
        
        assert "[片段1]" in formatted
        assert "[片段2]" in formatted
        assert "[片段3]" in formatted
        assert all(doc in formatted for doc in docs)
    
    def test_format_context_docs_strips_whitespace(self):
        """测试格式化时去除空白"""
        builder = WayFareContextBuilder()
        
        docs = ["  文档内容  \n"]
        formatted = builder._format_context_docs(docs)
        
        assert "文档内容" in formatted
        assert "  文档内容  " not in formatted
    
    def test_build_simple_message(self):
        """测试构建简单消息"""
        builder = WayFareContextBuilder()
        
        prompt = "解释什么是机器学习"
        messages = builder.build_simple_message(prompt)
        
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == prompt
    
    def test_build_simple_message_custom_system(self):
        """测试构建简单消息时使用自定义系统提示词"""
        builder = WayFareContextBuilder()
        
        prompt = "测试"
        custom_system = "自定义系统提示词"
        messages = builder.build_simple_message(prompt, system_prompt=custom_system)
        
        assert messages[0]["content"] == custom_system
    
    def test_update_prompt_template(self):
        """测试更新Prompt模板"""
        builder = WayFareContextBuilder()
        
        new_template = "新模板：{selected_text}\n上下文：{context}"
        builder.update_prompt_template("explanation", new_template)
        
        assert builder.PROMPT_TEMPLATES["explanation"] == new_template
    
    def test_update_prompt_template_invalid_type(self):
        """测试更新不存在的批注类型"""
        builder = WayFareContextBuilder()
        
        original_templates = builder.PROMPT_TEMPLATES.copy()
        builder.update_prompt_template("invalid_type", "模板")
        
        # 模板不应该被修改
        assert builder.PROMPT_TEMPLATES == original_templates
    
    def test_update_prompt_template_missing_placeholders(self):
        """测试更新模板时缺少必要占位符"""
        builder = WayFareContextBuilder()
        
        original_template = builder.PROMPT_TEMPLATES["explanation"]
        
        # 缺少{context}占位符
        invalid_template = "只有{selected_text}"
        builder.update_prompt_template("explanation", invalid_template)
        
        # 模板不应该被修改
        assert builder.PROMPT_TEMPLATES["explanation"] == original_template
    
    def test_get_prompt_template(self):
        """测试获取Prompt模板"""
        builder = WayFareContextBuilder()
        
        template = builder.get_prompt_template("explanation")
        assert template is not None
        assert "{selected_text}" in template
        assert "{context}" in template
    
    def test_get_prompt_template_invalid_type(self):
        """测试获取不存在的模板"""
        builder = WayFareContextBuilder()
        
        template = builder.get_prompt_template("invalid_type")
        assert template is None
    
    def test_get_available_types(self):
        """测试获取可用的批注类型"""
        builder = WayFareContextBuilder()
        
        types = builder.get_available_types()
        assert len(types) == 3
        assert "explanation" in types
        assert "question" in types
        assert "summary" in types
    
    def test_factory_function(self):
        """测试工厂函数"""
        builder = create_context_builder()
        assert isinstance(builder, WayFareContextBuilder)
    
    def test_system_prompt_contains_key_elements(self):
        """测试系统提示词包含关键元素"""
        builder = WayFareContextBuilder()
        
        system_prompt = builder.SYSTEM_PROMPT
        assert "WayFare学习助手" in system_prompt
        assert "费曼技巧" in system_prompt
        assert "简洁明了" in system_prompt
    
    def test_build_system_prompt_with_type_guidance(self):
        """测试构建带类型指导的系统提示词"""
        builder = WayFareContextBuilder()
        
        explanation_prompt = builder._build_system_prompt("explanation")
        assert "费曼技巧" in explanation_prompt
        
        question_prompt = builder._build_system_prompt("question")
        assert "启发性问题" in question_prompt
        
        summary_prompt = builder._build_system_prompt("summary")
        assert "核心要点" in summary_prompt
    
    def test_messages_structure_for_llm(self):
        """测试消息结构符合LLM API要求"""
        builder = WayFareContextBuilder()
        
        messages = builder.build_messages(
            selected_text="测试文本",
            annotation_type="explanation",
            context_docs=["上下文1", "上下文2"]
        )
        
        # 验证消息格式
        for msg in messages:
            assert "role" in msg
            assert "content" in msg
            assert msg["role"] in ["system", "user", "assistant"]
            assert isinstance(msg["content"], str)
    
    def test_context_docs_ordering(self):
        """测试上下文文档的顺序保持"""
        builder = WayFareContextBuilder()
        
        docs = ["第一个", "第二个", "第三个"]
        formatted = builder._format_context_docs(docs)
        
        # 验证顺序
        pos1 = formatted.find("第一个")
        pos2 = formatted.find("第二个")
        pos3 = formatted.find("第三个")
        
        assert pos1 < pos2 < pos3
