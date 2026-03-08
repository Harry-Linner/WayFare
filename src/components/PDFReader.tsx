import { useEffect, useRef, useState } from 'react';
import * as pdfjsLib from 'pdfjs-dist';
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut, RotateCw } from 'lucide-react';

// Set up the worker
pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;

interface PDFReaderProps {
  filePath: string;
  onPageChange?: (pageNumber: number, totalPages: number) => void;
  onResourceLoad?: (pageNumber: number) => void;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type PDFDocumentType = any;

export function PDFReader({ filePath, onPageChange, onResourceLoad }: PDFReaderProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [pdf, setPdf] = useState<PDFDocumentType | null>(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [zoom, setZoom] = useState(1);
  const [rotation, setRotation] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  // Load PDF document
  useEffect(() => {
    const loadPDF = async () => {
      try {
        setLoading(true);
        setError(null);

        // Only accept valid PDF URLs
        if (!filePath || !filePath.includes('.pdf')) {
          setError('Invalid PDF file path');
          return;
        }

        const pdfUrl = filePath.startsWith('http')
          ? filePath
          : `file://${filePath}`;

        const loadingTask = pdfjsLib.getDocument({
          url: pdfUrl,
          withCredentials: false,
        });

        const pdf = await loadingTask.promise;
        setPdf(pdf);
        setTotalPages(pdf.numPages);
        setPageNumber(1);
        setRetryCount(0);
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Failed to load PDF';
        setError(`PDF loading failed: ${errorMsg}`);
        console.error('PDF loading error:', err);
      } finally {
        setLoading(false);
      }
    };

    loadPDF();
  }, [filePath, retryCount]);

  // Render current page
  useEffect(() => {
    if (!pdf || !canvasRef.current || pageNumber < 1 || pageNumber > totalPages) return;

    const renderPage = async () => {
      try {
        setLoading(true);
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const page: any = await pdf!.getPage(pageNumber);

        // Calculate viewport with zoom and rotation
        let viewport = page.getViewport({ scale: zoom * 1.5, rotation });

        // Apply container width constraints
        const container = canvasRef.current?.parentElement;
        if (container) {
          const maxWidth = container.clientWidth - 32; // Padding
          if (viewport.width > maxWidth) {
            const scaleFactor = maxWidth / viewport.width;
            viewport = page.getViewport({
              scale: zoom * 1.5 * scaleFactor,
              rotation,
            });
          }
        }

        const canvas = canvasRef.current;
        if (!canvas) return;

        canvas.width = viewport.width;
        canvas.height = viewport.height;

        const renderContext = {
          canvasContext: canvas.getContext('2d')!,
          viewport: viewport,
        };

        await page.render(renderContext).promise;
        onResourceLoad?.(pageNumber);
      } catch (err) {
        console.error('Page rendering error:', err);
      } finally {
        setLoading(false);
      }
    };

    renderPage();
  }, [pdf, pageNumber, zoom, rotation, totalPages, onResourceLoad]);

  // Notify parent of page changes
  useEffect(() => {
    onPageChange?.(pageNumber, totalPages);
  }, [pageNumber, totalPages, onPageChange]);

  const handlePrevPage = () => {
    if (pageNumber > 1) {
      setPageNumber(pageNumber - 1);
    }
  };

  const handleNextPage = () => {
    if (pageNumber < totalPages) {
      setPageNumber(pageNumber + 1);
    }
  };

  const handleZoomIn = () => setZoom((z) => Math.min(z + 0.2, 3));
  const handleZoomOut = () => setZoom((z) => Math.max(z - 0.2, 0.5));
  const handleRotate = () => setRotation((r) => (r + 90) % 360);

  if (error) {
    return (
      <div className="flex-1 flex flex-col h-full w-full bg-stone-50 overflow-auto items-center justify-center p-8">
        <div className="max-w-md text-center bg-white rounded-lg shadow-sm p-8">
          <div className="text-6xl mb-4">📄</div>
          <h3 className="text-lg font-semibold text-stone-800 mb-2">PDF Load Failed</h3>
          <p className="text-stone-600 mb-4 text-sm break-words">{error}</p>
          <button
            onClick={() => setRetryCount(retryCount + 1)}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors text-sm font-medium"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-stone-50 rounded-lg shadow-lg overflow-hidden" data-content-area>
      {/* Toolbar */}
      <div className="flex items-center justify-between bg-stone-200 px-4 py-3 gap-2 flex-shrink-0">
        <div className="flex items-center gap-2">
          <button
            onClick={handlePrevPage}
            disabled={pageNumber <= 1 || loading}
            className="p-2 rounded hover:bg-stone-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title="Previous page"
          >
            <ChevronLeft size={20} />
          </button>

          <span className="px-3 py-1 bg-stone-100 rounded text-sm font-medium">
            {pageNumber} / {totalPages}
          </span>

          <button
            onClick={handleNextPage}
            disabled={pageNumber >= totalPages || loading}
            className="p-2 rounded hover:bg-stone-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title="Next page"
          >
            <ChevronRight size={20} />
          </button>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleZoomOut}
            disabled={zoom <= 0.5 || loading}
            className="p-2 rounded hover:bg-stone-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title="Zoom out"
          >
            <ZoomOut size={20} />
          </button>

          <span className="px-3 py-1 bg-stone-100 rounded text-sm font-medium w-12 text-center">
            {Math.round(zoom * 100)}%
          </span>

          <button
            onClick={handleZoomIn}
            disabled={zoom >= 3 || loading}
            className="p-2 rounded hover:bg-stone-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title="Zoom in"
          >
            <ZoomIn size={20} />
          </button>

          <div className="w-px h-6 bg-stone-300"></div>

          <button
            onClick={handleRotate}
            disabled={loading}
            className="p-2 rounded hover:bg-stone-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title="Rotate"
          >
            <RotateCw size={20} />
          </button>
        </div>
      </div>

      {/* Canvas container */}
      <div className="flex-1 overflow-auto flex items-center justify-center bg-white p-4">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/10 backdrop-blur-sm">
            <div className="bg-white rounded-lg p-6 shadow-xl">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto mb-2"></div>
              <p className="text-stone-700 text-sm font-medium">Rendering page...</p>
            </div>
          </div>
        )}

        <div className="bg-white rounded-lg shadow-2xl overflow-hidden">
          <canvas
            ref={canvasRef}
            className="block max-w-full h-auto"
          />
        </div>
      </div>
    </div>
  );
}
