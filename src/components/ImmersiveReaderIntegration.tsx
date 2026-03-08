/**
 * 沉浸式阅读器集成示例
 * 
 * 演示如何集成所有修复的交互监控、事件监听、批注渲染
 * 这是一个完整的参考实现
 */

import React, { useEffect, useRef, useCallback } from 'react';
import { useAppStore } from '../store/appStore';
import { useInteractionMonitor } from '../hooks/useInteractionMonitor';
import { useBackendEventListeners } from '../hooks/useBackendEvents';
import { AnnotationBubble } from './AnnotationBubble';
import type { EnhancedAnnotation, ChatMessage } from '../types';
import './Reader.css';

interface ImmersiveReaderProps {
  documentId: string
  documentType: 'pdf' | 'markdown'
  content: string
  annotations?: EnhancedAnnotation[]
  onAnnotationClick?: (annotationId: string) => void
}

/**
 * 沉浸式阅读器组件
 * 
 * 核心功能：
 * 1. 显示 PDF 或 Markdown 内容
 * 2. 渲染批注气泡（关键概念、难点标记）
 * 3. 追踪用户交互（滚动、停留、高亮）
 * 4. 接收 Agent 主动推送消息
 * 5. 提供侧边栏对话框
 */
export function ImmersiveReader({
  documentId,
  documentType,
  content,
  annotations = [],
  onAnnotationClick,
}: ImmersiveReaderProps) {
  const readerRef = useRef<HTMLDivElement>(null);
  const { currentDocument, updateDocument } = useAppStore();

  // ============= 1. 启动交互监控 =============
  // 这个 hook 会：
  // - 追踪用户滚动、高亮、点击、悬停
  // - 每 30 秒批量将数据发送给 Tauri
  // - 当用户停留超过 3 分钟时触发卡顿检测
  const { recordManualInteraction, flush, getPendingCount } = useInteractionMonitor(
    {
      enableTracking: true,
      recordDelay: 500, // 500ms 后记录滚动
      highlightDebounce: 300, // 高亮后 300ms 记录
      batchSize: 20, // 累积 20 条交互后批量上传
      flushInterval: 30000, // 每 30 秒强制上传
    },
    {
      documentId,
      pageNumber: 1, // TODO: 对于 PDF，这应该从视图中动态获取
      onError: (error) => {
        console.error('交互监控错误:', error);
        // 可选：显示用户通知
      },
    }
  );

  // ============= 2. 启动后端事件监听 =============
  // 这个 hook 会：
  // - 监听所有后端推送的事件
  // - 自动转换为聊天消息
  // - 在侧边栏显示 Agent 的主动帮助
  useBackendEventListeners({
    autoAddMessages: true,
    onError: (error) => {
      console.error('后端事件错误:', error);
    },
  });

  // ============= 3. 处理批注点击 =============
  const handleAnnotationClick = (annotationId: string) => {
    console.log('用户点击批注:', annotationId);

    // 记录用户与批注的交互
    recordManualInteraction('click', {
      annotation_id: annotationId,
      action: 'click',
    });

    onAnnotationClick?.(annotationId);

    // 打开详情对话框
    // TODO: 调用侧边栏显示批注详情
  };

  // ============= 3.5. 处理批注反馈提交 =============
  const handleFeedbackSubmit = useCallback(
    (annotationId: string, feedback: string, clarifications: string[]) => {
      console.log('📝 用户提交了批注反馈:', annotationId, feedback, clarifications);

      // 更新本地批注对象
      const annotation = annotations.find((a) => a.id === annotationId);
      if (annotation) {
        // 这里你可以：
        // 1. 调用 Tauri 命令存储这个反馈
        // 2. 更新 store 中的批注
        // 3. 通知后端分析学生的反馈（是否需要进一步帮助）
        recordManualInteraction('click', {
          annotation_id: annotationId,
          action: 'feedback_submit',
          metadata: {
            feedback_length: feedback.length,
            clarification_count: clarifications.length,
          },
        });

        // TODO: 调用 Tauri 保存反馈
        // await saveFeedback({ annotationId, feedback, clarifications });
      }
    },
    [annotations, recordManualInteraction]
  );

  // ============= 4. 处理页面变化 =============
  useEffect(() => {
    // 当打开新文档时记录
    if (currentDocument?.id !== documentId) {
      updateDocument(documentId, {
        updatedAt: Date.now(),
      });
    }
  }, [documentId, currentDocument?.id, updateDocument]);

  // ============= 5. 组件卸载时确保数据上报 =============
  useEffect(() => {
    return () => {
      // 确保所有待发送的交互数据都被上报
      console.log('📤 阅读器卸载，上报剩余交互数据...');
      flush();
    };
  }, [flush]);

  return (
    <div className="immersive-reader-container">
      {/* 主内容区域 */}
      <div className="reader-main" ref={readerRef} data-content-area>
        {documentType === 'markdown' ? (
          <MarkdownContent
            content={content}
            onHighlight={(text) => {
              recordManualInteraction('highlight', {
                text: text.substring(0, 100),
              });
            }}
          />
        ) : (
          <PDFContent
            content={content}
            // PDF.js 会在这里渲染
          />
        )}

        {/* 批注气泡叠加层 */}
        <div className="annotations-overlay">
          {annotations.map((annotation) => (
            <AnnotationBubble
              key={annotation.id}
              annotation={annotation}
              onDismiss={() => {
                recordManualInteraction('click', {
                  annotation_id: annotation.id,
                  action: 'dismiss',
                });
              }}
              onRequestDetail={() => {
                handleAnnotationClick(annotation.id);
              }}
              onAskQuestion={() => {
                recordManualInteraction('click', {
                  annotation_id: annotation.id,
                  action: 'ask_question',
                });
                // 触发后端生成详细解释
              }}
              onFeedbackSubmit={handleFeedbackSubmit}
            />
          ))}
        </div>
      </div>

      {/* 右侧 AI 导师面板 */}
      <div className="reader-sidebar">
        <AITutorPanel documentId={documentId} />

        {/* 调试信息（开发用） */}
        {import.meta.env.DEV && (
          <div className="debug-panel" style={{ marginTop: '20px', fontSize: '12px', color: '#999' }}>
            <p>待上报交互: {getPendingCount()} 条</p>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Markdown 内容渲染器
 * 支持语法高亮、代码块、数学公式等
 */
function MarkdownContent({
  content,
  onHighlight,
}: {
  content: string
  onHighlight?: (text: string) => void
}) {
  const handleTextSelect = useCallback(() => {
    const selection = window.getSelection();
    if (selection && selection.toString().length > 0) {
      onHighlight?.(selection.toString());
    }
  }, [onHighlight]);

  useEffect(() => {
    document.addEventListener('selectionchange', handleTextSelect);
    return () => {
      document.removeEventListener('selectionchange', handleTextSelect);
    };
  }, [handleTextSelect]);

  return (
    <div className="markdown-renderer" data-hoverable>
      {/* TODO: 使用 Milkdown 渲染 Markdown */}
      <div
        className="markdown-content"
        dangerouslySetInnerHTML={{
          __html: content, // 实际应该使用安全的 markdown 解析器
        }}
      />
    </div>
  );
}

/**
 * PDF 内容渲染器
 * 使用 pdf.js 进行渲染
 */
function PDFContent({ content }: { content: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    // TODO: 集成 pdf.js 进行 PDF 渲染
    // const pdfDoc = await pdfjsLib.getDocument(content).promise;
    // const page = await pdfDoc.getPage(1);
    // const viewport = page.getViewport({ scale: 1.5 });
    // const canvas = canvasRef.current;
    // const context = canvas.getContext('2d');
    // await page.render({ canvasContext: context, viewport }).promise;
  }, [content]);

  return (
    <div className="pdf-renderer" data-hoverable>
      <canvas ref={canvasRef} className="pdf-canvas" />
    </div>
  );
}

/**
 * AI 导师面板
 * 显示对话框、学习建议、资源推荐
 */
function AITutorPanel({ documentId }: { documentId: string }) {
  const {
    conversations,
    currentConversationId,
    addChatMessage,
  } = useAppStore();

  const conversation = currentConversationId
    ? conversations.find((c) => c.id === currentConversationId)
    : null;

  const handleSendMessage = async (content: string) => {
    if (!currentConversationId) return;
    
    // 使用 documentId 来追踪消息的上下文
    console.log('📨 用户向 AI 提问，文档:', documentId);

    // 1. 添加用户消息到本地 Store
    const userMessage: ChatMessage = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
      documentId,
    };
    addChatMessage(currentConversationId, userMessage);

    // 2. TODO: 调用后端 API 获取 AI 响应
    // const response = await invoke('get_ai_response', {
    //   conversation_id: currentConversationId,
    //   message: content,
    //   document_context: documentId,
    // });

    // 3. 添加 AI 响应
    const assistantMessage: ChatMessage = {
      id: `msg_${Date.now() + 1}`,
      role: 'assistant',
      content: '（处理中...）',
      timestamp: new Date().toISOString(),
      documentId,
    };
    addChatMessage(currentConversationId, assistantMessage);
  };

  return (
    <div className="ai-tutor-panel">
      {/* 聊天消息区域 */}
      <div className="chat-messages" style={{ flex: 1, overflowY: 'auto' }}>
        {conversation?.messages.map((msg) => (
          <div
            key={msg.id}
            className={`chat-message ${msg.role}`}
            style={{
              marginBottom: '12px',
              padding: '8px',
              borderRadius: '8px',
              backgroundColor: msg.role === 'user' ? '#e3f2fd' : '#f5f5f5',
            }}
          >
            <div style={{ fontSize: '12px', fontWeight: 'bold', marginBottom: '4px' }}>
              {msg.role === 'user' ? '你' : 'AI 导师'}
            </div>
            <div style={{ fontSize: '13px', lineHeight: '1.5' }}>{msg.content}</div>
            {msg.timestamp && (
              <div style={{ fontSize: '11px', color: '#999', marginTop: '4px' }}>
                {new Date(msg.timestamp).toLocaleTimeString()}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* 消息输入区域 */}
      <div style={{ borderTop: '1px solid #ddd', paddingTop: '12px', marginTop: '12px' }}>
        <ChatInput onSend={handleSendMessage} />
      </div>
    </div>
  );
}

/**
 * 聊天输入框
 */
function ChatInput({ onSend }: { onSend: (message: string) => void }) {
  const [input, setInput] = React.useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      onSend(input);
      setInput('');
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '8px' }}>
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="询问 AI 导师..."
        style={{
          flex: 1,
          padding: '8px 12px',
          border: '1px solid #ddd',
          borderRadius: '4px',
          fontSize: '13px',
        }}
      />
      <button
        type="submit"
        style={{
          padding: '8px 16px',
          backgroundColor: '#1976d2',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer',
          fontSize: '13px',
        }}
      >
        发送
      </button>
    </form>
  );
}

export default ImmersiveReader;
