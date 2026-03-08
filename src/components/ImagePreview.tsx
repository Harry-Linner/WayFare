/// 图片预览组件
/// 支持 PNG, JPG, GIF, WebP 等图片格式

import { useState } from 'react';
import { ZoomIn, ZoomOut, Download, RotateCw } from 'lucide-react';

interface ImagePreviewProps {
  imagePath: string;
  fileName: string;
  onAnnotationClick?: (x: number, y: number) => void;
}

export function ImagePreview({ imagePath, fileName, onAnnotationClick }: ImagePreviewProps) {
  const [zoom, setZoom] = useState(100);
  const [rotation, setRotation] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const [dragPos, setDragPos] = useState({ x: 0, y: 0 });

  const handleZoomIn = () => {
    setZoom((prev) => Math.min(prev + 10, 200));
  };

  const handleZoomOut = () => {
    setZoom((prev) => Math.max(prev - 10, 50));
  };

  const handleRotate = () => {
    setRotation((prev) => (prev + 90) % 360);
  };

  const handleDownload = () => {
    const link = document.createElement('a');
    link.href = imagePath;
    link.download = fileName;
    link.click();
  };

  const handleImageClick = (e: React.MouseEvent<HTMLImageElement>) => {
    if (onAnnotationClick) {
      const rect = e.currentTarget.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width * 100;
      const y = (e.clientY - rect.top) / rect.height * 100;
      onAnnotationClick(x, y);
    }
  };

  return (
    <div className="h-full flex flex-col bg-stone-100">
      {/* Toolbar */}
      <div className="bg-white border-b border-stone-200 px-4 py-3 flex items-center gap-2 flex-shrink-0">
        <button
          onClick={handleZoomIn}
          className="p-2 rounded hover:bg-stone-100 transition-colors"
          title="放大"
        >
          <ZoomIn size={18} />
        </button>
        <span className="text-sm text-stone-600 w-12 text-center">{zoom}%</span>
        <button
          onClick={handleZoomOut}
          className="p-2 rounded hover:bg-stone-100 transition-colors"
          title="缩小"
        >
          <ZoomOut size={18} />
        </button>

        <div className="w-px h-6 bg-stone-200" />

        <button
          onClick={handleRotate}
          className="p-2 rounded hover:bg-stone-100 transition-colors"
          title="旋转"
        >
          <RotateCw size={18} />
        </button>

        <div className="flex-1" />

        <button
          onClick={handleDownload}
          className="flex items-center gap-2 px-3 py-1.5 rounded text-sm text-stone-600 hover:bg-stone-100 transition-colors"
          title="下载原图"
        >
          <Download size={16} />
          <span>下载</span>
        </button>
      </div>

      {/* Image Container */}
      <div
        className="flex-1 overflow-auto flex items-center justify-center bg-stone-200 relative"
        onMouseDown={() => setIsDragging(true)}
        onMouseUp={() => setIsDragging(false)}
        onMouseMove={(e) => {
          if (isDragging) {
            setDragPos({
              x: dragPos.x + e.movementX,
              y: dragPos.y + e.movementY,
            });
          }
        }}
      >
        <div
          className="flex items-center justify-center"
          style={{
            transform: `translate(${dragPos.x}px, ${dragPos.y}px)`,
          }}
        >
          <img
            src={imagePath}
            alt={fileName}
            onClick={handleImageClick}
            className="cursor-crosshair select-none"
            style={{
              zoom: `${zoom}%`,
              transform: `rotate(${rotation}deg)`,
              transition: 'transform 0.2s',
              maxHeight: '90vh',
              maxWidth: '90vw',
            }}
          />
        </div>
      </div>

      {/* Info Bar */}
      <div className="bg-white border-t border-stone-200 px-4 py-2 text-xs text-stone-500 flex items-center justify-between">
        <span>{fileName}</span>
        <span>点击图片位置可添加批注</span>
      </div>
    </div>
  );
}
