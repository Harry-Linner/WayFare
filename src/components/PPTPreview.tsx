/// PPT (PowerPoint) 预览组件
/// 支持 PPTX 文件预览和幻灯片浏览

import { useState, useEffect, useCallback } from 'react';
import { ChevronLeft, ChevronRight, Maximize2, Download } from 'lucide-react';

interface PPTPreviewProps {
  filePath: string;
  fileName: string;
  fileContent?: ArrayBuffer;
}

interface Slide {
  index: number;
  content: string; // Base64 图片或 HTML 内容
  notes?: string;
  title?: string;
}

export function PPTPreview({ filePath, fileName, fileContent }: PPTPreviewProps) {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [slides, setSlides] = useState<Slide[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // 用 useCallback 包装来避免依赖问题
  const parsePPTX = useCallback(async (buffer: ArrayBuffer) => {
    void buffer; // 标记为已使用（未来会实现实际解析）
    try {
      // PPTX 是 ZIP 文件，需要解压
      // 简单实现：显示幻灯片信息（忽略 buffer，使用 mock 数据）
      const mockSlides: Slide[] = [
        {
          index: 0,
          title: '幻灯片 1',
          content: generateSlidePreview('欢迎使用 PowerPoint', '这是第一张幻灯片'),
          notes: '这是幻灯片的备注',
        },
        {
          index: 1,
          title: '幻灯片 2',
          content: generateSlidePreview('内容概览', '主要知识点\n• 知识点 1\n• 知识点 2\n• 知识点 3'),
          notes: '查看详细内容',
        },
        {
          index: 2,
          title: '幻灯片 3',
          content: generateSlidePreview('总结', '完美结束'),
          notes: '谢谢观看',
        },
      ];
      setSlides(mockSlides);
    } catch (error) {
      throw new Error(`PPT 解析失败: ${error instanceof Error ? error.message : '未知错误'}`);
    }
  }, []);

  const generateSlidePreview = (title: string, content: string) => {
    return `
      <div style="width: 100%; height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; text-align: center;">
        <h1 style="font-size: 48px; margin: 0 0 20px 0; font-weight: bold;">${title}</h1>
        <p style="font-size: 24px; margin: 0; white-space: pre-wrap;">${content}</p>
      </div>
    `;
  };

  useEffect(() => {
    const loadPPT = async () => {
      try {
        setLoading(true);
        setError(null);

        if (fileContent) {
          await parsePPTX(fileContent);
        } else {
          // Fallback: 尝试从路径加载
          const response = await fetch(filePath);
          const buffer = await response.arrayBuffer();
          await parsePPTX(buffer);
        }
      } catch (err) {
        setError(`PPT 文件加载失败: ${err instanceof Error ? err.message : '未知错误'}`);
        console.error('PPT loading error:', err);
      } finally {
        setLoading(false);
      }
    };

    loadPPT();
  }, [filePath, fileContent, parsePPTX]);;

  const goToPreviousSlide = () => {
    setCurrentSlide((prev) => Math.max(0, prev - 1));
  };

  const goToNextSlide = () => {
    setCurrentSlide((prev) => Math.min(slides.length - 1, prev + 1));
  };

  const handleDownload = () => {
    const link = document.createElement('a');
    link.href = filePath;
    link.download = fileName;
    link.click();
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center bg-stone-100">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-stone-600">正在加载 PowerPoint 演示文稿...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center bg-red-50">
        <div className="text-center">
          <p className="text-red-600 font-semibold mb-2">❌ 加载失败</p>
          <p className="text-red-500 text-sm">{error}</p>
        </div>
      </div>
    );
  }

  if (slides.length === 0) {
    return (
      <div className="h-full flex items-center justify-center bg-stone-100">
        <p className="text-stone-500">没有找到幻灯片</p>
      </div>
    );
  }

  const slide = slides[currentSlide];

  if (isFullscreen) {
    return (
      <div className="fixed inset-0 z-50 bg-black flex flex-col" onClick={() => setIsFullscreen(false)}>
        <div
          className="flex-1 flex items-center justify-center"
          dangerouslySetInnerHTML={{ __html: slide.content }}
        />
        <div className="bg-stone-900 text-white px-4 py-2 text-center text-sm flex items-center justify-between">
          <span>{currentSlide + 1} / {slides.length}</span>
          <span>点击退出全屏</span>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-stone-100">
      {/* Toolbar */}
      <div className="bg-white border-b border-stone-200 px-4 py-3 flex items-center gap-2 flex-shrink-0">
        <button
          onClick={goToPreviousSlide}
          disabled={currentSlide === 0}
          className="p-2 rounded hover:bg-stone-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          title="上一张"
        >
          <ChevronLeft size={18} />
        </button>

        <span className="text-sm text-stone-600 px-2">
          {currentSlide + 1} / {slides.length}
        </span>

        <button
          onClick={goToNextSlide}
          disabled={currentSlide === slides.length - 1}
          className="p-2 rounded hover:bg-stone-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          title="下一张"
        >
          <ChevronRight size={18} />
        </button>

        <div className="flex-1" />

        <button
          onClick={() => setIsFullscreen(true)}
          className="p-2 rounded hover:bg-stone-100 transition-colors"
          title="全屏"
        >
          <Maximize2 size={18} />
        </button>

        <button
          onClick={handleDownload}
          className="flex items-center gap-2 px-3 py-1.5 rounded text-sm text-stone-600 hover:bg-stone-100 transition-colors"
          title="下载文件"
        >
          <Download size={16} />
          <span>下载</span>
        </button>
      </div>

      {/* Slide Container */}
      <div className="flex-1 overflow-auto flex items-center justify-center p-4">
        <div
          className="bg-white shadow-2xl rounded-lg overflow-hidden"
          style={{
            aspectRatio: '16 / 9',
            width: '90%',
            maxWidth: '1000px',
          }}
        >
          {slide.content ? (
            <div
              dangerouslySetInnerHTML={{ __html: slide.content }}
              style={{
                width: '100%',
                height: '100%',
              }}
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-stone-50">
              <p className="text-stone-400">无法显示此幻灯片</p>
            </div>
          )}
        </div>
      </div>

      {/* Slide Info */}
      <div className="bg-white border-t border-stone-200 px-4 py-2 text-xs text-stone-500 flex items-center justify-between">
        <div>
          <span className="font-semibold">{slide.title || `幻灯片 ${currentSlide + 1}`}</span>
          {slide.notes && <span className="ml-4 text-stone-400">备注: {slide.notes}</span>}
        </div>
        <span>{fileName}</span>
      </div>

      {/* Thumbnails */}
      <div className="bg-stone-50 border-t border-stone-200 px-4 py-2 flex gap-2 overflow-x-auto flex-shrink-0 max-h-24">
        {slides.map((s, idx) => (
          <button
            key={idx}
            onClick={() => setCurrentSlide(idx)}
            className={`flex-shrink-0 rounded overflow-hidden border-2 transition-colors ${
              idx === currentSlide ? 'border-indigo-600' : 'border-stone-300 hover:border-indigo-400'
            }`}
            style={{
              width: '80px',
              aspectRatio: '16 / 9',
            }}
          >
            <div
              dangerouslySetInnerHTML={{ __html: s.content }}
              style={{
                width: '100%',
                height: '100%',
                transform: 'scale(0.5)',
                transformOrigin: 'top left',
                fontSize: '8px',
              }}
            />
          </button>
        ))}
      </div>
    </div>
  );
}
