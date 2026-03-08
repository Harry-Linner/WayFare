"""
Embedding Service使用示例

演示如何使用EmbeddingService生成文本向量。
"""

import asyncio
import numpy as np
from wayfare.embedding import EmbeddingService


async def main():
    """主函数"""
    
    # 1. 初始化Embedding Service
    print("初始化Embedding Service...")
    model_path = "./models/bge-small-zh-v1.5.onnx"
    
    try:
        service = EmbeddingService(model_path)
        print(f"✓ 服务创建成功")
        print(f"  向量维度: {service.get_vector_dimension()}")
        print()
    except FileNotFoundError as e:
        print(f"✗ 模型文件未找到: {e}")
        print("\n请从以下地址下载模型:")
        print("https://huggingface.co/BAAI/bge-small-zh-v1.5")
        return
    
    # 2. 单文本向量化
    print("=" * 60)
    print("示例1: 单文本向量化")
    print("=" * 60)
    
    text = "人工智能正在改变世界"
    print(f"输入文本: {text}")
    
    try:
        vector = await service.embed_single(text)
        print(f"✓ 生成向量成功")
        print(f"  向量形状: {vector.shape}")
        print(f"  L2范数: {np.linalg.norm(vector):.6f}")
        print(f"  前5个元素: {vector[:5]}")
        print()
    except Exception as e:
        print(f"✗ 向量化失败: {e}")
        return
    
    # 3. 批量文本向量化
    print("=" * 60)
    print("示例2: 批量文本向量化")
    print("=" * 60)
    
    texts = [
        "机器学习是人工智能的一个分支",
        "深度学习使用神经网络进行学习",
        "自然语言处理研究计算机与人类语言的交互",
        "计算机视觉让机器能够理解图像",
        "强化学习通过试错来学习最优策略"
    ]
    
    print(f"输入文本数量: {len(texts)}")
    for i, t in enumerate(texts, 1):
        print(f"  {i}. {t}")
    print()
    
    try:
        vectors = await service.embed_texts(texts)
        print(f"✓ 批量向量化成功")
        print(f"  向量矩阵形状: {vectors.shape}")
        print(f"  每个向量的L2范数:")
        for i, vec in enumerate(vectors, 1):
            norm = np.linalg.norm(vec)
            print(f"    文本{i}: {norm:.6f}")
        print()
    except Exception as e:
        print(f"✗ 批量向量化失败: {e}")
        return
    
    # 4. 计算语义相似度
    print("=" * 60)
    print("示例3: 计算语义相似度")
    print("=" * 60)
    
    # 计算余弦相似度（向量已归一化，点积即为余弦相似度）
    print("文本间的语义相似度矩阵:")
    print()
    
    # 打印表头
    print("     ", end="")
    for i in range(len(texts)):
        print(f"  文本{i+1}", end="")
    print()
    
    # 打印相似度矩阵
    for i in range(len(texts)):
        print(f"文本{i+1}", end="")
        for j in range(len(texts)):
            similarity = np.dot(vectors[i], vectors[j])
            print(f"  {similarity:.3f}", end="")
        print()
    print()
    
    # 5. 找出最相似的文本对
    print("=" * 60)
    print("示例4: 找出最相似的文本对")
    print("=" * 60)
    
    max_sim = -1
    max_pair = (0, 0)
    
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            similarity = np.dot(vectors[i], vectors[j])
            if similarity > max_sim:
                max_sim = similarity
                max_pair = (i, j)
    
    print(f"最相似的文本对:")
    print(f"  文本{max_pair[0]+1}: {texts[max_pair[0]]}")
    print(f"  文本{max_pair[1]+1}: {texts[max_pair[1]]}")
    print(f"  相似度: {max_sim:.4f}")
    print()
    
    # 6. 查询检索示例
    print("=" * 60)
    print("示例5: 查询检索")
    print("=" * 60)
    
    query = "什么是神经网络？"
    print(f"查询: {query}")
    print()
    
    try:
        query_vector = await service.embed_single(query)
        
        # 计算与所有文本的相似度
        similarities = np.dot(vectors, query_vector)
        
        # 排序并获取top-3
        top_k = 3
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        print(f"Top-{top_k} 最相关的文本:")
        for rank, idx in enumerate(top_indices, 1):
            print(f"  {rank}. [相似度: {similarities[idx]:.4f}] {texts[idx]}")
        print()
    except Exception as e:
        print(f"✗ 查询失败: {e}")
        return
    
    # 7. 性能测试
    print("=" * 60)
    print("示例6: 性能测试")
    print("=" * 60)
    
    import time
    
    # 测试单文本性能
    test_text = "这是一个性能测试文本"
    iterations = 10
    
    start_time = time.time()
    for _ in range(iterations):
        await service.embed_single(test_text)
    elapsed = time.time() - start_time
    
    print(f"单文本向量化性能:")
    print(f"  迭代次数: {iterations}")
    print(f"  总耗时: {elapsed:.3f}秒")
    print(f"  平均耗时: {elapsed/iterations*1000:.2f}毫秒/次")
    print()
    
    # 测试批量性能
    batch_sizes = [1, 5, 10, 20]
    print("批量向量化性能:")
    
    for batch_size in batch_sizes:
        test_texts = [f"测试文本{i}" for i in range(batch_size)]
        
        start_time = time.time()
        await service.embed_texts(test_texts)
        elapsed = time.time() - start_time
        
        print(f"  批量大小={batch_size:2d}: {elapsed*1000:.2f}毫秒 "
              f"({elapsed/batch_size*1000:.2f}毫秒/文本)")
    
    print()
    print("=" * 60)
    print("所有示例完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
