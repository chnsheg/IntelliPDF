/**
 * Document Viewer Page with PDF, AI Chat, and Bookmark System
 */

import { useState, useCallback, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { FiMessageSquare, FiX, FiBookmark } from 'react-icons/fi';
import { apiService } from '../services/api';
import { useIsMobile } from '../hooks/useResponsive';
import PDFViewerEnhanced from '../components/PDFViewerEnhanced';
import BookmarkPanel from '../components/BookmarkPanel';
import clsx from 'clsx';

// 动态导入 ChatPanel 以避免 TypeScript 缓存问题
import ChatPanel from '../components/ChatPanel.tsx';

export default function DocumentViewerPage() {
    const { id } = useParams<{ id: string }>();
    const isMobile = useIsMobile();
    const [chatOpen, setChatOpen] = useState(!isMobile);
    const [bookmarkOpen, setBookmarkOpen] = useState(false);
    const [currentPage, setCurrentPage] = useState(1);

    // Text selection state for bookmark creation
    const [selectedText, setSelectedText] = useState<string>('');
    const [selectedTextPosition, setSelectedTextPosition] = useState<{
        x: number;
        y: number;
        width: number;
        height: number;
    } | undefined>(undefined);

    // Bookmark data state (managed through React Query bookmarksData)

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

    // 获取书签数据
    const { data: bookmarksData, refetch: refetchBookmarks } = useQuery({
        queryKey: ['document-bookmarks', id],
        queryFn: async () => {
            if (!id) return [];
            const response = await apiService.getBookmarks({ document_id: id, limit: 100 });
            // 后端返回 { bookmarks: [...], total: number },需要提取 bookmarks 数组
            return response?.bookmarks || [];
        },
        enabled: !!id,
    });

    // 文本选择处理
    const handleTextSelected = useCallback((selection: {
        text: string;
        pageNumber: number;
        position: { x: number; y: number; width: number; height: number };
    }) => {
        setSelectedText(selection.text);
        setSelectedTextPosition(selection.position);
        setCurrentPage(selection.pageNumber);
        // 自动打开聊天面板以便生成书签
        if (!chatOpen) {
            setChatOpen(true);
        }
    }, [chatOpen]);

    // 书签点击处理 - 跳转到书签位置
    const handleBookmarkClick = useCallback((bookmarkId: string) => {
        const bookmark = bookmarksData?.find((b: any) => b.id === bookmarkId);
        if (bookmark) {
            setCurrentPage(bookmark.page_number);
            // 触发全局跳转事件，让 PDFViewerEnhanced 滚动到指定页
            window.dispatchEvent(new CustomEvent('jumpToPage', {
                detail: { page_number: bookmark.page_number }
            }));
        }
    }, [bookmarksData]);

    // 书签创建成功后的回调
    const handleBookmarkCreated = useCallback(async () => {
        // 刷新书签列表
        await refetchBookmarks();
        // 清除选中的文本
        setSelectedText('');
        setSelectedTextPosition(undefined);
    }, [refetchBookmarks]);

    // 书签跳转处理 (从 BookmarkPanel 触发)
    const handleJumpToBookmark = useCallback((page: number, _position: { x: number; y: number }) => {
        setCurrentPage(page);
        // 触发全局跳转事件，让 PDFViewerEnhanced 滚动到指定页
        window.dispatchEvent(new CustomEvent('jumpToPage', {
            detail: { page_number: page }
        }));
    }, []);

    // Listen for aiQuestion events dispatched by PDFViewerEnhanced
    useEffect(() => {
        const handleAIQuestion = (e: Event) => {
            try {
                const ce = e as CustomEvent;
                const detail = ce.detail || {};
                if (detail.documentId && detail.documentId !== document?.id) return;

                const page = Number(detail.page_number) || undefined;
                const selectedText = detail.selected_text || '';
                const position = detail.position || undefined;
                const action = detail.action || 'ask'; // 'set_context' or 'ask'

                // 设置选中文本和位置
                setSelectedText(selectedText);
                setSelectedTextPosition(position);
                setCurrentPage(page || 1);

                // 打开聊天面板
                if (!chatOpen) {
                    setChatOpen(true);
                }

                // 如果action是'set_context'，触发setTopicContext事件
                // 否则转发到ChatPanel自动提问
                if (action === 'set_context') {
                    window.dispatchEvent(new CustomEvent('setTopicContext', {
                        detail: {
                            documentId: document?.id,
                            page_number: page,
                            selected_text: selectedText,
                            position: position,
                            chunk_context: detail.chunk_context // 传递块上下文
                        }
                    }));
                } else {
                    window.dispatchEvent(new CustomEvent('aiQuestionToChat', {
                        detail: {
                            documentId: document?.id,
                            page_number: page,
                            selected_text: selectedText,
                            position: position
                        }
                    }));
                }
            } catch (err) {
                console.warn('Invalid aiQuestion event', err);
            }
        };

        window.addEventListener('aiQuestion', handleAIQuestion as EventListener);
        return () => window.removeEventListener('aiQuestion', handleAIQuestion as EventListener);
    }, [document, chatOpen]);

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

                <div className="flex items-center gap-2">
                    {/* Bookmark toggle button */}
                    <button
                        onClick={() => setBookmarkOpen(!bookmarkOpen)}
                        className={clsx(
                            'btn-icon',
                            bookmarkOpen && 'bg-primary-50 text-primary-600'
                        )}
                        aria-label={bookmarkOpen ? '关闭书签' : '打开书签'}
                    >
                        <FiBookmark className="w-5 h-5" />
                    </button>

                    {/* Chat toggle button */}
                    <button
                        onClick={() => setChatOpen(!chatOpen)}
                        className={clsx(
                            'btn-icon',
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
            </div>

            {/* Content: Bookmark + PDF + Chat */}
            <div className="flex-1 flex overflow-hidden">
                {/* Bookmark Panel */}
                {bookmarkOpen && !isMobile && (
                    <div className="w-80 flex-shrink-0 bg-white border-r border-gray-200 overflow-hidden">
                        <BookmarkPanel
                            documentId={document.id}
                            onJumpTo={handleJumpToBookmark}
                            currentSelection={
                                selectedText && selectedTextPosition
                                    ? {
                                        text: selectedText,
                                        pageNumber: currentPage,
                                        position: selectedTextPosition
                                    }
                                    : undefined
                            }
                        />
                    </div>
                )}

                {/* PDF Viewer */}
                <div
                    className={clsx(
                        'flex-1 overflow-hidden',
                        isMobile && (chatOpen || bookmarkOpen) && 'hidden'
                    )}
                >
                    <PDFViewerEnhanced
                        fileUrl={fileUrl}
                        documentId={document.id}
                        chunks={chunksData?.chunks || []}
                        bookmarks={bookmarksData || []}
                        currentPage={currentPage}
                        onPageChange={(page) => {
                            setCurrentPage(page);
                        }}
                        onChunkClick={(chunkId) => {
                            console.log('Chunk clicked:', chunkId);
                        }}
                        onTextSelected={handleTextSelected}
                        onBookmarkClick={handleBookmarkClick}
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
                            currentPage={currentPage}
                            onClose={isMobile ? () => setChatOpen(false) : undefined}
                            selectedText={selectedText}
                            selectedTextPosition={selectedTextPosition}
                            onBookmarkCreated={handleBookmarkCreated}
                        />
                    </div>
                )}
            </div>

            {/* Mobile: Floating buttons */}
            {isMobile && !chatOpen && !bookmarkOpen && (
                <>
                    <button
                        onClick={() => setBookmarkOpen(true)}
                        className="fixed bottom-24 right-6 w-14 h-14 bg-purple-600 text-white rounded-full shadow-lg flex items-center justify-center hover:bg-purple-700 transition-colors no-print"
                        aria-label="打开书签"
                    >
                        <FiBookmark className="w-6 h-6" />
                    </button>
                    <button
                        onClick={() => setChatOpen(true)}
                        className="fixed bottom-6 right-6 w-14 h-14 bg-primary-600 text-white rounded-full shadow-lg flex items-center justify-center hover:bg-primary-700 transition-colors no-print"
                        aria-label="打开聊天"
                    >
                        <FiMessageSquare className="w-6 h-6" />
                    </button>
                </>
            )}

            {/* Mobile: Bookmark Panel Overlay */}
            {isMobile && bookmarkOpen && (
                <div className="absolute inset-0 z-20 bg-white">
                    <div className="h-full flex flex-col">
                        <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
                            <h2 className="text-lg font-semibold text-gray-900">书签</h2>
                            <button
                                onClick={() => setBookmarkOpen(false)}
                                className="btn-icon"
                                aria-label="关闭书签"
                            >
                                <FiX className="w-5 h-5" />
                            </button>
                        </div>
                        <div className="flex-1 overflow-hidden">
                            <BookmarkPanel
                                documentId={document.id}
                                onJumpTo={(page) => {
                                    handleJumpToBookmark(page, { x: 0, y: 0 });
                                    setBookmarkOpen(false);
                                }}
                                currentSelection={
                                    selectedText && selectedTextPosition
                                        ? {
                                            text: selectedText,
                                            pageNumber: currentPage,
                                            position: selectedTextPosition
                                        }
                                        : undefined
                                }
                            />
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

// Global listener for aiQuestion to integrate with ChatPanel
// We attach inside the component to get access to setters via closure
// but here we export a small helper to be used in useEffect below.
