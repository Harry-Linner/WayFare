"""
Embedding Service测试

测试文本向量化服务的功能，包括批量处理、单文本处理和L2归一化。
"""

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from wayfare.embedding import EmbeddingService


class TestEmbeddingService:
    """测试EmbeddingService类"""
    
    @pytest.fixture
    def mock_model_path(self, tmp_path):
        """创建临时模型文件路径"""
        model_file = tmp_path / "model.onnx"
        model_file.touch()  # 创建空文件
        return str(model_file)
    
    @pytest.fixture
    def mock_onnx_session(self):
        """模拟ONNX Runtime session"""
        session = Mock()
        # 模拟返回512维向量
        session.run.return_value = [
            np.random.randn(2, 1, 512)  # (batch_size, seq_len, hidden_size)
        ]
        return session
    
    @pytest.fixture
    def mock_tokenizer(self):
        """模拟transformers tokenizer"""
        tokenizer = Mock()
        tokenizer.return_value = {
            "input_ids": np.array([[1, 2, 3], [4, 5, 6]]),
            "attention_mask": np.array([[1, 1, 1], [1, 1, 1]])
        }
        return tokenizer
    
    def test_init(self, mock_model_path):
        """测试初始化"""
        service = EmbeddingService(mock_model_path)
        
        assert service.model_path == Path(mock_model_path)
        assert service.max_length == 512
        assert service.vector_dim == 512
        assert not service.is_initialized
    
    def test_init_with_nonexistent_model(self):
        """测试使用不存在的模型路径初始化"""
        service = EmbeddingService("/nonexistent/model.onnx")
        
        # 初始化不应该失败，因为是延迟加载
        assert not service.is_initialized
        
        # 但是在实际使用时应该抛出异常
        with pytest.raises(FileNotFoundError):
            service._initialize()
    
    @patch('onnxruntime.InferenceSession')
    @patch('transformers.AutoTokenizer.from_pretrained')
    def test_initialize(self, mock_from_pretrained, mock_inference_session, mock_model_path):
        """测试延迟初始化"""
        mock_session = Mock()
        mock_inference_session.return_value = mock_session
        
        mock_tokenizer = Mock()
        mock_from_pretrained.return_value = mock_tokenizer
        
        service = EmbeddingService(mock_model_path)
        service._initialize()
        
        assert service.is_initialized
        assert service.session == mock_session
        assert service.tokenizer == mock_tokenizer
        
        # 验证调用
        mock_inference_session.assert_called_once()
        mock_from_pretrained.assert_called_once_with(
            "BAAI/bge-small-zh-v1.5"
        )
    
    @patch('onnxruntime.InferenceSession')
    @patch('transformers.AutoTokenizer.from_pretrained')
    async def test_embed_texts(self, mock_from_pretrained, mock_inference_session, mock_model_path):
        """测试批量文本向量化"""
        # 设置mock
        mock_session = Mock()
        # 返回未归一化的向量
        mock_session.run.return_value = [
            np.array([[[1.0] * 512], [[2.0] * 512]])  # (2, 1, 512)
        ]
        mock_inference_session.return_value = mock_session
        
        mock_tokenizer = Mock()
        mock_tokenizer.return_value = {
            "input_ids": np.array([[1, 2, 3], [4, 5, 6]]),
            "attention_mask": np.array([[1, 1, 1], [1, 1, 1]])
        }
        mock_from_pretrained.return_value = mock_tokenizer
        
        # 测试
        service = EmbeddingService(mock_model_path)
        texts = ["文本1", "文本2"]
        embeddings = await service.embed_texts(texts)
        
        # 验证
        assert embeddings.shape == (2, 512)
        assert service.is_initialized
        
        # 验证tokenizer调用
        mock_tokenizer.assert_called_once_with(
            texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="np"
        )
        
        # 验证ONNX session调用
        mock_session.run.assert_called_once()
    
    @patch('onnxruntime.InferenceSession')
    @patch('transformers.AutoTokenizer.from_pretrained')
    async def test_embed_single(self, mock_from_pretrained, mock_inference_session, mock_model_path):
        """测试单文本向量化"""
        # 设置mock
        mock_session = Mock()
        mock_session.run.return_value = [
            np.array([[[1.0] * 512]])  # (1, 1, 512)
        ]
        mock_inference_session.return_value = mock_session
        
        mock_tokenizer = Mock()
        mock_tokenizer.return_value = {
            "input_ids": np.array([[1, 2, 3]]),
            "attention_mask": np.array([[1, 1, 1]])
        }
        mock_from_pretrained.return_value = mock_tokenizer
        
        # 测试
        service = EmbeddingService(mock_model_path)
        text = "示例文本"
        embedding = await service.embed_single(text)
        
        # 验证
        assert embedding.shape == (512,)
        assert service.is_initialized
    
    async def test_embed_texts_empty_list(self, mock_model_path):
        """测试空文本列表"""
        service = EmbeddingService(mock_model_path)
        
        with pytest.raises(ValueError, match="texts cannot be empty"):
            await service.embed_texts([])
    
    async def test_embed_single_empty_text(self, mock_model_path):
        """测试空文本"""
        service = EmbeddingService(mock_model_path)
        
        with pytest.raises(ValueError, match="text cannot be empty"):
            await service.embed_single("")
        
        with pytest.raises(ValueError, match="text cannot be empty"):
            await service.embed_single("   ")
    
    def test_normalize_l2(self, mock_model_path):
        """测试L2归一化"""
        service = EmbeddingService(mock_model_path)
        
        # 创建测试向量
        vectors = np.array([
            [3.0, 4.0],  # 长度为5
            [1.0, 0.0],  # 长度为1
            [0.0, 0.0]   # 零向量
        ])
        
        normalized = service._normalize_l2(vectors)
        
        # 验证形状
        assert normalized.shape == vectors.shape
        
        # 验证归一化（前两个向量的L2范数应该为1）
        norm1 = np.linalg.norm(normalized[0])
        norm2 = np.linalg.norm(normalized[1])
        
        assert np.isclose(norm1, 1.0)
        assert np.isclose(norm2, 1.0)
        
        # 验证零向量不会导致除以零错误
        assert not np.any(np.isnan(normalized))
        assert not np.any(np.isinf(normalized))
    
    def test_get_vector_dimension(self, mock_model_path):
        """测试获取向量维度"""
        service = EmbeddingService(mock_model_path)
        
        assert service.get_vector_dimension() == 512
    
    @patch('onnxruntime.InferenceSession')
    @patch('transformers.AutoTokenizer.from_pretrained')
    async def test_l2_normalization_in_embed_texts(
        self, mock_from_pretrained, mock_inference_session, mock_model_path
    ):
        """测试embed_texts中的L2归一化"""
        # 设置mock返回已知的向量
        mock_session = Mock()
        mock_session.run.return_value = [
            np.array([[[3.0, 4.0] + [0.0] * 510]])  # (1, 1, 512)
        ]
        mock_inference_session.return_value = mock_session
        
        mock_tokenizer = Mock()
        mock_tokenizer.return_value = {
            "input_ids": np.array([[1, 2, 3]]),
            "attention_mask": np.array([[1, 1, 1]])
        }
        mock_from_pretrained.return_value = mock_tokenizer
        
        # 测试
        service = EmbeddingService(mock_model_path)
        embeddings = await service.embed_texts(["test"])
        
        # 验证L2范数为1
        norm = np.linalg.norm(embeddings[0])
        assert np.isclose(norm, 1.0)
        
        # 验证前两个元素的比例保持不变（3:4）
        assert np.isclose(embeddings[0][0] / embeddings[0][1], 3.0 / 4.0)
    
    @patch('onnxruntime.InferenceSession')
    @patch('transformers.AutoTokenizer.from_pretrained')
    async def test_multiple_initializations(
        self, mock_from_pretrained, mock_inference_session, mock_model_path
    ):
        """测试多次初始化不会重复加载模型"""
        mock_session = Mock()
        mock_session.run.return_value = [
            np.array([[[1.0] * 512]])
        ]
        mock_inference_session.return_value = mock_session
        
        mock_tokenizer = Mock()
        mock_tokenizer.return_value = {
            "input_ids": np.array([[1, 2, 3]]),
            "attention_mask": np.array([[1, 1, 1]])
        }
        mock_from_pretrained.return_value = mock_tokenizer
        
        service = EmbeddingService(mock_model_path)
        
        # 多次调用embed_texts
        await service.embed_texts(["text1"])
        await service.embed_texts(["text2"])
        
        # 验证只初始化了一次
        assert mock_inference_session.call_count == 1
        assert mock_from_pretrained.call_count == 1
    
    @patch('onnxruntime.InferenceSession')
    @patch('transformers.AutoTokenizer.from_pretrained')
    async def test_tokenizer_parameters(
        self, mock_from_pretrained, mock_inference_session, mock_model_path
    ):
        """测试tokenizer参数正确传递"""
        mock_session = Mock()
        mock_session.run.return_value = [
            np.array([[[1.0] * 512], [[2.0] * 512]])
        ]
        mock_inference_session.return_value = mock_session
        
        mock_tokenizer = Mock()
        mock_tokenizer.return_value = {
            "input_ids": np.array([[1, 2], [3, 4]]),
            "attention_mask": np.array([[1, 1], [1, 1]])
        }
        mock_from_pretrained.return_value = mock_tokenizer
        
        service = EmbeddingService(mock_model_path)
        texts = ["长文本" * 100, "短文本"]
        
        await service.embed_texts(texts)
        
        # 验证tokenizer调用参数
        call_args = mock_tokenizer.call_args
        assert call_args[0][0] == texts
        assert call_args[1]["padding"] is True
        assert call_args[1]["truncation"] is True
        assert call_args[1]["max_length"] == 512
        assert call_args[1]["return_tensors"] == "np"
    
    @patch('onnxruntime.InferenceSession')
    @patch('transformers.AutoTokenizer.from_pretrained')
    async def test_onnx_session_input_format(
        self, mock_from_pretrained, mock_inference_session, mock_model_path
    ):
        """测试ONNX session输入格式正确"""
        mock_session = Mock()
        mock_session.run.return_value = [
            np.array([[[1.0] * 512]])
        ]
        mock_inference_session.return_value = mock_session
        
        input_ids = np.array([[1, 2, 3]])
        attention_mask = np.array([[1, 1, 1]])
        
        mock_tokenizer = Mock()
        mock_tokenizer.return_value = {
            "input_ids": input_ids,
            "attention_mask": attention_mask
        }
        mock_from_pretrained.return_value = mock_tokenizer
        
        service = EmbeddingService(mock_model_path)
        await service.embed_texts(["test"])
        
        # 验证ONNX session调用参数
        call_args = mock_session.run.call_args
        assert call_args[0][0] is None  # output_names
        assert "input_ids" in call_args[0][1]
        assert "attention_mask" in call_args[0][1]
        assert np.array_equal(call_args[0][1]["input_ids"], input_ids)
        assert np.array_equal(call_args[0][1]["attention_mask"], attention_mask)


class TestEmbeddingServiceIntegration:
    """集成测试（需要实际的模型文件）"""
    
    @pytest.mark.skip(reason="Requires actual ONNX model file")
    async def test_real_model_inference(self):
        """测试真实模型推理（需要下载模型）"""
        model_path = "./models/bge-small-zh-v1.5.onnx"
        
        if not Path(model_path).exists():
            pytest.skip("Model file not found")
        
        service = EmbeddingService(model_path)
        
        # 测试中文文本
        texts = [
            "这是一个测试文本",
            "人工智能正在改变世界",
            "机器学习是人工智能的一个分支"
        ]
        
        embeddings = await service.embed_texts(texts)
        
        # 验证输出
        assert embeddings.shape == (3, 512)
        
        # 验证L2归一化
        for i in range(3):
            norm = np.linalg.norm(embeddings[i])
            assert np.isclose(norm, 1.0, atol=1e-6)
        
        # 验证语义相似性（后两个文本应该更相似）
        sim_01 = np.dot(embeddings[0], embeddings[1])
        sim_12 = np.dot(embeddings[1], embeddings[2])
        
        # 后两个文本都关于AI，应该更相似
        assert sim_12 > sim_01
