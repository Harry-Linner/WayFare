from typing import Any, Dict, List, Optional


def _clean_profile_text(content: str) -> str:
    return str(content or "").strip()


def _build_profile_block(title: str, content: str) -> str:
    normalized = _clean_profile_text(content)
    if not normalized:
        return ""
    return f"[{title}]\n{normalized}\n"


def build_annotate_prompt(
    anno_type: str,
    selected_text: str,
    rag_contexts: List[Dict[str, Any]],
    metadata: Optional[Dict[str, Any]] = None,
    global_profile: str = "",
    knowledge_base_profile: str = "",
    response_language: str = "简体中文",
) -> tuple[str, str]:
    """Build the system/user prompts used by the annotate pipeline."""

    metadata = metadata or {}

    context_lines: list[str] = []
    if rag_contexts:
        context_lines.append("[从当前知识库检索到的相关材料]")
        for index, ctx in enumerate(rag_contexts):
            context_lines.append(f"[{index + 1}]（第 {ctx.get('page', 0)} 页）{ctx.get('text', '')}")
        context_lines.append("")

    location_lines: list[str] = []
    document_name = str(metadata.get("documentName", "") or "").strip()
    page = metadata.get("page")
    kb_name = str(metadata.get("knowledgeBaseName", "") or "").strip()
    kb_description = str(metadata.get("knowledgeBaseDescription", "") or "").strip()
    kb_purpose = str(metadata.get("knowledgeBasePurpose", "") or "").strip()
    kb_goals = str(metadata.get("knowledgeBaseLearningGoals", "") or "").strip()

    if kb_name:
        location_lines.append(f"知识库：{kb_name}")
    if kb_description:
        location_lines.append(f"知识库说明：{kb_description}")
    if kb_purpose:
        location_lines.append(f"知识库用途：{kb_purpose}")
    if kb_goals:
        location_lines.append(f"知识库目标：{kb_goals}")
    if document_name:
        location_lines.append(f"文档：{document_name}")
    if page not in (None, "", 0):
        location_lines.append(f"页码：{page}")

    location_block = ""
    if location_lines:
        location_block = "[当前定位信息]\n" + "\n".join(location_lines) + "\n"

    global_profile_block = _build_profile_block("全局学习画像", global_profile)
    kb_profile_block = _build_profile_block("知识库画像", knowledge_base_profile)

    system_prompt = f"""你是 WayFare 的 AI 学习助手。

你的任务是帮助用户理解自己的学习材料，而不是脱离上下文泛泛而谈。请严格遵守以下规则：
1. 默认使用{response_language}回答。除非用户明确要求其它语言，否则不要整段输出英文。
2. 优先结合当前知识库、文档定位和检索材料回答；证据不足时要明确说明“不确定”。
3. 如果材料本身是英文，也要优先用中文解释，只保留必要术语或原文短语。
4. 输出必须清楚、自然、适合学习场景，不要堆砌术语。
5. 当 force_json 为真时，你只能输出合法 JSON，不要输出 Markdown 代码块，也不要输出额外解释。

返回 JSON 时必须严格符合以下结构：
{{
  "knowledge_point": "具体知识点名称",
  "frequency": "例如：2 次 / 未发现 / 0 次",
  "content": "中文解释 / 中文总结 / 中文回答"
}}"""

    task_instruction = {
        "explanation": "请用中文给出分层解释：1）它是什么意思；2）它为什么在这里重要；3）一个容易忽略的误区。",
        "summary": "请用中文提炼重点：先给 1 句核心概括，再补 2 条简短关键信息。",
        "ask": "请先用中文直接回答问题，再补 2 条简短支撑点，帮助用户继续阅读。",
        "question": "请围绕选中文本生成 1 个适合继续思考的苏格拉底式问题，使用中文。",
    }.get(anno_type, "请用中文清晰解释用户当前关注的内容。")

    user_prompt = "\n".join(
        [
            *context_lines,
            location_block.strip(),
            global_profile_block.strip(),
            kb_profile_block.strip(),
            "[用户当前关注的内容]",
            str(selected_text or "").strip(),
            "",
            "[任务要求]",
            task_instruction,
        ]
    ).strip()

    return system_prompt, user_prompt
