// WayFare API联调测试工具
import { api } from './client';

export class WayFareDebugger {
  private static instance: WayFareDebugger;
  
  static getInstance(): WayFareDebugger {
    if (!this.instance) {
      this.instance = new WayFareDebugger();
    }
    return this.instance;
  }

  // 测试API连接
  async testConnection(): Promise<void> {
    console.log('🔍 开始API连接测试...');
    
    try {
      // 1. 测试健康检查
      console.log('1️⃣ 测试健康检查...');
      const health = await api.healthCheck();
      console.log('   ✅ 健康检查:', health.success ? '通过' : '失败', health.data);
      
      // 2. 测试系统状态
      console.log('2️⃣ 测试系统状态...');
      const status = await api.getSystemStatus();
      console.log('   ✅ 系统状态:', status.success ? '通过' : '失败', status.data);
      
      // 3. 测试文档列表
      console.log('3️⃣ 测试文档列表...');
      const docs = await api.getDocuments();
      console.log('   ✅ 文档列表:', docs.success ? '通过' : '失败', 
        docs.success ? `找到 ${docs.data?.length || 0} 个文档` : docs.error);
      
      console.log('🎉 API连接测试完成！');
      
    } catch (error) {
      console.error('❌ API连接测试失败:', error);
    }
  }

  // 测试文件上传
  async testFileUpload(file: File): Promise<void> {
    console.log(`📁 测试文件上传: ${file.name}`);
    
    try {
      const response = await api.uploadDocument(file, (progress) => {
        console.log(`   📊 上传进度: ${Math.round(progress)}%`);
      });
      
      if (response.success) {
        console.log('   ✅ 文件上传成功:', {
          id: response.data.id,
          filename: response.data.filename,
          docHash: response.data.docHash,
          status: response.data.status
        });
      } else {
        console.error('   ❌ 文件上传失败:', response.error);
      }
      
    } catch (error) {
      console.error('   ❌ 文件上传错误:', error);
    }
  }

  // 测试聊天功能
  async testChat(message: string, docHash?: string): Promise<void> {
    console.log(`💬 测试聊天功能: "${message}" ${docHash ? `(doc: ${docHash})` : ''}`);
    
    try {
      const response = await api.sendChatMessage(message, docHash);
      
      if (response.success) {
        console.log('   ✅ 聊天测试成功:', {
          message: response.data.message,
          knowledgePoint: response.data.knowledgePoint,
          type: response.data.type
        });
      } else {
        console.error('   ❌ 聊天测试失败:', response.error);
      }
      
    } catch (error) {
      console.error('   ❌ 聊天测试错误:', error);
    }
  }

  // 完整的联调测试
  async runFullTest(): Promise<void> {
    console.log('🚀 开始完整的WayFare联调测试...\n');
    
    // 1. 连接测试
    await this.testConnection();
    console.log('');
    
    // 2. 如果有测试文件，可以在这里添加文件上传测试
    // await this.testFileUpload(testFile);
    
    // 3. 聊天测试
    await this.testChat('你好，请介绍一下WayFare系统');
    console.log('');
    
    console.log('🏁 联调测试完成！');
  }
}

// 创建全局调试器实例
export const wayfareDebugger = WayFareDebugger.getInstance();

// 在浏览器控制台中可用的快捷命令
if (typeof window !== 'undefined') {
  (window as any).WayFareDebug = {
    testConnection: () => wayfareDebugger.testConnection(),
    testChat: (message: string, docHash?: string) => wayfareDebugger.testChat(message, docHash),
    runFullTest: () => wayfareDebugger.runFullTest(),
    api: api
  };
  
  console.log('🛠️  WayFare调试工具已加载！');
  console.log('💡 可用命令:');
  console.log('   WayFareDebug.testConnection() - 测试API连接');
  console.log('   WayFareDebug.testChat(msg, docHash?) - 测试聊天功能');
  console.log('   WayFareDebug.runFullTest() - 运行完整测试');
  console.log('   WayFareDebug.api - API客户端实例');
}