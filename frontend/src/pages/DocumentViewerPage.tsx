/**
 * Document Viewer Page with PDF and AI Chat
 */

import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { FiMessageSquare, FiX } from 'react-icons/fi';
import { apiService } from '../services/api';
import { useIsMobile } from '../hooks/useResponsive';
import PDFViewerEnhanced from '../components/PDFViewerEnhanced';
import ChatPanel from '../components/ChatPanel';
import clsx from 'clsx';

export default function DocumentViewerPage() {
    const { id } = useParams<{ id: string }>();
    const isMobile = useIsMobile();
    const [chatOpen, setChatOpen] = useState(!isMobile);
    const [currentPage, setCurrentPage] = useState(1);

    // 获取文档信息 - 后端直接返回文档对象
    const { data: document, isLoading, error } = useQuery({
        queryKey: ['document', id],
        queryFn: () => apiService.getDocument(id!),
        enabled: !!id,
    });

    // 获取文档分块数据
    const { data: chunksData } = useQuery({
        queryKey: ['document-chunks', id],
        queryFn: () => apiService.getDocumentChunks(id!),
        enabled: !!id,
    });

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="animate-spin w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full" />
            </div>
        );
    }

    if (error || !document) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-center">
                    <p className="text-red-600 mb-2">文档加载失败</p>
                    <p className="text-sm text-gray-600">
                        {(error as Error)?.message || '文档不存在'}
                    </p>
                </div>
            </div>
        );
    }
    const fileUrl = apiService.getDocumentUrl(document.id);

    return (
        <div className="h-full flex flex-col">
            {/* Header */}
            <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between no-print">
                <h1 className="text-lg md:text-xl font-semibold text-gray-900 truncate flex-1">
                    {document.filename}
                </h1>

                {/* Chat toggle button */}
                <button
                    onClick={() => setChatOpen(!chatOpen)}
                    className={clsx(
                        'btn-icon ml-2',
                        chatOpen && 'bg-primary-50 text-primary-600'
                    )}
                    aria-label={chatOpen ? '关闭聊天' : '打开聊天'}
                >
                    {chatOpen && isMobile ? (
                        <FiX className="w-5 h-5" />
                    ) : (
                        <FiMessageSquare className="w-5 h-5" />
                    )}
                </button>
            </div>

            {/* Content: PDF + Chat */}
            <div className="flex-1 flex overflow-hidden">
                {/* PDF Viewer */}
                <div
                    className={clsx(
                        'flex-1 overflow-hidden',
                        isMobile && chatOpen && 'hidden'
                    )}
                >
                    <PDFViewerEnhanced
                        fileUrl={fileUrl}
                        documentId={document.id}
                        chunks={chunksData?.chunks || []}
                        onPageChange={(page) => {
                            setCurrentPage(page);
                            console.log('Current page:', page);
                        }}
                        onChunkClick={(chunkId) => {
                            console.log('Chunk clicked:', chunkId);
                            // TODO: Highlight chunk or show details in chat panel
                        }}
                    />
                </div>

                {/* Chat Panel */}
                {chatOpen && (
                    <div
                        className={clsx(
                            'bg-white border-l border-gray-200 overflow-hidden',
                            isMobile
                                ? 'absolute inset-0 z-20'
                                : 'w-96 flex-shrink-0'
                        )}
                    >
                        <ChatPanel
                            documentId={document.id}
                            onClose={isMobile ? () => setChatOpen(false) : undefined}
                        />
                    </div>
                )}
            </div>

            {/* Mobile: Floating chat button */}
            {isMobile && !chatOpen && (
                <button
                    onClick={() => setChatOpen(true)}
                    className="fixed bottom-6 right-6 w-14 h-14 bg-primary-600 text-white rounded-full shadow-lg flex items-center justify-center hover:bg-primary-700 transition-colors no-print"
                    aria-label="打开聊天"
                >
                    <FiMessageSquare className="w-6 h-6" />
                </button>
            )}
        </div>
    );
}
