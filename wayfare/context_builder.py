"""
Context Builder集成模块

复用nanobot的ContextBuilder系统，为批注生成构建LLM上下文。
实现系统提示词配置和上下文文档格式化。
"""

from typing import List, Dict, Any, Optional
from loguru import logger


class WayFareContextBuilder:
    """
    WayFare Context Builder封装类
    
    为批注生成场景构建LLM上下文，包括：
    - 系统提示词配置（学习助手角色）
    - RAG上下文文档格式化
    - 用户选中文本的格式化
    - 批注类型特定的Prompt模板
    """
    
    # 系统提示词
    SYSTEM_PROMPT = """你是WayFare学习助手，帮助学生理解和掌握知识。

你的职责是：
1. 使用费曼技巧，用简单易懂的语言解释复杂概念
2. 通过启发性问题引导学生深入思考
3. 提炼核心要点，帮助学生建立知识框架

你的回答应该：
- 简洁明了，不超过200字
- 贴近学生的认知水平
- 结合具体例子和类比
- 鼓励主动思考和探索"""
    
    # 批注类型特定的Prompt模板
    PROMPT_TEMPLATES = {
        "explanation": """用户选中的文本：
{selected_text}

相关上下文：
{context}

请用简单易懂的语言解释这段内容，包括：
1. 核心概念是什么
2. 用类比或例子说明
3. 为什么这个概念重要

保持简洁，不超过200字。""",
        
        "question": """用户选中的文本：
{selected_text}

相关上下文：
{context}

请提出2-3个启发性问题，帮助学生：
1. 理解概念的本质
2. 联系已有知识
3. 思考应用场景

每个问题简短有力。""",
        
        "summary": """用户选中的文本：
{selected_text}

相关上下文：
{context}

请总结这段内容的核心要点：
1. 主要观点（1-2句话）
2. 关键细节（2-3个要点）
3. 与上下文的关系

保持简洁，不超过150字。"""
    }
    
    def __init__(self):
        """初始化Context Builder"""
        logger.info("Initialized WayFare Context Builder")
    
    def build_messages(
        self,
        selected_text: str,
        annotation_type: str,
        context_docs: List[str],
        system_prompt: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        构建LLM消息列表
        
        Args:
            selected_text: 用户选中的文本
            annotation_type: 批注类型（explanation/question/summary）
            context_docs: RAG检索到的上下文文档列表
            system_prompt: 可选的自定义系统提示词
            
        Returns:
            消息列表，格式为[{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
        """
        # 1. 构建系统提示词
        sys_prompt = system_prompt or self._build_system_prompt(annotation_type)
        
        # 2. 格式化上下文文档
        formatted_context = self._format_context_docs(context_docs)
        
        # 3. 获取Prompt模板
        prompt_template = self.PROMPT_TEMPLATES.get(
            annotation_type,
            self.PROMPT_TEMPLATES["explanation"]
        )
        
        # 4. 填充模板
        user_message = prompt_template.format(
            selected_text=selected_text,
            context=formatted_context
        )
        
        # 5. 构建消息列表
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_message}
        ]
        
        logger.debug(
            f"Built messages for annotation type: {annotation_type}, "
            f"context docs: {len(context_docs)}"
        )
        
        return messages
    
    def _build_system_prompt(self, annotation_type: str) -> str:
        """
        构建系统提示词
        
        Args:
            annotation_type: 批注类型
            
        Returns:
            系统提示词
        """
        base_prompt = self.SYSTEM_PROMPT
        
        # 根据批注类型添加特定指导
        type_guidance = {
            "explanation": "\n\n当前任务：使用费曼技巧，用简单语言解释复杂概念。",
            "question": "\n\n当前任务：通过启发性问题引导学生深入思考。",
            "summary": "\n\n当前任务：提炼核心要点，帮助学生建立知识框架。"
        }
        
        guidance = type_guidance.get(annotation_type, "")
        return base_prompt + guidance
    
    def _format_context_docs(self, context_docs: List[str]) -> str:
        """
        格式化上下文文档
        
        Args:
            context_docs: 上下文文档列表
            
        Returns:
            格式化后的上下文字符串
        """
        if not context_docs:
            return "（无相关上下文）"
        
        # 为每个文档添加编号和分隔符
        formatted_docs = []
        for i, doc in enumerate(context_docs, 1):
            formatted_docs.append(f"[片段{i}]\n{doc.strip()}")
        
        return "\n\n".join(formatted_docs)
    
    def build_simple_message(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        构建简单的单轮对话消息
        
        Args:
            prompt: 用户提示词
            system_prompt: 可选的系统提示词
            
        Returns:
            消息列表
        """
        sys_prompt = system_prompt or self.SYSTEM_PROMPT
        
        return [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": prompt}
        ]
    
    def update_prompt_template(
        self,
        annotation_type: str,
        template: str
    ):
        """
        更新Prompt模板
        
        Args:
            annotation_type: 批注类型
            template: 新的模板字符串，应包含{selected_text}和{context}占位符
        """
        if annotation_type not in self.PROMPT_TEMPLATES:
            logger.warning(
                f"Unknown annotation type: {annotation_type}. "
                f"Valid types: {list(self.PROMPT_TEMPLATES.keys())}"
            )
            return
        
        # 验证模板包含必要的占位符
        if "{selected_text}" not in template or "{context}" not in template:
            logger.error(
                "Template must contain {selected_text} and {context} placeholders"
            )
            return
        
        self.PROMPT_TEMPLATES[annotation_type] = template
        logger.info(f"Updated prompt template for {annotation_type}")
    
    def get_prompt_template(self, annotation_type: str) -> Optional[str]:
        """
        获取Prompt模板
        
        Args:
            annotation_type: 批注类型
            
        Returns:
            模板字符串，如果类型不存在则返回None
        """
        return self.PROMPT_TEMPLATES.get(annotation_type)
    
    def get_available_types(self) -> List[str]:
        """
        获取所有可用的批注类型
        
        Returns:
            批注类型列表
        """
        return list(self.PROMPT_TEMPLATES.keys())


def create_context_builder() -> WayFareContextBuilder:
    """
    工厂函数：创建Context Builder实例
    
    Returns:
        WayFareContextBuilder实例
    """
    return WayFareContextBuilder()
