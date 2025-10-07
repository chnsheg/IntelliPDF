/**
 * Upload Page
 */

import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiUpload, FiFile, FiX } from 'react-icons/fi';
import { useMutation } from '@tanstack/react-query';
import { apiService } from '../services/api';
import { useUploadStore } from '../stores';
import { useIsMobile } from '../hooks/useResponsive';
import clsx from 'clsx';

export default function UploadPage() {
    const navigate = useNavigate();
    const isMobile = useIsMobile();
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [isDragging, setIsDragging] = useState(false);
    const { uploadProgress, setUploadProgress, setUploading, resetUpload } =
        useUploadStore();

    const uploadMutation = useMutation({
        mutationFn: (file: File) =>
            apiService.uploadDocument(file, (progress) => {
                setUploadProgress(progress.percentage);
            }),
        onMutate: () => {
            setUploading(true);
        },
        onSuccess: (response) => {
            resetUpload();
            if (response) {
                navigate(`/document/${response.id}`);
            }
        },
        onError: (error) => {
            console.error('Upload failed:', error);
            resetUpload();
        },
    });

    const handleFileSelect = (file: File) => {
        if (file.type === 'application/pdf') {
            setSelectedFile(file);
        } else {
            alert('请选择 PDF 文件');
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        const file = e.dataTransfer.files[0];
        if (file) handleFileSelect(file);
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

    return (
        <div className="max-w-3xl mx-auto px-4 py-6 md:py-12">
            <div className="text-center mb-8">
                <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">
                    上传 PDF 文档
                </h1>
                <p className="text-gray-600">
                    支持拖拽上传或点击选择文件
                </p>
            </div>

            {/* Upload area */}
            <div
                className={clsx(
                    'card border-2 border-dashed transition-all',
                    isDragging
                        ? 'border-primary-500 bg-primary-50'
                        : 'border-gray-300 hover:border-primary-400',
                    isMobile ? 'p-8' : 'p-12'
                )}
                onDrop={handleDrop}
                onDragOver={(e) => {
                    e.preventDefault();
                    setIsDragging(true);
                }}
                onDragLeave={() => setIsDragging(false)}
            >
                {!selectedFile ? (
                    <div className="text-center">
                        <FiUpload className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                        <p className="text-lg font-medium text-gray-900 mb-2">
                            {isMobile ? '点击上传文件' : '拖拽文件到此处或点击上传'}
                        </p>
                        <p className="text-sm text-gray-600 mb-6">
                            仅支持 PDF 格式，最大 100MB
                        </p>
                        <button
                            onClick={() => fileInputRef.current?.click()}
                            className="btn btn-primary"
                        >
                            选择文件
                        </button>
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept="application/pdf"
                            onChange={handleFileChange}
                            className="hidden"
                        />
                    </div>
                ) : (
                    <div className="space-y-4">
                        {/* Selected file */}
                        <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
                            <FiFile className="w-8 h-8 text-primary-600 flex-shrink-0" />
                            <div className="flex-1 min-w-0">
                                <p className="font-medium text-gray-900 truncate">
                                    {selectedFile.name}
                                </p>
                                <p className="text-sm text-gray-600">
                                    {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                                </p>
                            </div>
                            {!uploadMutation.isPending && (
                                <button
                                    onClick={() => setSelectedFile(null)}
                                    className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
                                >
                                    <FiX className="w-5 h-5 text-gray-600" />
                                </button>
                            )}
                        </div>

                        {/* Upload progress */}
                        {uploadMutation.isPending && (
                            <div>
                                <div className="flex items-center justify-between text-sm text-gray-700 mb-2">
                                    <span>上传中...</span>
                                    <span>{uploadProgress}%</span>
                                </div>
                                <div className="w-full bg-gray-200 rounded-full h-2">
                                    <div
                                        className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                                        style={{ width: `${uploadProgress}%` }}
                                    />
                                </div>
                            </div>
                        )}

                        {/* Actions */}
                        {!uploadMutation.isPending && (
                            <div className="flex gap-3 justify-end">
                                <button
                                    onClick={() => setSelectedFile(null)}
                                    className="btn btn-secondary"
                                >
                                    取消
                                </button>
                                <button onClick={handleUpload} className="btn btn-primary">
                                    开始上传
                                </button>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Tips */}
            <div className="mt-8 p-4 bg-blue-50 rounded-lg">
                <h3 className="font-medium text-blue-900 mb-2">📌 使用提示</h3>
                <ul className="text-sm text-blue-800 space-y-1">
                    <li>• 文档上传后将自动进行智能分块和向量化处理</li>
                    <li>• 处理完成后可以开始 AI 问答和知识图谱分析</li>
                    <li>• 建议上传清晰的文本型 PDF，扫描件效果可能较差</li>
                </ul>
            </div>
        </div>
    );
}
