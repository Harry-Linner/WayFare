import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_DSN: str = os.getenv("DB_DSN", "postgresql://your_db_user:your_db_pwd@localhost:5432/wayfare_db")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "your_llm_api_key_here")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.siliconflow.cn/v1/chat/completions")
    LLM_MODEL_NAME: str = os.getenv("LLM_MODEL_NAME", "Pro/deepseek-ai/DeepSeek-V3")
    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "4"))
    
    # 动态配置阈值，默认 60 秒
    INTERVENTION_THRESHOLD: int = 60
    
    class Config:
        env_file = ".env"

settings = Settings()
