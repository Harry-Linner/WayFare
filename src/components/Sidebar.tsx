import { useState } from 'react';
import { Send, Bot, Brain } from 'lucide-react';
import type { ChatMessage } from '../types.js';

export function Sidebar() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (!input.trim()) return;
    
    const newUserMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    };
    
    setMessages([...messages, newUserMsg]);
    setInput('');
    
    // Mock AI response
    setTimeout(() => {
      const aiMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '好的，正在为你调用费曼转化器... \n\n简单来说，工作记忆就像是电脑的内存（RAM），而长期记忆是硬盘。当你阅读这段文字时，文字信息就在你的“内存”里处理。因为内存容量有限（7±2），所以我们需要“组块化”——就像把零散的文件打包成一个 ZIP 压缩包，这样就能在内存里放下更多东西了。',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, aiMsg]);
    }, 1000);
  };

  return (
    <div className="flex flex-col h-full">
      <div className="h-12 border-b border-gray-200 flex items-center px-4 bg-white">
          <h2 className="font-semibold text-gray-800 flex items-center space-x-2">
          <Bot size={18} className="text-indigo-600" />
          <span>AI 导师</span>
        </h2>
        <span className="ml-auto text-xs text-stone-500 flex items-center space-x-1">
          <Brain size={14} />
          <span>Sidecar Kernel</span>
        </span>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-white">
        {messages.map(msg => (
          <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] rounded-2xl px-4 py-3 ${
              msg.role === 'user' 
                ? 'bg-gray-200 text-gray-900 rounded-tr-sm' 
                : 'bg-gray-100 text-gray-800 rounded-tl-sm'
            }`}>
              <div className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="p-4 border-t border-gray-200 bg-white">
        <div className="relative flex items-center">
          <textarea 
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="向 AI 导师提问..."
            className="w-full bg-stone-50 border border-stone-200 rounded-xl pl-4 pr-12 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 resize-none"
            rows={1}
          />
          <button 
            onClick={handleSend}
            className="absolute right-2 w-8 h-8 flex items-center justify-center text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <Send size={18} />
          </button>
        </div>
        <div className="mt-2 text-xs text-stone-400 text-center">
          基于本地 RAG 引擎与教育专用模型
        </div>
      </div>
    </div>
  );
}
