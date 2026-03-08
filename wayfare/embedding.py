"""
Embedding Service模块

使用ONNX Runtime和transformers实现文本向量化服务。
支持批量和单文本向量生成，使用BAAI/bge-small-zh-v1.5模型。
"""

import numpy as np
from typing import List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    文本向量化服务
    
    使用BAAI/bge-small-zh-v1.5 ONNX模型生成512维文本向量。
    支持批量处理和L2归一化。
    
    Requirements:
    - 3.1: Use BAAI/bge-small-zh-v1.5 ONNX model for text vectors
    - 3.2: Generate 512-dimensional vectors for each document segment
    """
    
    def __init__(self, model_path: str):
        """
        初始化Embedding服务
        
        Args:
            model_path: ONNX模型文件路径
            
        Raises:
            FileNotFoundError: 如果模型文件不存在
            ImportError: 如果缺少必要的依赖包
        """
        self.model_path = Path(model_path)
        self.session: Optional[object] = None
        self.tokenizer: Optional[object] = None
        
        # 模型配置
        self.max_length = 512
        self.vector_dim = 512
        
        # 延迟加载模型（在第一次使用时加载）
        self._initialized = False
    
    def _initialize(self):
        """
        延迟初始化模型和tokenizer
        
        Raises:
            FileNotFoundError: 如果模型文件不存在
            ImportError: 如果缺少必要的依赖包
        """
        if self._initialized:
            return
        
        try:
            import onnxruntime as ort
            from transformers import AutoTokenizer
        except ImportError as e:
            raise ImportError(
                "Missing required dependencies. Please install: "
                "pip install onnxruntime transformers"
            ) from e
        
        # 检查模型文件是否存在
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"ONNX model file not found: {self.model_path}\n"
                f"Please download the model from: "
                f"https://huggingface.co/BAAI/bge-small-zh-v1.5"
            )
        
        logger.info(f"Loading ONNX model from {self.model_path}")
        
        # 加载ONNX模型
        self.session = ort.InferenceSession(
            str(self.model_path),
            providers=['CPUExecutionProvider']  # MVP使用CPU推理
        )
        
        logger.info("Loading tokenizer for BAAI/bge-small-zh-v1.5")
        
        # 加载tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            "BAAI/bge-small-zh-v1.5"
        )
        
        self._initialized = True
        logger.info("Embedding service initialized successfully")
    
    async def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        批量生成文本向量
        
        Args:
            texts: 文本列表
            
        Returns:
            shape为(len(texts), 512)的向量数组，已进行L2归一化
            
        Raises:
            ValueError: 如果texts为空
            RuntimeError: 如果模型推理失败
            
        Example:
            >>> service = EmbeddingService("model.onnx")
            >>> vectors = await service.embed_texts(["文本1", "文本2"])
            >>> vectors.shape
            (2, 512)
        """
        if not texts:
            raise ValueError("texts cannot be empty")
        
        # 确保模型已初始化
        self._initialize()
        
        logger.debug(f"Embedding {len(texts)} texts")
        
        try:
            # Tokenize
            encoded = self.tokenizer(
                texts,
                padding=True,
                truncation=True,
                max_length=self.max_length,
                return_tensors="np"
            )
            
            # ONNX推理
            input_ids = encoded["input_ids"]
            attention_mask = encoded["attention_mask"]
            
            outputs = self.session.run(
                None,
                {
                    "input_ids": input_ids,
                    "attention_mask": attention_mask
                }
            )
            
            # 提取[CLS] token的embedding
            embeddings = outputs[0][:, 0, :]  # shape: (batch_size, 512)
            
            # L2归一化
            embeddings = self._normalize_l2(embeddings)
            
            logger.debug(f"Generated embeddings with shape {embeddings.shape}")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise RuntimeError(f"Embedding generation failed: {e}") from e
    
    async def embed_single(self, text: str) -> np.ndarray:
        """
        生成单个文本的向量
        
        Args:
            text: 单个文本
            
        Returns:
            shape为(512,)的向量，已进行L2归一化
            
        Raises:
            ValueError: 如果text为空
            RuntimeError: 如果模型推理失败
            
        Example:
            >>> service = EmbeddingService("model.onnx")
            >>> vector = await service.embed_single("示例文本")
            >>> vector.shape
            (512,)
        """
        if not text or not text.strip():
            raise ValueError("text cannot be empty")
        
        embeddings = await self.embed_texts([text])
        return embeddings[0]
    
    def _normalize_l2(self, embeddings: np.ndarray) -> np.ndarray:
        """
        L2归一化向量
        
        Args:
            embeddings: 输入向量数组，shape为(batch_size, vector_dim)
            
        Returns:
            归一化后的向量数组，shape不变
        """
        # 计算L2范数
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        
        # 避免除以零
        norms = np.maximum(norms, 1e-12)
        
        # 归一化
        normalized = embeddings / norms
        
        return normalized
    
    @property
    def is_initialized(self) -> bool:
        """
        检查服务是否已初始化
        
        Returns:
            True如果已初始化，否则False
        """
        return self._initialized
    
    def get_vector_dimension(self) -> int:
        """
        获取向量维度
        
        Returns:
            向量维度（512）
        """
        return self.vector_dim
