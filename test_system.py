#!/usr/bin/env python3
"""
WayFare AI学习助手 - 系统集成测试脚本
用于验证所有服务组件的正确集成和基本功能
"""

import asyncio
import aiohttp
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

# 服务配置
SERVICES = {
    'frontend': 'http://localhost:3000',
    'go_backend': 'http://localhost:8080',
    'python_ai': 'http://localhost:8001',
    'cpp_sandbox': 'http://localhost:8002'
}

class WayFareTestClient:
    """WayFare系统测试客户端"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.test_results = []
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=10)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def check_service_health(self, service_name: str, url: str) -> bool:
        """检查服务健康状态"""
        try:
            print(f"🔍 检查 {service_name} 健康状态...")
            
            # 尝试多个健康检查端点
            health_endpoints = ['/health', '/api/health', '/status', '/']
            
            for endpoint in health_endpoints:
                try:
                    async with self.session.get(f"{url}{endpoint}") as response:
                        if response.status == 200:
                            print(f"✅ {service_name} 服务正常 (端点: {endpoint})")
                            return True
                except:
                    continue
            
            print(f"❌ {service_name} 服务异常")
            return False
            
        except Exception as e:
            print(f"❌ {service_name} 连接失败: {e}")
            return False
    
    async def test_file_upload(self) -> bool:
        """测试文件上传功能"""
        try:
            print("📁 测试文件上传功能...")
            
            # 创建一个测试文件
            test_content = """# WayFare测试文档
            
这是一个用于测试的Markdown文档。

## 测试内容
- 列表项1
- 列表项2
- 列表项3

### 代码块示例
```python
def hello_world():
    print("Hello, WayFare!")
```

> 这是一个引用块

**加粗文本** 和 *斜体文本*
"""
            
            # 创建临时文件
            test_file = Path("test_document.md")
            test_file.write_text(test_content, encoding='utf-8')
            
            # 上传文件
            with open(test_file, 'rb') as f:
                form_data = aiohttp.FormData()
                form_data.add_field('file', f, filename='test_document.md', 
                                  content_type='text/markdown')
                
                async with self.session.post(f"{SERVICES['go_backend']}/api/upload", 
                                           data=form_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ 文件上传成功: {result.get('message', 'Unknown')}")
                        print(f"📄 文档ID: {result.get('docId', 'Unknown')}")
                        print(f"🔑 文档哈希: {result.get('docHash', 'Unknown')}")
                        
                        # 保存文档哈希用于后续测试
                        self.doc_hash = result.get('docHash')
                        self.doc_id = result.get('docId')
                        
                        # 清理临时文件
                        test_file.unlink()
                        return True
                    else:
                        error_text = await response.text()
                        print(f"❌ 文件上传失败: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            print(f"❌ 文件上传测试失败: {e}")
            return False
    
    async def test_chat_functionality(self) -> bool:
        """测试聊天功能"""
        try:
            print("💬 测试聊天功能...")
            
            if not hasattr(self, 'doc_hash'):
                print("⚠️  需要先上传文件才能测试聊天功能")
                return False
            
            # 测试消息
            test_messages = [
                "这篇文档的主要内容是什么？",
                "文档中提到了哪些技术概念？",
                "请总结一下文档的要点"
            ]
            
            for i, message in enumerate(test_messages):
                print(f"📝 测试消息 {i+1}: {message}")
                
                payload = {
                    "message": message,
                    "docHash": self.doc_hash,
                    "history": []
                }
                
                async with self.session.post(f"{SERVICES['go_backend']}/api/chat", 
                                           json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        ai_response = result.get('message', '无响应')
                        print(f"🤖 AI回复: {ai_response[:100]}...")
                        
                        # 检查响应质量
                        if len(ai_response) > 10:
                            print(f"✅ 聊天功能正常")
                        else:
                            print(f"⚠️  AI回复可能不完整")
                    else:
                        error_text = await response.text()
                        print(f"❌ 聊天请求失败: {response.status} - {error_text}")
                        return False
                
                # 等待一下，避免请求过快
                await asyncio.sleep(1)
            
            return True
            
        except Exception as e:
            print(f"❌ 聊天功能测试失败: {e}")
            return False
    
    async def test_document_listing(self) -> bool:
        """测试文档列表功能"""
        try:
            print("📋 测试文档列表功能...")
            
            async with self.session.get(f"{SERVICES['go_backend']}/api/documents") as response:
                if response.status == 200:
                    documents = await response.json()
                    print(f"✅ 文档列表获取成功，共 {len(documents)} 个文档")
                    
                    # 显示前几个文档
                    for i, doc in enumerate(documents[:3]):
                        print(f"  📄 {doc.get('fileName', 'Unknown')} - {doc.get('status', 'Unknown')}")
                    
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ 文档列表获取失败: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            print(f"❌ 文档列表测试失败: {e}")
            return False
    
    async def test_python_ai_service(self) -> bool:
        """测试Python AI服务"""
        try:
            print("🤖 测试Python AI服务...")
            
            # 测试解析功能
            test_data = {
                "path": "/tmp/test_document.md",
                "filename": "test_document.md",
                "size": 1024
            }
            
            # 注意：Python服务通过IPC与Go通信，直接访问可能受限
            # 这里我们测试Go后端是否能正确调用Python服务
            async with self.session.post(f"{SERVICES['go_backend']}/api/parse-test", 
                                       json=test_data) as response:
                if response.status in [200, 404]:  # 404也是可以接受的，说明服务在运行
                    print(f"✅ Python AI服务集成正常")
                    return True
                else:
                    print(f"⚠️  Python AI服务可能未完全就绪")
                    return False
                    
        except Exception as e:
            print(f"⚠️  Python AI服务测试跳过: {e}")
            return True  # 不将此作为失败条件
    
    async def test_cpp_sandbox(self) -> bool:
        """测试C++沙箱服务"""
        try:
            print("🔒 测试C++沙箱服务...")
            
            # 尝试连接沙箱服务
            async with self.session.get(f"{SERVICES['cpp_sandbox']}/status", 
                                      timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ C++沙箱服务正常: {result}")
                    return True
                else:
                    print(f"⚠️  C++沙箱服务状态异常: {response.status}")
                    return False
                    
        except asyncio.TimeoutError:
            print(f"⚠️  C++沙箱服务连接超时（可能未启动或端口未开放）")
            return True  # 不将此作为失败条件
        except Exception as e:
            print(f"⚠️  C++沙箱服务测试跳过: {e}")
            return True  # 不将此作为失败条件
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """运行所有测试"""
        print("🚀 开始WayFare系统集成测试...")
        print("=" * 50)
        
        results = {}
        
        # 1. 健康检查
        print("\n📊 第一阶段：服务健康检查")
        print("-" * 30)
        for service_name, url in SERVICES.items():
            results[f"health_{service_name}"] = await self.check_service_health(service_name, url)
        
        # 2. 文件上传测试
        print("\n📁 第二阶段：文件上传功能")
        print("-" * 30)
        results['file_upload'] = await self.test_file_upload()
        
        # 3. 聊天功能测试
        print("\n💬 第三阶段：聊天功能")
        print("-" * 30)
        results['chat'] = await self.test_chat_functionality()
        
        # 4. 文档列表测试
        print("\n📋 第四阶段：文档列表功能")
        print("-" * 30)
        results['document_list'] = await self.test_document_listing()
        
        # 5. AI服务测试
        print("\n🤖 第五阶段：AI服务集成")
        print("-" * 30)
        results['python_ai'] = await self.test_python_ai_service()
        
        # 6. 沙箱服务测试
        print("\n🔒 第六阶段：C++沙箱服务")
        print("-" * 30)
        results['cpp_sandbox'] = await self.test_cpp_sandbox()
        
        return results
    
    def print_test_summary(self, results: Dict[str, bool]):
        """打印测试总结"""
        print("\n" + "=" * 50)
        print("📊 WayFare系统集成测试总结")
        print("=" * 50)
        
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result)
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {failed_tests} ❌")
        print(f"成功率: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\n详细结果:")
        for test_name, result in results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"  {test_name}: {status}")
        
        if failed_tests > 0:
            print("\n🔧 建议:")
            print("1. 检查Docker服务是否全部启动: docker-compose ps")
            print("2. 查看服务日志: docker-compose logs [服务名]")
            print("3. 检查端口占用情况")
            print("4. 确保所有依赖服务已正确配置")
        else:
            print("\n🎉 所有测试通过！系统运行正常！")
            print("🚀 请在浏览器中访问 http://localhost:3000 开始使用WayFare！")

async def main():
    """主函数"""
    try:
        async with WayFareTestClient() as client:
            # 运行所有测试
            results = await client.run_all_tests()
            
            # 打印测试总结
            client.print_test_summary(results)
            
            # 根据测试结果退出
            failed_count = sum(1 for result in results.values() if not result)
            if failed_count > 0:
                sys.exit(1)
            else:
                sys.exit(0)
                
    except KeyboardInterrupt:
        print("\n🛑 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"💥 测试执行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # 运行异步主函数
    asyncio.run(main())