/// 文件上传和选择组件
/// 支持拖拽上传、文件夹选择、批量文件选择

import { useState, useRef } from 'react';
import { Upload, Folder, File, X, AlertCircle, Check } from 'lucide-react';

interface FileUploadProps {
  onFilesSelected?: (files: File[]) => void;
  onFolderSelected?: (files: File[]) => void;
  supportedFormats?: string[]; // e.g., ['.md', '.pdf', '.txt', '.doc', '.docx']
  maxFileSize?: number; // in MB
}

interface UploadedFile {
  file: File;
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress?: number;
  error?: string;
}

export function FileUpload({
  onFilesSelected,
  onFolderSelected,
  supportedFormats = ['.md', '.pdf', '.txt', '.doc', '.docx', '.ppt', '.pptx', '.png', '.jpg', '.jpeg', '.gif', '.webp'],
  maxFileSize = 100, // MB
}: FileUploadProps) {
  const [isDragActive, setIsDragActive] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);
  const dragRef = useRef<HTMLDivElement>(null);

  const validateFile = (file: File): string | null => {
    // Check file format
    const fileExt = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!supportedFormats.includes(fileExt)) {
      return `不支持的文件格式: ${fileExt}。支持: ${supportedFormats.join(', ')}`;
    }

    // Check file size
    const fileSizeMB = file.size / (1024 * 1024);
    if (fileSizeMB > maxFileSize) {
      return `文件过大: ${fileSizeMB.toFixed(2)}MB，最大支持: ${maxFileSize}MB`;
    }

    return null;
  };

  const handleFiles = (files: FileList | null, isFolder: boolean = false) => {
    if (!files) {
      console.log('❌ handleFiles: 没有文件');
      return;
    }

    console.log('📦 handleFiles 开始处理:', files.length, '个文件，isFolder:', isFolder);
    const fileArray = Array.from(files);
    const validatedFiles: UploadedFile[] = [];

    fileArray.forEach((file) => {
      const error = validateFile(file);
      validatedFiles.push({
        file,
        status: error ? 'error' : 'pending',
        error: error || undefined,
      });
    });

    setUploadedFiles((prev) => [...prev, ...validatedFiles]);

    // Extract valid files
    const validFiles = validatedFiles.filter((uf) => !uf.error).map((uf) => uf.file);

    console.log('✔️ 验证完成，有效文件:', validFiles.length, '个，错误文件:', validatedFiles.filter(uf => uf.error).length, '个');

    if (validFiles.length > 0) {
      if (isFolder) {
        console.log('📢 调用 onFolderSelected 回调');
        onFolderSelected?.(validFiles);
      } else {
        console.log('📢 调用 onFilesSelected 回调');
        onFilesSelected?.(validFiles);
      }
    } else {
      console.log('⚠️ 没有有效的文件要上传');
    }
  };

  // 拖拽处理
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragActive(true);
    } else if (e.type === 'dragleave') {
      setIsDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);

    const files = e.dataTransfer.files;
    handleFiles(files);
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    console.log('📤 文件输入改变事件触发，选择的文件:', e.target.files);
    if (e.target.files) {
      console.log('文件列表长度:', e.target.files.length);
      Array.from(e.target.files).forEach((f, i) => {
        console.log(`  文件 ${i}: ${f.name} (${f.size} bytes)`);
      });
    }
    handleFiles(e.target.files);
  };

  const handleFolderInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    console.log('📁 文件夹输入改变事件触发');
    handleFiles(e.target.files, true);
  };

  const removeFile = (index: number) => {
    setUploadedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const clearAll = () => {
    setUploadedFiles([]);
  };

  const successCount = uploadedFiles.filter((uf) => uf.status === 'success').length;
  const errorCount = uploadedFiles.filter((uf) => uf.error).length;

  return (
    <div className="space-y-4">
      {/* 主上传区域 */}
      <div
        ref={dragRef}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          isDragActive
            ? 'border-indigo-500 bg-indigo-50'
            : 'border-stone-300 bg-stone-50 hover:border-indigo-400'
        }`}
      >
        {/* 拖拽提示 */}
        {isDragActive && (
          <div className="absolute inset-0 flex items-center justify-center bg-indigo-500/10 rounded-lg">
            <div className="text-center">
              <Upload className="w-12 h-12 text-indigo-600 mx-auto mb-2 animate-bounce" />
              <p className="text-lg font-semibold text-indigo-600">释放以上传文件</p>
            </div>
          </div>
        )}

        {!isDragActive && (
          <div>
            <Upload className="w-12 h-12 text-stone-400 mx-auto mb-3" />
            <p className="text-stone-800 font-semibold mb-2">拖拽文件到此，或点击选择</p>
            <p className="text-sm text-stone-500 mb-4">
              支持格式: {supportedFormats.join(', ')} (最大 {maxFileSize}MB)
            </p>

            <div className="flex gap-3 justify-center flex-wrap">
              <button
                onClick={() => {
                  console.log('📄 点击选择文件按钮，ref:', fileInputRef.current);
                  fileInputRef.current?.click();
                }}
                className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors text-sm font-medium"
              >
                <File size={16} />
                选择文件
              </button>

              <button
                onClick={() => {
                  console.log('📂 点击选择文件夹按钮');
                  folderInputRef.current?.click();
                }}
                className="inline-flex items-center gap-2 px-4 py-2 bg-stone-200 text-stone-800 rounded-lg hover:bg-stone-300 transition-colors text-sm font-medium"
              >
                <Folder size={16} />
                选择文件夹
              </button>
            </div>

            {/* 隐藏的文件输入 */}
            <input
              ref={fileInputRef}
              type="file"
              multiple
              hidden
              accept={supportedFormats.join(',')}
              onChange={handleFileInputChange}
            />

            <input
              ref={folderInputRef}
              type="file"
              multiple
              hidden
              // @ts-expect-error - webkitdirectory 用于选择文件夹
              webkitdirectory="true"
              mozdirectory="true"
              onChange={handleFolderInputChange}
            />
          </div>
        )}
      </div>

      {/* 上传文件列表 */}
      {uploadedFiles.length > 0 && (
        <div className="bg-white rounded-lg border border-stone-200 overflow-hidden">
          {/* 标题栏 */}
          <div className="bg-stone-50 px-4 py-3 border-b border-stone-200 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <h3 className="font-semibold text-stone-800">上传列表</h3>
              <span className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded">
                {uploadedFiles.length} 个文件
              </span>
              {successCount > 0 && (
                <span className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded flex items-center gap-1">
                  <Check size={14} /> {successCount} 成功
                </span>
              )}
              {errorCount > 0 && (
                <span className="text-xs px-2 py-1 bg-red-100 text-red-700 rounded flex items-center gap-1">
                  <AlertCircle size={14} /> {errorCount} 错误
                </span>
              )}
            </div>
            <button
              onClick={clearAll}
              className="text-xs text-stone-600 hover:text-red-600 transition-colors"
            >
              清空列表
            </button>
          </div>

          {/* 文件列表 */}
          <div className="max-h-96 overflow-y-auto">
            {uploadedFiles.map((uf, idx) => (
              <div
                key={idx}
                className="px-4 py-3 border-b border-stone-100 last:border-b-0 flex items-center justify-between hover:bg-stone-50 transition-colors group"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <File size={16} className="text-stone-400 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-stone-800 truncate">
                        {uf.file.name}
                      </p>
                      <p className="text-xs text-stone-500">
                        {(uf.file.size / 1024).toFixed(2)} KB
                      </p>
                    </div>
                  </div>

                  {/* 错误信息 */}
                  {uf.error && (
                    <div className="mt-1 ml-6 text-xs text-red-600 flex items-center gap-1">
                      <AlertCircle size={12} />
                      {uf.error}
                    </div>
                  )}

                  {/* 进度条 */}
                  {uf.status === 'uploading' && (
                    <div className="mt-2 ml-6 h-1 bg-stone-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-indigo-600 transition-all duration-300"
                        style={{ width: `${uf.progress || 0}%` }}
                      />
                    </div>
                  )}
                </div>

                {/* 状态指示 */}
                <div className="ml-4 flex items-center gap-2 flex-shrink-0">
                  {uf.status === 'success' && (
                    <div className="flex items-center gap-1 text-xs text-green-600">
                      <Check size={16} className="text-green-600" />
                    </div>
                  )}
                  {uf.status === 'error' && (
                    <div className="flex items-center gap-1 text-xs text-red-600">
                      <AlertCircle size={16} className="text-red-600" />
                    </div>
                  )}
                  {uf.status === 'uploading' && (
                    <div className="w-4 h-4 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
                  )}

                  <button
                    onClick={() => removeFile(idx)}
                    className="p-1 text-stone-400 hover:text-red-600 transition-colors opacity-0 group-hover:opacity-100"
                  >
                    <X size={16} />
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* 底部操作 */}
          {successCount > 0 && (
            <div className="bg-green-50 px-4 py-2 border-t border-green-200 text-xs text-green-700 flex items-center gap-2">
              <Check size={14} className="text-green-600" />
              <span>{successCount} 个文件已准备就绪，可以开始学习了！</span>
            </div>
          )}
        </div>
      )}

      {/* 快速链接 */}
      <div className="text-xs text-stone-500 text-center">
        <p>💡 提示: 你可以选择整个文件夹来批量导入学习资料</p>
      </div>
    </div>
  );
}
