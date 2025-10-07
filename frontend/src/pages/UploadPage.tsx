/**
 * Modern Upload Page with Enhanced UX
 */

import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FiUpload, FiFile, FiX, FiCheckCircle, FiAlertCircle,
  FiFileText, FiClock, FiZap
} from 'react-icons/fi';
import { useMutation } from '@tanstack/react-query';
import { apiService } from '../services/api';
import { useUploadStore } from '../stores';
import { useToast } from '../components/Toast';
import { ProgressBar } from '../components/Loading';
import clsx from 'clsx';

interface FileWithPreview extends File {
  preview?: string;
}

export default function UploadPage() {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<FileWithPreview | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const { uploadProgress, setUploadProgress, setUploading, resetUpload } = useUploadStore();
  const { showToast } = useToast();

  const uploadMutation = useMutation({
    mutationFn: (file: File) =>
      apiService.uploadDocument(file, (progress) => {
        setUploadProgress(progress.percentage);
      }),
    onMutate: () => {
      setUploading(true);
    },
    onSuccess: () => {
      showToast('success', '文档上传成功！正在处理中...');
      resetUpload();
      // 跳转到文档列表页查看所有文档
      setTimeout(() => {
        navigate('/documents');
      }, 1500);
    },
    onError: (error: any) => {
      showToast('error', error.message || '上传失败，请重试');
      resetUpload();
    },
  });

  const handleFileSelect = (file: File) => {
    if (file.type === 'application/pdf') {
      const fileWithPreview = Object.assign(file, {
        preview: URL.createObjectURL(file),
      });
      setSelectedFile(fileWithPreview);
      showToast('success', '文件已选择，点击上传按钮开始处理');
    } else {
      showToast('error', '请选择 PDF 文件');
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFileSelect(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFileSelect(file);
  };

  const handleUpload = () => {
    if (selectedFile) {
      uploadMutation.mutate(selectedFile);
    }
  };

  const handleRemoveFile = () => {
    if (selectedFile?.preview) {
      URL.revokeObjectURL(selectedFile.preview);
    }
    setSelectedFile(null);
    resetUpload();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-purple-50/30 py-8 px-4">
      <div className="max-w-4xl mx-auto">

        {/* Header */}
        <div className="text-center mb-8 animate-fade-in-up">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-primary-500 to-accent-500 rounded-2xl shadow-lg mb-4">
            <FiUpload className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-2">
            上传 PDF 文档
          </h1>
          <p className="text-gray-600 text-lg">
            智能解析，快速处理，开启知识探索之旅
          </p>
        </div>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8 animate-fade-in-up" style={{ animationDelay: '100ms' }}>
          {[
            { icon: FiZap, title: '快速处理', desc: 'AI 驱动解析' },
            { icon: FiFileText, title: '智能分块', desc: '结构化提取' },
            { icon: FiClock, title: '历史记录', desc: '随时查看' },
          ].map((feature, i) => (
            <div key={i} className="card-glass text-center py-4">
              <feature.icon className="w-8 h-8 text-primary-600 mx-auto mb-2" />
              <h3 className="font-semibold text-gray-900 mb-1">{feature.title}</h3>
              <p className="text-sm text-gray-600">{feature.desc}</p>
            </div>
          ))}
        </div>

        {/* Upload Area */}
        <div className="card-glass p-8 animate-fade-in-up" style={{ animationDelay: '200ms' }}>

          {!selectedFile ? (
            // Drag & Drop Zone
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              className={clsx(
                'relative border-2 border-dashed rounded-2xl p-12 text-center transition-all duration-300 cursor-pointer group',
                isDragging
                  ? 'border-primary-500 bg-primary-50/50 scale-[1.02]'
                  : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
              )}
              onClick={() => fileInputRef.current?.click()}
            >
              {/* Background decoration */}
              <div className="absolute inset-0 bg-gradient-to-br from-primary-500/5 to-accent-500/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity" />

              <div className="relative z-10">
                <div className={clsx(
                  'inline-flex items-center justify-center w-20 h-20 rounded-full mb-6 transition-all duration-300',
                  isDragging
                    ? 'bg-gradient-to-br from-primary-500 to-accent-500 scale-110'
                    : 'bg-gray-100 group-hover:bg-gradient-to-br group-hover:from-primary-500 group-hover:to-accent-500'
                )}>
                  <FiUpload className={clsx(
                    'w-10 h-10 transition-all duration-300',
                    isDragging ? 'text-white animate-bounce-soft' : 'text-gray-400 group-hover:text-white'
                  )} />
                </div>

                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  {isDragging ? '松开以上传文件' : '拖拽文件到此处'}
                </h3>
                <p className="text-gray-600 mb-6">
                  或者点击选择文件
                </p>

                <button
                  type="button"
                  className="inline-flex items-center gap-2 bg-gradient-to-r from-primary-600 to-primary-700 text-white px-6 py-3 rounded-xl font-medium shadow-soft hover:shadow-lg transition-all duration-300 hover:scale-105"
                  onClick={(e) => {
                    e.stopPropagation();
                    fileInputRef.current?.click();
                  }}
                >
                  <FiFile className="w-5 h-5" />
                  选择 PDF 文件
                </button>

                <p className="text-xs text-gray-500 mt-4">
                  支持最大 50MB 的 PDF 文件
                </p>
              </div>

              <input
                ref={fileInputRef}
                type="file"
                accept="application/pdf"
                onChange={handleFileChange}
                className="hidden"
              />
            </div>
          ) : (
            // File Preview
            <div className="space-y-6 animate-fade-in">
              <div className="flex items-start gap-4 p-6 bg-gradient-to-r from-gray-50 to-gray-100 rounded-xl border border-gray-200">
                <div className="flex-shrink-0 w-16 h-16 bg-gradient-to-br from-error-500 to-orange-500 rounded-xl flex items-center justify-center shadow-lg">
                  <FiFileText className="w-8 h-8 text-white" />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div className="flex-1 min-w-0">
                      <h4 className="font-semibold text-gray-900 truncate mb-1">
                        {selectedFile.name}
                      </h4>
                      <p className="text-sm text-gray-600">
                        {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>

                    {!uploadMutation.isPending && (
                      <button
                        onClick={handleRemoveFile}
                        className="p-2 hover:bg-white rounded-lg transition-colors group"
                      >
                        <FiX className="w-5 h-5 text-gray-400 group-hover:text-error-600 transition-colors" />
                      </button>
                    )}
                  </div>

                  {uploadMutation.isPending && (
                    <div className="space-y-2">
                      <ProgressBar
                        progress={uploadProgress}
                        showPercentage
                        variant="primary"
                      />
                      <p className="text-sm text-gray-600">
                        正在上传文档...
                      </p>
                    </div>
                  )}

                  {uploadMutation.isSuccess && (
                    <div className="flex items-center gap-2 text-success-600">
                      <FiCheckCircle className="w-5 h-5" />
                      <span className="text-sm font-medium">上传成功！</span>
                    </div>
                  )}

                  {uploadMutation.isError && (
                    <div className="flex items-center gap-2 text-error-600">
                      <FiAlertCircle className="w-5 h-5" />
                      <span className="text-sm font-medium">上传失败</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Actions */}
              {!uploadMutation.isPending && !uploadMutation.isSuccess && (
                <div className="flex flex-col sm:flex-row gap-3">
                  <button
                    onClick={handleUpload}
                    disabled={uploadMutation.isPending}
                    className="flex-1 flex items-center justify-center gap-2 bg-gradient-to-r from-primary-600 to-primary-700 text-white px-6 py-3 rounded-xl font-semibold shadow-soft hover:shadow-lg transition-all duration-300 hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed group"
                  >
                    <FiUpload className="w-5 h-5 group-hover:animate-bounce-soft" />
                    开始上传
                  </button>
                  <button
                    onClick={handleRemoveFile}
                    className="px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition-colors"
                  >
                    取消
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Tips */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-4 animate-fade-in-up" style={{ animationDelay: '300ms' }}>
          <div className="flex items-start gap-3 p-4 bg-white/50 backdrop-blur-sm rounded-xl border border-gray-200">
            <div className="flex-shrink-0 w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center">
              <FiCheckCircle className="w-4 h-4 text-primary-600" />
            </div>
            <div>
              <h4 className="font-medium text-gray-900 mb-1">文件要求</h4>
              <p className="text-sm text-gray-600">支持 PDF 格式，最大 50MB</p>
            </div>
          </div>

          <div className="flex items-start gap-3 p-4 bg-white/50 backdrop-blur-sm rounded-xl border border-gray-200">
            <div className="flex-shrink-0 w-8 h-8 bg-accent-100 rounded-lg flex items-center justify-center">
              <FiZap className="w-4 h-4 text-accent-600" />
            </div>
            <div>
              <h4 className="font-medium text-gray-900 mb-1">处理速度</h4>
              <p className="text-sm text-gray-600">通常 1-2 分钟完成解析</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
