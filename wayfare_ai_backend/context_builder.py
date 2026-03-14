from typing import List, Dict

def build_annotate_prompt(anno_type: str, selected_text: str, rag_contexts: List[Dict]) -> tuple[str, str]:
    """
    构建强制要求输出 JSON 的系统提示词和用户提示词
    返回: (system_prompt, user_prompt)
    """
    # 拼装历史检索上下文
    context_str = ""
    if rag_contexts:
        context_str = "【历史卷宗与讲义参考】\n"
        for i, ctx in enumerate(rag_contexts):
            context_str += f"[{i+1}] (第{ctx.get('page', 0)}页): {ctx.get('text', '')}\n"

    system_prompt = """你现在是 WayFare，一位顶尖的主动式个性化AI学习管家。
你的核心任务是辅导学生备考。

【工作准则】
1. 绝对客观：提取的考点必须具体、细化。
2. 严谨求证：考频（frequency）只能基于我提供给你的《历史卷宗》进行统计。如果在上下文中没找到，频次就是 0。
3. 降维打击：在编写讲解时，必须使用直觉化的类比（费曼技巧），通俗易懂。
4. 格式铁律：必须且只能输出合法的 JSON 格式，绝对不能包含 Markdown 标记（如 ```json）或任何其他废话。

【强制输出 JSON 结构】
{
  "knowledge_point": "具体的知识点名称",
  "frequency": "历史考频统计描述，如 '考过2次' 或 '未考过'",
  "content": "你的降维拆解讲解或总结内容"
}"""

    task_instruction = {
        "explanation": "请针对【用户选中内容】进行费曼降维讲解。",
        "question": "请针对【用户选中内容】提出一个苏格拉底式的启发反问。",
        "summary": "请对【用户选中内容】进行极简总结提取。"
    }.get(anno_type, "请进行详细解释。")

    user_prompt = f"""
{context_str}

【用户选中内容】
{selected_text}

【任务指令】
{task_instruction}
"""
    return system_prompt, user_prompt