import { useState, useEffect, useRef, useCallback } from 'react';
import { FileText, BookOpen, Loader, Plus, Trash2, Download, MessageSquare, Copy, Image, Presentation } from 'lucide-react';
import { MarkdownEditor } from './MarkdownEditor';
import { PDFReader } from './PDFReader';
import { FileUpload } from './FileUpload';
import { ImagePreview } from './ImagePreview';
import { PPTPreview } from './PPTPreview';
import { useAppStore } from '../store/appStore';
import { useInteractionMonitor } from '../hooks/useInteractionMonitor';
import { useBackendEventListeners } from '../hooks/useBackendEvents';
import { useTauriCommands } from '../hooks/useTauriCommands';
import type { Annotation, AnnotationFile, Document } from '../types.js';

interface ReaderProps {
  documentId?: string;
}

/// 划词工具栏位置和内容
interface SelectionToolbar {
  visible: boolean;
  x: number;
  y: number;
  selectedText: string;
}

export function Reader({ documentId }: ReaderProps = {}) {
  const [mode, setMode] = useState<'pdf' | 'markdown' | 'image' | 'ppt'>('markdown');
  const [loading, setLoading] = useState(false);
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [content, setContent] = useState('');
  const [currentDocument, setCurrentDocument] = useState<Document | null>(null);
  const [selectedAnnotation, setSelectedAnnotation] = useState<Annotation | null>(null);
  const [annotationPos, setAnnotationPos] = useState<{ x: number; y: number; isAbsolute?: boolean } | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newAnnotationText, setNewAnnotationText] = useState('');
  const [selectedText, setSelectedText] = useState<{ text: string; position: { x: number; y: number } } | null>(null);
  const [selectionToolbar, setSelectionToolbar] = useState<SelectionToolbar>({ visible: false, x: 0, y: 0, selectedText: '' });
  const [showFileUpload, setShowFileUpload] = useState(true);
  const [fileContent, setFileContent] = useState<ArrayBuffer | null>(null);
  
  console.log('🔄 Reader 组件渲染，showFileUpload:', showFileUpload, 'currentDocument:', currentDocument);
  
  const contentAreaRef = useRef<HTMLDivElement>(null);
  const editorRef = useRef<HTMLDivElement>(null);
  const selectionToolbarRef = useRef<HTMLDivElement>(null);

  const { addDocument, setCurrentDocument: setCurrentDocStore, updateDocument } = useAppStore();
  
  // ============ 启动后端事件监听 ============
  // 监听 Agent 主动推送的消息、学习计划、复习提醒等
  useBackendEventListeners({
    autoAddMessages: true,
    onError: (error) => {
      console.error('❌ 后端事件错误:', error);
    },
  });

  // ============ 启动 Tauri 命令接口 ============
  // 获取与 Tauri 中枢通信的命令函数
  const { saveAnnotation } = useTauriCommands();

  // ============ 启动交互监控 ============
  // 追踪用户的滚动、高亮、点击事件
  // 定期向 Tauri 中枢上报交互数据
  // 当用户停留超过 3 分钟时自动触发卡顿检测
  const { recordManualInteraction, flush } = useInteractionMonitor(
    {
      enableTracking: true,
      recordDelay: 500, // 500ms 后记录滚动
      highlightDebounce: 300, // 高亮后 300ms 记录
      batchSize: 20, // 累积 20 条后批量上传
      flushInterval: 30000, // 30 秒强制上传一次
    },
    {
      documentId: documentId || 'unknown',
      pageNumber: 1,
      onError: (error) => {
        console.error('❌ 交互监控错误:', error);
      },
    }
  );

  // ============ 隐藏划词工具栏的函数 ============
  // 当用户点击其他地方时调用
  const hideSelectionToolbar = useCallback(() => {
    setSelectionToolbar((prev) => ({ ...prev, visible: false }));
  }, []);

  // 组件卸载时确保所有交互数据已上报
  useEffect(() => {
    return () => {
      console.log('📤 组件卸载，尝试上报剩余交互数据...');
      flush()
        .then(() => console.log('✅ 剩余交互数据已上报'))
        .catch((error) => console.error('❌ 上报失败:', error));
    };
  }, [flush]);

  // 隐藏划词工具栏当用户点击其他地方时
  useEffect(() => {
    const handleClickOutside = () => {
      if (selectionToolbar.visible) {
        setTimeout(() => {
          hideSelectionToolbar();
        }, 100);
      }
    };

    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, [selectionToolbar.visible, hideSelectionToolbar]);


  useEffect(() => {
    const loadSampleData = async () => {
      try {
        setLoading(true);
        const markdownRes = await fetch('/sample-data/cognitive-psychology.md');
        const markdownText = await markdownRes.text();
        const annotationsRes = await fetch('/sample-data/cognitive-psychology.annotations.json');
        const annotationData: AnnotationFile = await annotationsRes.json();
        const doc: Document = {
          id: 'doc_cognitive_psychology',
          name: '认知心理学基础',
          path: '/sample-data/cognitive-psychology.md',
          type: 'markdown',
          content: markdownText,
          createdAt: Date.now(),
          updatedAt: Date.now(),
        };
        setContent(markdownText);
        setAnnotations(annotationData.annotations);
        setCurrentDocument(doc);
        setCurrentDocStore(doc);
        addDocument(doc);
      } catch (error) {
        console.error('Failed to load sample data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadSampleData();
  }, [addDocument, setCurrentDocStore]);

  const handleEditMarkdown = (newContent: string) => {
    setContent(newContent);
    if (currentDocument) {
      const updatedDoc = {
        ...currentDocument,
        content: newContent,
        updatedAt: Date.now(),
      };
      setCurrentDocument(updatedDoc);
      // Update in store
      updateDocument(currentDocument.id, updatedDoc);
    }
  };

  const handleSaveMarkdown = (finalContent: string) => {
    if (currentDocument) {
      const updatedDoc = {
        ...currentDocument,
        content: finalContent,
        updatedAt: Date.now(),
      };
      setContent(finalContent);
      setCurrentDocument(updatedDoc);
      // Update in store
      updateDocument(currentDocument.id, updatedDoc);
      
      // 📊 记录文档保存交互
      recordManualInteraction('click', {
        action: 'save_document',
        documentId: currentDocument.id,
        contentLength: finalContent.length,
      });
      
      // Log confirmation
      const timestamp = new Date().toLocaleTimeString('zh-CN');
      console.log(`✅ 文档已保存 (${currentDocument.name}) - ${timestamp}`);
      console.log('💾 已保存到 localStorage');
    }
  };

  // Handle scroll to update annotation panel position
  useEffect(() => {
    if (!contentAreaRef.current) return;
    
    const scrollElement = contentAreaRef.current;
    
    const handleScroll = () => {
      if (selectedAnnotation && annotationPos) {
        const scrollTop = scrollElement.scrollTop || 0;
        // Update annotation panel Y position based on scroll
        // We need to track the original position and adjust for scroll
        // This keeps the panel visible when scrolling
        if (annotationPos.y > window.innerHeight * 0.7) {
          // If panel is near bottom, don't let it scroll out of view
          const newY = Math.max(15, annotationPos.y - (scrollTop * 0.5));
          setAnnotationPos({ ...annotationPos, y: newY });
        }
      }
    };
    
    scrollElement.addEventListener('scroll', handleScroll);
    return () => scrollElement.removeEventListener('scroll', handleScroll);
  }, [selectedAnnotation, annotationPos]);

  const handleRequestDetail = (annotationId: string) => {
    // Find the annotation and show it in Sidebar
    const annotation = annotations.find((a) => a.id === annotationId);
    if (annotation) {
      // This would trigger Sidebar to show the annotation detail
      console.log('Requesting detail for:', annotation.content);
      // You can emit an event or use context to notify Sidebar
    }
  };

  const copySelectedText = () => {
    if (selectedText?.text) {
      navigator.clipboard.writeText(selectedText.text);
      console.log('✅ 已复制:', selectedText.text);
    }
  };

  // 处理文件上传
  const handleFilesSelected = (files: File[]) => {
    console.log('📁 接收到文件选择回调:', files.length, '个文件');
    files.forEach((file) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const result = e.target?.result;
        let content = '';
        let docType: 'pdf' | 'markdown' | 'image' | 'ppt' = 'markdown';
        
        // 判断文件类型
        if (file.type.startsWith('image/') || ['.png', '.jpg', '.jpeg', '.gif', '.webp'].some(ext => file.name.toLowerCase().endsWith(ext))) {
          docType = 'image';
          content = URL.createObjectURL(file);
        } else if (file.name.toLowerCase().endsWith('.pdf')) {
          docType = 'pdf';
          content = URL.createObjectURL(file);
        } else if (['.ppt', '.pptx'].some(ext => file.name.toLowerCase().endsWith(ext))) {
          docType = 'ppt';
          content = URL.createObjectURL(file);
          setFileContent(result as ArrayBuffer);
        } else {
          docType = 'markdown';
          content = result as string;
        }

        const doc: Document = {
          id: `doc_${Date.now()}`,
          name: file.name,
          path: file.name,
          type: docType,
          content: content,
          createdAt: Date.now(),
          updatedAt: Date.now(),
        };
        
        setContent(content);
        setCurrentDocument(doc);
        setMode(docType);
        setShowFileUpload(false);
        addDocument(doc);
        console.log('✅ 文件已加载:', file.name, '|', docType, '| showFileUpload 应该变为:', false);
      };
      
      if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pptx') || file.name.toLowerCase().endsWith('.ppt')) {
        reader.readAsArrayBuffer(file);
      } else if (file.type.startsWith('image/') || ['.png', '.jpg', '.jpeg', '.gif', '.webp'].some(ext => file.name.toLowerCase().endsWith(ext))) {
        reader.readAsDataURL(file);
      } else {
        reader.readAsText(file);
      }
    });
  };

  // 处理文件夹上传
  const handleFolderSelected = (files: File[]) => {
    console.log('📁 文件夹已选择，共', files.length, '个文件');
    // 加载第一个文件
    if (files.length > 0) {
      handleFilesSelected([files[0]]);
    }
  };

  // Handle text selection for creating annotations
  const handleTextSelection = () => {
    const selection = window.getSelection();
    if (selection && selection.toString().length > 0 && editorRef.current) {
      const selectedText = selection.toString();
      const range = selection.getRangeAt(0);
      const rect = range.getBoundingClientRect();
      
      if (editorRef.current) {
        const editorRect = editorRef.current.getBoundingClientRect();
        // Calculate position as percentage of editor
        const relativeX = (rect.left - editorRect.left) / editorRect.width * 100;
        const relativeY = (rect.top - editorRect.top) / editorRect.height * 100;
        
        setSelectedText({
          text: selectedText,
          position: { x: Math.max(0, Math.min(100, relativeX)), y: Math.max(0, Math.min(100, relativeY)) }
        });
        
        // 显示划词工具栏
        setSelectionToolbar({
          visible: true,
          x: rect.left + rect.width / 2,
          y: rect.top - 10,
          selectedText: selectedText
        });

        // 📊 记录文本选择交互
        recordManualInteraction('highlight', {
          selectedLength: selectedText.length,
          position: { x: relativeX, y: relativeY },
        });
      }
    }
  };

  const handleCreateAnnotation = async () => {
    if (!newAnnotationText.trim() || !currentDocument) return;

    const newAnnotation: Annotation = {
      id: `anno_${Date.now()}`,
      documentId: currentDocument.id,
      sourceText: selectedText?.text || newAnnotationText.substring(0, 50),
      position: selectedText ? selectedText.position : { x: 50, y: 50 },
      content: newAnnotationText,
      type: 'bubble',
      severity: 'medium',
      category: 'learning_strategy',
      createdAt: Date.now(),
      updatedAt: Date.now(),
    };

    setAnnotations([...annotations, newAnnotation]);
    setNewAnnotationText('');
    setSelectedText(null);
    setShowCreateForm(false);
    
    // 📊 记录批注创建交互
    recordManualInteraction('click', {
      action: 'create_annotation',
      annotationType: newAnnotation.type,
      category: newAnnotation.category,
      contentLength: newAnnotation.content.length,
    });
    
    // 保存批注到数据库
    try {
      await saveAnnotation(
        newAnnotation.id,
        newAnnotation.documentId,
        newAnnotation.sourceText || null,
        newAnnotation.content,
        newAnnotation.position.x,
        newAnnotation.position.y,
        newAnnotation.position.page || null,
        newAnnotation.type,
        newAnnotation.severity || 'medium',
        newAnnotation.category,
        'analogy'
      );
      console.log('✅ 批注已保存到数据库:', newAnnotation.id);
    } catch (error) {
      console.error('保存批注失败:', error);
    }
  };

  const handleDeleteAnnotation = (annotationId: string) => {
    setAnnotations(annotations.filter((a) => a.id !== annotationId));
    setSelectedAnnotation(null);
    
    // 📊 记录删除批注交互
    recordManualInteraction('click', {
      action: 'delete_annotation',
      annotationId: annotationId,
    });
    
    console.log('✅ Annotation deleted:', annotationId);
  };

  // Export/Save document to file system
  const handleExportDocument = async () => {
    if (!currentDocument) return;
    
    try {
      // Try to use Tauri if available for native file save
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const anyWindow = window as any;
      if (anyWindow.__TAURI__) {
        const { invoke } = anyWindow.__TAURI__?.core || anyWindow.__TAURI__;
        if (invoke) {
          await invoke('save_document_file', {
            name: currentDocument.name,
            content: content
          });
          console.log('✅ 文件已保存到磁盘');
          return;
        }
      }
      
      // Fallback: Browser download
      const element = document.createElement('a');
      element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(content));
      element.setAttribute('download', currentDocument.name);
      element.style.display = 'none';
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);
      console.log('✅ 文件已下载，请保存到项目目录');
    } catch (error) {
      console.error('保存文件失败:', error);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full relative">
      {/* Toolbar */}
      <div className="h-12 border-b border-stone-200 flex items-center px-4 justify-between bg-white z-10">
        <div className="flex space-x-2">
          {currentDocument && (
            <>
              {currentDocument.type === 'markdown' && (
                <button 
                  onClick={() => setMode('markdown')}
                  className={`px-3 py-1.5 rounded-md text-sm font-medium flex items-center space-x-2 transition-colors ${mode === 'markdown' ? 'bg-indigo-50 text-indigo-700' : 'text-stone-600 hover:bg-stone-100'}`}
                >
                  <BookOpen size={16} />
                  <span>编辑</span>
                </button>
              )}
              {currentDocument.type === 'pdf' && (
                <button 
                  onClick={() => setMode('pdf')}
                  className={`px-3 py-1.5 rounded-md text-sm font-medium flex items-center space-x-2 transition-colors ${mode === 'pdf' ? 'bg-indigo-50 text-indigo-700' : 'text-stone-600 hover:bg-stone-100'}`}
                >
                  <FileText size={16} />
                  <span>PDF</span>
                </button>
              )}
              {currentDocument.type === 'image' && (
                <button 
                  onClick={() => setMode('image')}
                  className={`px-3 py-1.5 rounded-md text-sm font-medium flex items-center space-x-2 transition-colors bg-indigo-50 text-indigo-700`}
                >
                  <Image size={16} />
                  <span>图片</span>
                </button>
              )}
              {currentDocument.type === 'ppt' && (
                <button 
                  onClick={() => setMode('ppt')}
                  className={`px-3 py-1.5 rounded-md text-sm font-medium flex items-center space-x-2 transition-colors bg-indigo-50 text-indigo-700`}
                >
                  <Presentation size={16} />
                  <span>演示</span>
                </button>
              )}
              {(currentDocument.type === 'markdown' || currentDocument.type === 'pdf') && (
                <button 
                  onClick={handleExportDocument}
                  className="px-3 py-1.5 rounded-md text-sm font-medium flex items-center space-x-2 transition-colors text-stone-600 hover:bg-stone-100"
                  title="保存文件到本地"
                >
                  <Download size={16} />
                  <span>保存</span>
                </button>
              )}
            </>
          )}
          <button
            onClick={() => {
              console.log('🔍 点击了上传文件按钮，currentDocument:', currentDocument, 'showFileUpload:', showFileUpload);
              setShowFileUpload(true);
              setCurrentDocument(null);
              setContent('');
              setAnnotations([]);
            }}
            className="px-3 py-1.5 rounded-md text-sm font-medium flex items-center space-x-2 transition-colors text-stone-600 hover:bg-stone-100"
            title="上传新文件"
          >
            <Plus size={16} />
            <span>上传文件</span>
          </button>
        </div>
        <div className="text-sm text-stone-500 flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>互动监测中</span>
          {currentDocument && (
            <span className="ml-4 text-xs bg-indigo-50 text-indigo-700 px-2 py-1 rounded-md">
              {currentDocument.name} • {annotations.length} 个批注
            </span>
          )}
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-hidden bg-stone-100 relative">
        {/* 文件上传面板 */}
        {showFileUpload && (
          <div className="h-full overflow-auto bg-stone-50">
            <div className="max-w-2xl mx-auto p-8">
              <div className="mb-6 flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-stone-900 mb-2">开始学习</h2>
                  <p className="text-stone-600">上传您的学习资料（PDF、Markdown 或 TXT 文件）</p>
                </div>
                <button
                  onClick={() => {
                    console.log('❌ 点击了关闭按钮');
                    setShowFileUpload(false);
                  }}
                  className="text-stone-600 hover:text-stone-900 hover:bg-stone-200 p-2 rounded-lg transition-colors"
                  title="关闭上传面板"
                >
                  ✕
                </button>
              </div>
              <FileUpload
                onFilesSelected={handleFilesSelected}
                onFolderSelected={handleFolderSelected}
                supportedFormats={['.md', '.pdf', '.txt', '.doc', '.docx', '.ppt', '.pptx', '.png', '.jpg', '.jpeg', '.gif', '.webp']}
                maxFileSize={100}
              />
            </div>
          </div>
        )}

        {/* 文档内容 */}
        {!showFileUpload && loading && (
          <div className="h-full flex items-center justify-center">
            <div className="flex flex-col items-center space-y-3">
              <Loader className="w-8 h-8 text-indigo-600 animate-spin" />
              <p className="text-stone-600">正在加载文档...</p>
            </div>
          </div>
        )}

        {!showFileUpload && !loading && currentDocument && mode === 'pdf' && (
          <PDFReader
            filePath={content}
            onPageChange={(page, total) => console.log(`Page ${page}/${total}`)}
          />
        )}

        {!showFileUpload && !loading && currentDocument && mode === 'image' && (
          <ImagePreview
            imagePath={content}
            fileName={currentDocument.name}
            onAnnotationClick={() => {
              setSelectedText(null);
              setSelectedAnnotation(null);
              setShowCreateForm(true);
            }}
          />
        )}

        {!showFileUpload && !loading && currentDocument && mode === 'ppt' && (
          <PPTPreview
            filePath={content}
            fileName={currentDocument.name}
            fileContent={fileContent || undefined}
          />
        )}

        {!showFileUpload && !loading && currentDocument && mode === 'markdown' && (
          <div className="h-full flex flex-col relative" data-content-area>
            {/* Annotation Panel - moved to outer level to not be clipped by overflow */}
            {selectedAnnotation && annotationPos && (
              <div
                className="absolute bg-white rounded-lg shadow-2xl border border-stone-200 z-50 flex flex-col"
                style={{
                  left: `${annotationPos.x}px`,
                  top: `${annotationPos.y}px`,
                  width: '340px',
                  maxHeight: '70vh',
                  padding: '16px',
                  minHeight: '200px',
                }}
              >
                {/* Header: Close + Delete buttons - Fixed height */}
                <div className="flex justify-between items-start mb-3 flex-shrink-0">
                  <h4 className="font-semibold text-stone-800 text-sm">
                    {selectedAnnotation.category ? 
                      selectedAnnotation.category.replace(/_/g, ' ').toUpperCase() 
                      : '批注'}
                  </h4>
                  <div className="flex space-x-2">
                    {selectedAnnotation.id.startsWith('anno_') && (
                      <button
                        onClick={() => {
                          handleDeleteAnnotation(selectedAnnotation.id);
                        }}
                        className="text-stone-400 hover:text-red-600 transition-colors flex-shrink-0"
                        title="Delete"
                      >
                        <Trash2 size={16} />
                      </button>
                    )}
                    <button
                      onClick={() => {
                        setSelectedAnnotation(null);
                        setAnnotationPos(null);
                      }}
                      className="text-stone-400 hover:text-stone-600 text-lg flex-shrink-0"
                    >
                      ✕
                    </button>
                  </div>
                </div>

                {/* Scrollable Content Area */}
                <div className="flex-1 overflow-y-auto pr-2">
                  {/* Source text (if available) */}
                  {selectedAnnotation.sourceText && (
                    <div className="text-xs text-stone-600 italic mb-2 pb-2 border-b border-stone-100">
                      "{selectedAnnotation.sourceText}"
                    </div>
                  )}

                  {/* Main content */}
                  <p className="text-sm text-stone-700 leading-relaxed mb-3">
                    {selectedAnnotation.content}
                  </p>

                  {/* Metadata display */}
                  {selectedAnnotation.metadata && (
                    <div className="bg-stone-50 rounded-lg p-2 mb-3 text-xs text-stone-600 space-y-1">
                      {selectedAnnotation.metadata.frequency && (
                        <div className="flex items-center space-x-2">
                          <span>考频: {selectedAnnotation.metadata.frequency}</span>
                        </div>
                      )}
                      {selectedAnnotation.metadata.mistakeRate && (
                        <div>错题率: {Math.round(selectedAnnotation.metadata.mistakeRate * 100)}%</div>
                      )}
                      {selectedAnnotation.metadata.estimatedTimeToUnderstand && (
                        <div>
                          预计学习时间: {Math.round(selectedAnnotation.metadata.estimatedTimeToUnderstand / 60)} 分钟
                        </div>
                      )}
                    </div>
                  )}

                  {/* Deep explanation */}
                  {selectedAnnotation.metadata?.mistakeRate && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-3">
                      <div className="text-xs font-semibold text-blue-900 mb-2 flex items-center space-x-1">
                        <span>💡</span>
                        <span>深入讲解</span>
                      </div>
                      <p className="text-sm text-blue-900 leading-relaxed">
                        根据你的学习数据，这个知识点之前有 {Math.round((selectedAnnotation.metadata.mistakeRate || 0) * 100)}% 的错误率。{selectedAnnotation.content}
                      </p>
                    </div>
                  )}
                </div>

                {/* Action buttons - Fixed footer */}
                <div className="flex space-x-2 pt-3 border-t border-stone-100 mt-3 flex-shrink-0">
                  <button
                    onClick={() => {
                      setSelectedAnnotation(null);
                      setAnnotationPos(null);
                    }}
                    className="flex-1 text-xs text-stone-600 hover:text-stone-800 px-2 py-1 rounded hover:bg-stone-100 transition-colors"
                  >
                    关闭
                  </button>
                  <button
                    onClick={() => {
                      handleRequestDetail(selectedAnnotation.id);
                    }}
                    className="flex-1 text-xs bg-indigo-50 text-indigo-700 px-3 py-1 rounded hover:bg-indigo-100 transition-colors font-medium"
                  >
                    深入讲解
                  </button>
                </div>
              </div>
            )}

            {/* Create Annotation Form - at top for visibility */}
            {showCreateForm && (
              <div className="bg-green-50 border-b border-green-200 p-4 shadow-sm">
                <div className="flex items-center space-x-2 mb-3">
                  <Plus size={18} className="text-green-700" />
                  <h3 className="font-semibold text-stone-800">创建个人批注</h3>
                </div>
                {selectedText && (
                  <div className="mb-3 p-3 bg-white border-l-4 border-green-600 rounded">
                    <p className="text-xs text-stone-500 font-semibold mb-1">选中的文本：</p>
                    <p className="text-sm text-stone-700 italic">"{selectedText.text}"</p>
                  </div>
                )}
                <textarea
                  value={newAnnotationText}
                  onChange={(e) => setNewAnnotationText(e.target.value)}
                  placeholder={selectedText ? "为这段文本添加您的笔记、理解或疑问..." : "输入你的学习笔记或疑问..."}
                  className="w-full p-2 border border-green-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-green-500 resize-none"
                  rows={3}
                />
                <div className="mt-2 flex space-x-2">
                  <button
                    onClick={handleCreateAnnotation}
                    className="px-3 py-1 bg-green-600 text-white rounded text-sm font-medium hover:bg-green-700 transition-colors"
                  >
                    保存批注
                  </button>
                  <button
                    onClick={() => {
                      setShowCreateForm(false);
                      setNewAnnotationText('');
                      setSelectedText(null);
                    }}
                    className="px-3 py-1 bg-stone-200 text-stone-700 rounded text-sm font-medium hover:bg-stone-300 transition-colors"
                  >
                    取消
                  </button>
                </div>
              </div>
            )}
            
            {/* Markdown Content */}
            <div 
              ref={contentAreaRef}
              className="flex-1 overflow-auto p-8 flex justify-center bg-stone-100 relative"
              onScroll={() => {
                // Update annotation panel position to follow scroll
                if (selectedAnnotation && annotationPos) {
                  // Panel position will be updated by the scroll event listener in useEffect
                }
              }}
            >
              {/* 划词工具栏 */}
              {selectionToolbar.visible && (
                <div
                  ref={selectionToolbarRef}
                  className="fixed bg-white border border-stone-300 rounded-lg shadow-lg flex items-center gap-2 p-1 z-50"
                  style={{
                    left: `${selectionToolbar.x - 100}px`,
                    top: `${selectionToolbar.y}px`,
                    transform: 'translateX(-50%)',
                  }}
                  onMouseLeave={hideSelectionToolbar}
                >
                  <button
                    onClick={() => {
                      setShowCreateForm(true);
                      hideSelectionToolbar();
                    }}
                    className="px-3 py-1.5 text-xs text-indigo-600 hover:bg-indigo-50 rounded flex items-center gap-1 transition-colors"
                    title="为选中的文本创建批注"
                  >
                    <MessageSquare size={14} />
                    <span>批注</span>
                  </button>
                  <div className="w-px h-4 bg-stone-200" />
                  <button
                    onClick={copySelectedText}
                    className="px-3 py-1.5 text-xs text-stone-600 hover:bg-stone-100 rounded flex items-center gap-1 transition-colors"
                    title="复制选中的文本"
                  >
                    <Copy size={14} />
                    <span>复制</span>
                  </button>
                  <div className="w-px h-4 bg-stone-200" />
                  <button
                    onClick={hideSelectionToolbar}
                    className="px-2 py-1 text-xs text-stone-400 hover:text-stone-600"
                  >
                    ✕
                  </button>
                </div>
              )}
              <div 
                ref={editorRef}
                className="w-full max-w-4xl relative"
                onMouseUp={handleTextSelection}
              >
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-lg font-semibold text-stone-800">学习笔记</h2>
                  <button
                    onClick={() => {
                      if (!showCreateForm) {
                        setSelectedText(null);
                      }
                      setShowCreateForm(!showCreateForm);
                    }}
                    className="flex items-center space-x-2 px-4 py-2 bg-green-50 text-green-700 rounded-lg hover:bg-green-100 transition-colors text-sm font-medium border border-green-200"
                  >
                    <Plus size={16} />
                    <span>新建批注</span>
                  </button>
                </div>
                
                <MarkdownEditor
                  initialContent={content}
                  onChange={handleEditMarkdown}
                  onSave={handleSaveMarkdown}
                  readOnly={false}
                />
                
                {/* Annotation Indicators - floating badges */}
                {annotations.map((anno, idx) => {
                  // Calculate line-based positioning to ensure proper scrolling
                  // Each line is approximately 24px high
                  const lines = content.split('\n');
                  const totalLines = lines.length;
                  const targetLineNum = Math.floor((anno.position.y / 100) * totalLines);
                  const lineHeight = 24; // Approximate line height in pixels
                  const topPixels = targetLineNum * lineHeight + 16; // 16px top padding of editor
                  
                  return (
                    <button
                      key={anno.id}
                      onClick={(e) => {
                        setSelectedAnnotation(anno);

                        // 📊 记录批注点击交互
                        recordManualInteraction('click', {
                          action: 'view_annotation',
                          annotationId: anno.id,
                          category: anno.category,
                        });
                        
                        // Get position relative to content container
                        if (contentAreaRef.current) {
                          const buttonRect = e.currentTarget.getBoundingClientRect();
                          
                          // Calculate position relative to content container's parent (the flex container)
                          // This requires getting the flex container rect too
                          const flexContainerRect = contentAreaRef.current.parentElement?.getBoundingClientRect();
                          
                          if (flexContainerRect) {
                            let posX = buttonRect.right - flexContainerRect.left + 15;
                            let posY = buttonRect.top - flexContainerRect.top + contentAreaRef.current.scrollTop;
                            
                            const panelWidth = 350;
                            
                            // Adjust if panel would go off-screen to the right
                            if (posX + panelWidth > flexContainerRect.width) {
                              posX = buttonRect.left - flexContainerRect.left - panelWidth - 15;
                            }
                            
                            // Ensure minimum margins
                            posX = Math.max(15, posX);
                            posY = Math.max(15, posY);
                            
                            // Cap maximum to stay within container
                            posX = Math.min(posX, flexContainerRect.width - panelWidth - 15);
                            
                            setAnnotationPos({ x: posX, y: posY, isAbsolute: true });
                          }
                        }
                      }}
                      className="absolute w-3 h-3 rounded-full hover:scale-150 transition-all shadow-md cursor-pointer"
                      style={{
                        // Line-based pixel positioning relative to editor
                        // This will scroll with content when parent scrolls
                        left: `${anno.position.x}%`,
                        top: `${topPixels}px`,
                        backgroundColor: idx % 3 === 0 ? '#ef4444' : idx % 3 === 1 ? '#f97316' : '#6366f1',
                        zIndex: 10,
                      }}
                      title={`Click to view: ${anno.category || 'annotation'}`}
                    />
                  );
                })}
              </div>
            </div>

            {/* Annotations List Panel - on the right */}
            <div className="absolute right-0 top-0 bottom-0 w-80 bg-white border-l border-stone-200 shadow-lg overflow-y-auto flex flex-col">
              {/* New Annotation Button */}
              <div className="p-4 border-b border-stone-200 flex-shrink-0">
                <button
                  onClick={() => {
                    setSelectedText(null);
                    setNewAnnotationText('');
                    setShowCreateForm(!showCreateForm);
                  }}
                  className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium"
                >
                  <Plus size={16} />
                  <span>新建批注</span>
                </button>
              </div>
              
              {/* Annotations List */}
              <div className="flex-1 overflow-y-auto">
                {annotations.length > 0 ? (
                  <div className="p-4 space-y-3">
                    <h3 className="text-sm font-semibold text-stone-800 pt-2">
                      我的批注 ({annotations.length})
                    </h3>
                    {annotations.map((anno) => (
                      <button
                        key={anno.id}
                        onClick={(e) => {
                          setSelectedAnnotation(anno);
                          const rect = e.currentTarget.getBoundingClientRect();
                          setAnnotationPos({ x: rect.left - 360, y: rect.top });

                          // 📊 记录从列表中点击批注的交互
                          recordManualInteraction('click', {
                            action: 'view_annotation_from_list',
                            annotationId: anno.id,
                            category: anno.category,
                          });
                        }}
                        className="w-full text-left border-l-4 border-indigo-500 pl-3 py-2 bg-indigo-50 rounded hover:bg-indigo-100 transition-colors text-xs"
                      >
                        <p className="font-medium text-stone-800 truncate">{anno.sourceText?.substring(0, 30)}</p>
                        <p className="text-stone-500 text-xs mt-1">{anno.category}</p>
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="text-center text-stone-400 py-8 text-xs px-4">
                    <p className="mb-3">还没有批注</p>
                    <p className="text-xs text-stone-400">选中文本后，点击上方"新建批注"按钮添加</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
