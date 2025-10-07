/**
 * Enhanced Document Detail Page with tabs for PDF, Chunks, and Chat
 */

import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
    FiFileText,
    FiGrid,
    FiMessageSquare,
    FiDownload,
    FiArrowLeft,
    FiClock,
    FiCheckCircle,
    FiAlertCircle,
} from 'react-icons/fi';
import clsx from 'clsx';
import { apiService } from '../services/api';
import { Spinner } from '../components/Loading';
import PDFViewer from '../components/PDFViewer';
import ChatPanel from '../components/ChatPanel';


type TabType = 'pdf' | 'chunks' | 'chat';

export default function DocumentDetailPage() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState<TabType>('pdf');

    // Fetch document
    const { data: document, isLoading: docLoading } = useQuery({
        queryKey: ['document', id],
        queryFn: () => apiService.getDocument(id!),
        enabled: !!id,
    });

    // Fetch chunks
    const { data: chunksData, isLoading: chunksLoading } = useQuery({
        queryKey: ['document-chunks', id],
        queryFn: () => apiService.getDocumentChunks(id!),
        enabled: !!id && activeTab === 'chunks',
    });

    if (docLoading) {
        return (
            <div className="flex flex-col items-center justify-center h-screen">
                <Spinner size="lg" />
                <p className="mt-4 text-gray-600">加载文档...</p>
            </div>
        );
    }

    if (!document) {
        return (
            <div className="flex flex-col items-center justify-center h-screen">
                <FiAlertCircle className="w-16 h-16 text-red-500 mb-4" />
                <h2 className="text-2xl font-bold text-gray-900 mb-2">文档不存在</h2>
                <p className="text-gray-600 mb-6">无法找到该文档</p>
                <button
                    onClick={() => navigate('/documents')}
                    className="btn-primary"
                >
                    返回文档列表
                </button>
            </div>
        );
    }

    const getStatusBadge = (status: string) => {
        const configs = {
            completed: { icon: FiCheckCircle, text: '已完成', className: 'bg-green-100 text-green-800' },
            processing: { icon: FiClock, text: '处理中', className: 'bg-yellow-100 text-yellow-800' },
            pending: { icon: FiClock, text: '待处理', className: 'bg-gray-100 text-gray-800' },
            failed: { icon: FiAlertCircle, text: '失败', className: 'bg-red-100 text-red-800' },
        };
        const config = configs[status as keyof typeof configs] || configs.pending;
        const Icon = config.icon;

        return (
            <span className={clsx('inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium', config.className)}>
                <Icon className="w-4 h-4" />
                {config.text}
            </span>
        );
    };

    const fileUrl = apiService.getDocumentUrl(document.id);

    return (
        <div className="h-screen flex flex-col bg-gray-50">
            {/* Header */}
            <div className="bg-white border-b border-gray-200 px-6 py-4">
                <div className="flex items-center gap-4 mb-4">
                    <button
                        onClick={() => navigate('/documents')}
                        className="btn-icon"
                        title="返回"
                    >
                        <FiArrowLeft className="w-5 h-5" />
                    </button>
                    <div className="flex-1">
                        <h1 className="text-2xl font-bold text-gray-900 mb-1">
                            {document.filename}
                        </h1>
                        <div className="flex items-center gap-4 text-sm text-gray-600">
                            <span>{(document.file_size / 1024 / 1024).toFixed(2)} MB</span>
                            <span>•</span>
                            <span>{document.chunk_count} 个块</span>
                            <span>•</span>
                            {getStatusBadge(document.status)}
                        </div>
                    </div>
                    <a
                        href={fileUrl}
                        download={document.filename}
                        className="btn-secondary flex items-center gap-2"
                    >
                        <FiDownload className="w-4 h-4" />
                        下载 PDF
                    </a>
                </div>

                {/* Tabs */}
                <div className="flex gap-1">
                    {[
                        { key: 'pdf', label: 'PDF 预览', icon: FiFileText },
                        { key: 'chunks', label: `文档块 (${document.chunk_count})`, icon: FiGrid },
                        { key: 'chat', label: '智能对话', icon: FiMessageSquare },
                    ].map(tab => {
                        const Icon = tab.icon;
                        return (
                            <button
                                key={tab.key}
                                onClick={() => setActiveTab(tab.key as TabType)}
                                className={clsx(
                                    'flex items-center gap-2 px-4 py-2 rounded-t-lg font-medium transition-colors',
                                    activeTab === tab.key
                                        ? 'bg-primary-50 text-primary-700 border-b-2 border-primary-600'
                                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                                )}
                            >
                                <Icon className="w-4 h-4" />
                                {tab.label}
                            </button>
                        );
                    })}
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-hidden">
                {activeTab === 'pdf' && (
                    <div className="h-full bg-gray-100">
                        <PDFViewer fileUrl={fileUrl} documentId={document.id} />
                    </div>
                )}

                {activeTab === 'chunks' && (
                    <div className="h-full overflow-y-auto p-6">
                        {chunksLoading ? (
                            <div className="flex flex-col items-center justify-center py-12">
                                <Spinner size="lg" />
                                <p className="mt-4 text-gray-600">加载文档块...</p>
                            </div>
                        ) : chunksData && chunksData.items.length > 0 ? (
                            <div className="max-w-4xl mx-auto space-y-4">
                                <div className="text-sm text-gray-600 mb-4">
                                    共 {chunksData.total} 个文档块
                                </div>
                                {chunksData.items.map((chunk: any) => (
                                    <div
                                        key={chunk.id}
                                        className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow"
                                    >
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="text-sm font-medium text-gray-700">
                                                块 {chunk.chunk_index + 1}
                                            </span>
                                            <span className="text-xs text-gray-500">
                                                第 {chunk.start_page} 页
                                                {chunk.end_page !== chunk.start_page && ` - ${chunk.end_page} 页`}
                                            </span>
                                        </div>
                                        <p className="text-gray-800 text-sm leading-relaxed whitespace-pre-wrap">
                                            {chunk.content.substring(0, 500)}
                                            {chunk.content.length > 500 && '...'}
                                        </p>
                                        <div className="mt-2 flex items-center gap-3 text-xs text-gray-500">
                                            <span>{chunk.token_count} tokens</span>
                                            <span>•</span>
                                            <span>{chunk.chunk_type}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-center py-12">
                                <FiGrid className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                                <p className="text-gray-600">暂无文档块</p>
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'chat' && (
                    <div className="h-full">
                        <ChatPanel documentId={document.id} />
                    </div>
                )}
            </div>
        </div>
    );
}
