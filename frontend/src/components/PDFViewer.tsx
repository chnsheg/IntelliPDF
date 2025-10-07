/**
 * Modern PDF Viewer Component with glass morphism and advanced features
 */

import { useState, useCallback, useMemo } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import {
    FiChevronLeft,
    FiChevronRight,
    FiZoomIn,
    FiZoomOut,
    FiMaximize,
    FiMinimize,
    FiDownload,
    FiRotateCw,
    FiBookmark,
    FiMoon,
    FiSun,
    FiGrid,
} from 'react-icons/fi';
import { useIsMobile } from '../hooks/useResponsive';
import clsx from 'clsx';
import { Spinner } from './Loading';

import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';

// Configure PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.js`;

interface PDFViewerProps {
    fileUrl: string;
    documentId: string;
    onPageChange?: (page: number) => void;
}

export default function PDFViewer({
    fileUrl,
    onPageChange,
}: PDFViewerProps) {
    const [numPages, setNumPages] = useState<number>(0);
    const [pageNumber, setPageNumber] = useState<number>(1);
    const [scale, setScale] = useState<number>(1.0);
    const [rotation, setRotation] = useState<number>(0);
    const [isFullscreen, setIsFullscreen] = useState(false);
    const [showThumbnails, setShowThumbnails] = useState(false);
    const [darkMode, setDarkMode] = useState(false);
    const [bookmarks, setBookmarks] = useState<Set<number>>(new Set());
    const isMobile = useIsMobile();

    // PDF load success handler
    const onDocumentLoadSuccess = useCallback(
        ({ numPages: nextNumPages }: { numPages: number }) => {
            setNumPages(nextNumPages);
            setPageNumber(1);
        },
        []
    );

    // Navigation handlers
    const goToPrevPage = useCallback(() => {
        const newPage = Math.max(pageNumber - 1, 1);
        setPageNumber(newPage);
        onPageChange?.(newPage);
    }, [pageNumber, onPageChange]);

    const goToNextPage = useCallback(() => {
        const newPage = Math.min(pageNumber + 1, numPages);
        setPageNumber(newPage);
        onPageChange?.(newPage);
    }, [pageNumber, numPages, onPageChange]);

    const goToPage = useCallback((page: number) => {
        if (page >= 1 && page <= numPages) {
            setPageNumber(page);
            onPageChange?.(page);
        }
    }, [numPages, onPageChange]);

    // Zoom handlers with animation
    const zoomIn = useCallback(() => {
        setScale((prev) => Math.min(prev + 0.2, 3.0));
    }, []);

    const zoomOut = useCallback(() => {
        setScale((prev) => Math.max(prev - 0.2, 0.5));
    }, []);

    const resetZoom = useCallback(() => {
        setScale(1.0);
    }, []);

    // Rotation handler
    const rotate = useCallback(() => {
        setRotation((prev) => (prev + 90) % 360);
    }, []);

    // Fullscreen handler
    const toggleFullscreen = useCallback(() => {
        setIsFullscreen((prev) => !prev);
    }, []);

    // Bookmark handler
    const toggleBookmark = useCallback((page: number) => {
        setBookmarks((prev) => {
            const newBookmarks = new Set(prev);
            if (newBookmarks.has(page)) {
                newBookmarks.delete(page);
            } else {
                newBookmarks.add(page);
            }
            return newBookmarks;
        });
    }, []);

    const isBookmarked = useMemo(() => bookmarks.has(pageNumber), [bookmarks, pageNumber]);

    // Thumbnail pages array
    const thumbnailPages = useMemo(() => {
        return Array.from({ length: numPages }, (_, i) => i + 1);
    }, [numPages]);

    return (
        <div
            className={clsx(
                'flex flex-col transition-all duration-300',
                darkMode ? 'bg-gray-900' : 'bg-gray-100',
                isFullscreen ? 'fixed inset-0 z-50' : 'h-full'
            )}
        >
            {/* Modern Toolbar with Glass Effect */}
            <div className={clsx(
                'backdrop-blur-xl border-b px-4 py-3 no-print',
                'transition-all duration-300',
                darkMode 
                    ? 'bg-gray-800/80 border-gray-700' 
                    : 'bg-white/80 border-gray-200'
            )}>
                <div className="flex items-center justify-between">
                    {/* Left: Navigation */}
                    <div className="flex items-center gap-2">
                        <button
                            onClick={goToPrevPage}
                            disabled={pageNumber <= 1}
                            className={clsx(
                                'p-2 rounded-lg transition-all duration-300',
                                'hover:scale-110 active:scale-95',
                                pageNumber <= 1 
                                    ? 'opacity-40 cursor-not-allowed' 
                                    : darkMode
                                    ? 'hover:bg-gray-700 text-gray-200'
                                    : 'hover:bg-gray-100 text-gray-700'
                            )}
                            aria-label="上一页"
                        >
                            <FiChevronLeft className="w-5 h-5" />
                        </button>

                        <div className="flex items-center gap-2 text-sm">
                            <input
                                type="number"
                                value={pageNumber}
                                onChange={(e) => goToPage(parseInt(e.target.value))}
                                className={clsx(
                                    'w-16 px-2 py-1.5 border rounded-lg text-center',
                                    'transition-all duration-300 focus:ring-2 focus:ring-primary-500',
                                    darkMode
                                        ? 'bg-gray-700 border-gray-600 text-gray-200'
                                        : 'bg-white border-gray-300 text-gray-900'
                                )}
                                min={1}
                                max={numPages}
                            />
                            <span className={darkMode ? 'text-gray-400' : 'text-gray-600'}>
                                / {numPages}
                            </span>
                        </div>

                        <button
                            onClick={goToNextPage}
                            disabled={pageNumber >= numPages}
                            className={clsx(
                                'p-2 rounded-lg transition-all duration-300',
                                'hover:scale-110 active:scale-95',
                                pageNumber >= numPages 
                                    ? 'opacity-40 cursor-not-allowed' 
                                    : darkMode
                                    ? 'hover:bg-gray-700 text-gray-200'
                                    : 'hover:bg-gray-100 text-gray-700'
                            )}
                            aria-label="下一页"
                        >
                            <FiChevronRight className="w-5 h-5" />
                        </button>
                    </div>

                    {/* Center: Zoom & Rotate controls */}
                    <div className="flex items-center gap-2">
                        <button
                            onClick={zoomOut}
                            disabled={scale <= 0.5}
                            className={clsx(
                                'p-2 rounded-lg transition-all duration-300',
                                'hover:scale-110 active:scale-95',
                                scale <= 0.5 
                                    ? 'opacity-40 cursor-not-allowed' 
                                    : darkMode
                                    ? 'hover:bg-gray-700 text-gray-200'
                                    : 'hover:bg-gray-100 text-gray-700'
                            )}
                            aria-label="缩小"
                        >
                            <FiZoomOut className="w-5 h-5" />
                        </button>

                        <button
                            onClick={resetZoom}
                            className={clsx(
                                'px-3 py-1.5 text-sm font-medium rounded-lg',
                                'transition-all duration-300 hover:scale-105',
                                darkMode
                                    ? 'text-gray-300 hover:bg-gray-700'
                                    : 'text-gray-700 hover:bg-gray-100'
                            )}
                        >
                            {Math.round(scale * 100)}%
                        </button>

                        <button
                            onClick={zoomIn}
                            disabled={scale >= 3.0}
                            className={clsx(
                                'p-2 rounded-lg transition-all duration-300',
                                'hover:scale-110 active:scale-95',
                                scale >= 3.0 
                                    ? 'opacity-40 cursor-not-allowed' 
                                    : darkMode
                                    ? 'hover:bg-gray-700 text-gray-200'
                                    : 'hover:bg-gray-100 text-gray-700'
                            )}
                            aria-label="放大"
                        >
                            <FiZoomIn className="w-5 h-5" />
                        </button>

                        <div className={clsx(
                            'w-px h-6 mx-1',
                            darkMode ? 'bg-gray-700' : 'bg-gray-300'
                        )} />

                        <button
                            onClick={rotate}
                            className={clsx(
                                'p-2 rounded-lg transition-all duration-300',
                                'hover:scale-110 hover:rotate-90 active:scale-95',
                                darkMode
                                    ? 'hover:bg-gray-700 text-gray-200'
                                    : 'hover:bg-gray-100 text-gray-700'
                            )}
                            aria-label="旋转"
                        >
                            <FiRotateCw className="w-5 h-5" />
                        </button>
                    </div>

                    {/* Right: Actions */}
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => toggleBookmark(pageNumber)}
                            className={clsx(
                                'p-2 rounded-lg transition-all duration-300',
                                'hover:scale-110 active:scale-95',
                                isBookmarked
                                    ? 'text-yellow-500 bg-yellow-500/10'
                                    : darkMode
                                    ? 'hover:bg-gray-700 text-gray-200'
                                    : 'hover:bg-gray-100 text-gray-700'
                            )}
                            aria-label={isBookmarked ? '取消书签' : '添加书签'}
                        >
                            <FiBookmark className={clsx(
                                'w-5 h-5 transition-all duration-300',
                                isBookmarked && 'fill-current'
                            )} />
                        </button>

                        <button
                            onClick={() => setShowThumbnails(!showThumbnails)}
                            className={clsx(
                                'p-2 rounded-lg transition-all duration-300',
                                'hover:scale-110 active:scale-95',
                                showThumbnails
                                    ? 'bg-primary-500/10 text-primary-600'
                                    : darkMode
                                    ? 'hover:bg-gray-700 text-gray-200'
                                    : 'hover:bg-gray-100 text-gray-700'
                            )}
                            aria-label="缩略图"
                        >
                            <FiGrid className="w-5 h-5" />
                        </button>

                        <button
                            onClick={() => setDarkMode(!darkMode)}
                            className={clsx(
                                'p-2 rounded-lg transition-all duration-300',
                                'hover:scale-110 active:scale-95',
                                darkMode
                                    ? 'hover:bg-gray-700 text-yellow-400'
                                    : 'hover:bg-gray-100 text-gray-700'
                            )}
                            aria-label={darkMode ? '浅色模式' : '深色模式'}
                        >
                            {darkMode ? (
                                <FiSun className="w-5 h-5" />
                            ) : (
                                <FiMoon className="w-5 h-5" />
                            )}
                        </button>

                        <div className={clsx(
                            'w-px h-6 mx-1',
                            darkMode ? 'bg-gray-700' : 'bg-gray-300'
                        )} />

                        <button
                            onClick={toggleFullscreen}
                            className={clsx(
                                'p-2 rounded-lg transition-all duration-300',
                                'hover:scale-110 active:scale-95',
                                darkMode
                                    ? 'hover:bg-gray-700 text-gray-200'
                                    : 'hover:bg-gray-100 text-gray-700'
                            )}
                            aria-label={isFullscreen ? '退出全屏' : '全屏'}
                        >
                            {isFullscreen ? (
                                <FiMinimize className="w-5 h-5" />
                            ) : (
                                <FiMaximize className="w-5 h-5" />
                            )}
                        </button>

                        <a
                            href={fileUrl}
                            download
                            className={clsx(
                                'p-2 rounded-lg transition-all duration-300',
                                'hover:scale-110 active:scale-95',
                                darkMode
                                    ? 'hover:bg-gray-700 text-gray-200'
                                    : 'hover:bg-gray-100 text-gray-700'
                            )}
                            aria-label="下载PDF"
                        >
                            <FiDownload className="w-5 h-5" />
                        </a>
                    </div>
                </div>
            </div>

            <div className="flex flex-1 overflow-hidden">
                {/* Thumbnail Sidebar */}
                {showThumbnails && !isMobile && (
                    <div className={clsx(
                        'w-48 border-r overflow-y-auto',
                        'animate-slideInLeft transition-all duration-300',
                        darkMode
                            ? 'bg-gray-800/50 border-gray-700'
                            : 'bg-white/50 border-gray-200'
                    )}>
                        <div className="p-2 space-y-2">
                            {thumbnailPages.map((page) => (
                                <button
                                    key={page}
                                    onClick={() => goToPage(page)}
                                    className={clsx(
                                        'w-full p-2 rounded-lg transition-all duration-300',
                                        'hover:scale-105 active:scale-95',
                                        'border-2 relative group',
                                        page === pageNumber
                                            ? 'border-primary-500 bg-primary-500/10 shadow-lg'
                                            : darkMode
                                            ? 'border-gray-700 hover:border-gray-600'
                                            : 'border-gray-200 hover:border-gray-300'
                                    )}
                                >
                                    <Document file={fileUrl}>
                                        <Page
                                            pageNumber={page}
                                            width={160}
                                            renderTextLayer={false}
                                            renderAnnotationLayer={false}
                                            className="rounded"
                                        />
                                    </Document>
                                    <div className={clsx(
                                        'absolute bottom-2 right-2 px-2 py-0.5 rounded',
                                        'text-xs font-medium backdrop-blur-sm',
                                        page === pageNumber
                                            ? 'bg-primary-500 text-white'
                                            : darkMode
                                            ? 'bg-gray-800/80 text-gray-200'
                                            : 'bg-white/80 text-gray-700'
                                    )}>
                                        {page}
                                    </div>
                                    {bookmarks.has(page) && (
                                        <div className="absolute top-2 right-2">
                                            <FiBookmark className="w-4 h-4 text-yellow-500 fill-current" />
                                        </div>
                                    )}
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {/* PDF Content with smooth transitions */}
                <div className={clsx(
                    'flex-1 overflow-auto flex items-center justify-center p-4',
                    'transition-all duration-500'
                )}>
                    <Document
                        file={fileUrl}
                        onLoadSuccess={onDocumentLoadSuccess}
                        loading={
                            <div className="flex flex-col items-center justify-center p-8 space-y-4">
                                <Spinner size="lg" />
                                <span className={clsx(
                                    'text-sm font-medium',
                                    darkMode ? 'text-gray-300' : 'text-gray-600'
                                )}>
                                    加载 PDF 文档中...
                                </span>
                            </div>
                        }
                        error={
                            <div className={clsx(
                                'text-center p-8 rounded-xl',
                                darkMode ? 'bg-gray-800' : 'bg-white'
                            )}>
                                <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-100 flex items-center justify-center">
                                    <span className="text-3xl">📄</span>
                                </div>
                                <p className="text-red-600 font-medium mb-2">PDF 加载失败</p>
                                <p className={clsx(
                                    'text-sm',
                                    darkMode ? 'text-gray-400' : 'text-gray-600'
                                )}>
                                    请检查文件是否存在或网络连接
                                </p>
                            </div>
                        }
                    >
                        <div className={clsx(
                            'transition-all duration-300 rounded-xl overflow-hidden',
                            darkMode ? 'shadow-2xl shadow-black/50' : 'shadow-2xl'
                        )}>
                            <Page
                                pageNumber={pageNumber}
                                scale={scale}
                                rotate={rotation}
                                renderTextLayer={true}
                                renderAnnotationLayer={true}
                                loading={
                                    <div className="flex items-center justify-center p-16">
                                        <Spinner size="md" />
                                    </div>
                                }
                                className={clsx(
                                    'transition-transform duration-300',
                                    darkMode && 'brightness-90'
                                )}
                            />
                        </div>
                    </Document>
                </div>
            </div>

            {/* Mobile zoom controls (floating buttons) */}
            {isMobile && (
                <div className="fixed bottom-24 right-4 flex flex-col gap-3 no-print animate-fadeIn">
                    <button
                        onClick={zoomIn}
                        disabled={scale >= 3.0}
                        className={clsx(
                            'w-14 h-14 rounded-full shadow-lg backdrop-blur-xl',
                            'flex items-center justify-center',
                            'transition-all duration-300 hover:scale-110 active:scale-95',
                            scale >= 3.0
                                ? 'opacity-40 cursor-not-allowed'
                                : darkMode
                                ? 'bg-gray-800/80 hover:bg-gray-700/80'
                                : 'bg-white/80 hover:bg-white/90'
                        )}
                        aria-label="放大"
                    >
                        <FiZoomIn className={clsx(
                            'w-6 h-6',
                            darkMode ? 'text-gray-200' : 'text-gray-700'
                        )} />
                    </button>
                    <button
                        onClick={zoomOut}
                        disabled={scale <= 0.5}
                        className={clsx(
                            'w-14 h-14 rounded-full shadow-lg backdrop-blur-xl',
                            'flex items-center justify-center',
                            'transition-all duration-300 hover:scale-110 active:scale-95',
                            scale <= 0.5
                                ? 'opacity-40 cursor-not-allowed'
                                : darkMode
                                ? 'bg-gray-800/80 hover:bg-gray-700/80'
                                : 'bg-white/80 hover:bg-white/90'
                        )}
                        aria-label="缩小"
                    >
                        <FiZoomOut className={clsx(
                            'w-6 h-6',
                            darkMode ? 'text-gray-200' : 'text-gray-700'
                        )} />
                    </button>
                </div>
            )}
        </div>
    );
}
