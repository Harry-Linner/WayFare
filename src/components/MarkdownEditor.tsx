import { useRef, useState } from 'react';
import { SaveIcon, UndoIcon, RedoIcon, HelpCircle } from 'lucide-react';

interface MarkdownEditorProps {
  initialContent?: string;
  onChange?: (content: string) => void;
  onSave?: (content: string) => void;
  readOnly?: boolean;
  className?: string;
}

export function MarkdownEditor({
  initialContent = '# 欢迎使用 WayFare Markdown 编辑器\n\n开始编辑...',
  onChange,
  onSave,
  readOnly = false,
  className = '',
}: MarkdownEditorProps) {
  const editorRef = useRef<HTMLTextAreaElement>(null);
  const [content, setContent] = useState(initialContent);
  const [history, setHistory] = useState<string[]>([initialContent]);
  const [historyIndex, setHistoryIndex] = useState(0);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newContent = e.target.value;
    setContent(newContent);
    
    // Update history
    const newHistory = history.slice(0, historyIndex + 1);
    newHistory.push(newContent);
    setHistory(newHistory);
    setHistoryIndex(newHistory.length - 1);
    
    onChange?.(newContent);
  };

  const handleSave = () => {
    onSave?.(content);
  };

  const handleUndo = () => {
    if (historyIndex > 0) {
      const newIndex = historyIndex - 1;
      setHistoryIndex(newIndex);
      setContent(history[newIndex]);
      onChange?.(history[newIndex]);
    }
  };

  const handleRedo = () => {
    if (historyIndex < history.length - 1) {
      const newIndex = historyIndex + 1;
      setHistoryIndex(newIndex);
      setContent(history[newIndex]);
      onChange?.(history[newIndex]);
    }
  };

  return (
    <div
      className={`flex flex-col h-full bg-stone-50 rounded-lg shadow-lg overflow-hidden ${className}`}
    >
      {/* Toolbar */}
      <div className="flex items-center justify-between bg-stone-200 px-4 py-3 gap-2 flex-shrink-0">
        <div className="flex items-center gap-2">
          <button
            onClick={handleUndo}
            disabled={historyIndex <= 0}
            className="p-2 rounded hover:bg-stone-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title="Undo (Ctrl+Z)"
          >
            <UndoIcon size={20} />
          </button>

          <button
            onClick={handleRedo}
            disabled={historyIndex >= history.length - 1}
            className="p-2 rounded hover:bg-stone-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title="Redo (Ctrl+Y)"
          >
            <RedoIcon size={20} />
          </button>

          <div className="w-px h-6 bg-stone-300"></div>

          <button
            onClick={handleSave}
            className="flex items-center gap-2 px-3 py-2 bg-indigo-500 text-white rounded hover:bg-indigo-600 transition-colors font-medium text-sm"
            title="Save document"
          >
            <SaveIcon size={18} />
            Save
          </button>

          <a
            href="https://commonmark.org/help/"
            target="_blank"
            rel="noopener noreferrer"
            className="p-2 rounded hover:bg-stone-300 transition-colors ml-auto"
            title="Markdown help"
          >
            <HelpCircle size={20} className="text-stone-600" />
          </a>
        </div>
      </div>

      {/* Editor */}
      <div className="flex-1 overflow-hidden p-0">
        <textarea
          ref={editorRef}
          value={content}
          onChange={handleChange}
          disabled={readOnly}
          className={`w-full h-full p-4 font-mono text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500/50 border-0 ${
            readOnly ? 'opacity-75 bg-stone-100' : 'bg-white'
          }`}
          placeholder="输入 Markdown 内容..."
        />
      </div>

      {/* Status bar */}
      <div className="bg-stone-100 px-4 py-2 text-xs text-stone-600 border-t border-stone-300 flex justify-between">
        <div>
          <span className="font-medium">Word count:</span>{' '}
          {content.split(/\s+/).filter(Boolean).length} words
        </div>
        <div>
          <span className="font-medium">Lines:</span>{' '}
          {content.split('\n').length}
        </div>
      </div>
    </div>
  );
}
