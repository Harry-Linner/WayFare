import httpx
from loguru import logger
from config import settings


class EmbeddingProvider:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(30.0))
        self.headers = {
            "Authorization": f"Bearer {settings.LLM_API_KEY}",
            "Content-Type": "application/json"
        }
        # 推荐使用 bge-m3 等支持多语言的优质向量模型
        self.embed_model = "Pro/BAAI/bge-m3"

    async def get_embedding(self, text: str) -> list[float]:
        """将单段文本转化为 1536 维 (或 1024 维，取决于模型) 向量"""
        # 注意：如果你的模型输出是 1024 维，请在 database.py 中把 vector(1536) 改为 vector(1024)
        payload = {
            "model": self.embed_model,
            "input": text,
            "encoding_format": "float"
        }

        try:
            resp = await self.client.post(
                "https://api.siliconflow.cn/v1/embeddings",
                json=payload,
                headers=self.headers
            )
            resp.raise_for_status()
            data = resp.json()
            return data["data"][0]["embedding"]
        except Exception as e:
            logger.error(f"Embedding API failed: {e}")
            # 降级：如果失败，返回全 0 向量避免主流程崩溃 (假设维度为 1536)
            return [0.0] * 1536

    async def close(self):
        await self.client.aclose()


embed_client = EmbeddingProvider()