import httpx
import json
from loguru import logger
from typing import Dict, Any
from config import settings

class LLMProvider:
    def __init__(self):
        # 初始化 HTTPX 异步客户端
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(120.0), # 推理和深思模型时间较长，增加超时
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=50)
        )
        self.headers = {
            "Authorization": f"Bearer {settings.LLM_API_KEY}",
            "Content-Type": "application/json"
        }

    async def close(self):
        await self.client.aclose()

    async def call_llm(self, prompt: str, system_prompt: str, history: list = None, force_json: bool = True) -> Dict[
        str, Any]:
        """
        异步调用 LLM，强制要求返回严格 JSON 对象，支持多轮历史对话上下文。
        """
        # 1. 组装基础的 system 提示词
        messages = [{"role": "system", "content": system_prompt}]

        # 2. 注入前端传来的多轮历史聊天记录 (如果有的话)
        if history:
            messages.extend(history)

        # 3. 拼接当前最新的提问 (包含 RAG 检索内容)
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": settings.LLM_MODEL_NAME,
            "messages": messages,
            "temperature": 0.3  # 降低温度保证字段结构不变
        }

        # 排除不支持 json_object 的 R1 推理模型
        if force_json and "reasoner" not in settings.LLM_MODEL_NAME.lower():
            payload["response_format"] = {"type": "json_object"}

        try:
            resp = await self.client.post(
                settings.LLM_BASE_URL,
                json=payload,
                headers=self.headers
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]

            if force_json:
                # 处理容错：避免模型输出携带 Markdown Code Block
                content = content.replace("```json", "").replace("```", "").strip()
                return json.loads(content)

            return {"content": content}

        except httpx.HTTPStatusError as e:
            logger.error(f"LLM API HTTP Error: {e.response.text}")
            raise RuntimeError(f"LLM API request failed: {e.response.status_code}")
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from LLM: {content}")
            raise ValueError("LLM returned malformed JSON instead of structured data.")
        except Exception as e:
            logger.exception("Unexpected error during LLM call")
            raise

llm_client = LLMProvider()
