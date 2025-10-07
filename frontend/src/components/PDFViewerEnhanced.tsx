/**
 * Enhanced PDF Viewer with Immersive Reading Mode
 * 支持翻页/滚动模式、快捷键、分块可视化
 */

import { useState, useCallback, useEffect, useRef, useMemo } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import {
    FiChevronLeft,
    FiChevronRight,
    FiZoomIn,
    FiZoomOut,
    FiMaximize2,
    FiMinimize2,
    FiBook,
    FiList,
    FiEye,
    FiEyeOff,
} from 'react-icons/fi';
import { useIsMobile } from '../hooks/useResponsive';
import clsx from 'clsx';

import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';

// Configure PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.js`;

// Reading modes
type ReadingMode = 'page' | 'scroll';

interface BoundingBox {
    page: number;
    x0: number;
    y0: number;
    x1: number;
    y1: number;
}

interface Chunk {
    id: string;
    chunk_index: number;
    start_page: number;
    end_page: number;
    bounding_boxes?: BoundingBox[];
}

interface PDFViewerEnhancedProps {
    fileUrl: string;
    documentId: string;
    chunks?: Chunk[];
    onPageChange?: (page: number, position?: { x: number; y: number }) => void;
    onChunkClick?: (chunkId: string) => void;
}

export default function PDFViewerEnhanced({
    fileUrl,
    documentId,
    chunks = [],
    onPageChange,
    onChunkClick,
}: PDFViewerEnhancedProps) {
    // State
    const [numPages, setNumPages] = useState<number>(0);
    const [pageNumber, setPageNumber] = useState<number>(1);
    const [scale, setScale] = useState<number>(1.0);
    const [readingMode, setReadingMode] = useState<ReadingMode>('page');
    const [isImmersive, setIsImmersive] = useState(false);
    const [showChunks, setShowChunks] = useState(false);
    const [activeChunkId, setActiveChunkId] = useState<string | null>(null);
    const isMobile = useIsMobile();

    const containerRef = useRef<HTMLDivElement>(null);
    const pageRefs = useRef<Map<number, HTMLDivElement>>(new Map());

    // PDF load success
    const onDocumentLoadSuccess = useCallback(
        ({ numPages: nextNumPages }: { numPages: number }) => {
            setNumPages(nextNumPages);
            setPageNumber(1);
        },
        []
    );

    // Navigation
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

    const goToPage = useCallback(
        (page: number) => {
            if (page >= 1 && page <= numPages) {
                setPageNumber(page);
                onPageChange?.(page);

                // Scroll to page in scroll mode
                if (readingMode === 'scroll') {
                    const pageElement = pageRefs.current.get(page);
                    pageElement?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }
        },
        [numPages, readingMode, onPageChange]
    );

    // Zoom
    const zoomIn = useCallback(() => {
        setScale((prev) => Math.min(prev + 0.1, 2.5));
    }, []);

    const zoomOut = useCallback(() => {
        setScale((prev) => Math.max(prev - 0.1, 0.5));
    }, []);

    const fitToWidth = useCallback(() => {
        if (containerRef.current) {
            const containerWidth = containerRef.current.clientWidth;
            // Assuming A4 width ~595pt, adjust scale to fit
            const newScale = (containerWidth - 40) / 595;
            setScale(Math.min(Math.max(newScale, 0.5), 2.5));
        }
    }, []);

    // Toggle modes
    const toggleReadingMode = useCallback(() => {
        setReadingMode((prev) => (prev === 'page' ? 'scroll' : 'page'));
    }, []);

    const toggleImmersive = useCallback(() => {
        setIsImmersive((prev) => {
            const newImmersive = !prev;
            if (newImmersive) {
                document.documentElement.requestFullscreen?.();
            } else {
                document.exitFullscreen?.();
            }
            return newImmersive;
        });
    }, []);

    const toggleChunkVisibility = useCallback(() => {
        setShowChunks((prev) => !prev);
    }, []);

    // Keyboard shortcuts
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            // Prevent when typing in input
            if (['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement).tagName)) {
                return;
            }

            switch (e.key) {
                case 'ArrowRight':
                case 'PageDown':
                    e.preventDefault();
                    goToNextPage();
                    break;
                case 'ArrowLeft':
                case 'PageUp':
                    e.preventDefault();
                    goToPrevPage();
                    break;
                case ' ':
                    e.preventDefault();
                    if (e.shiftKey) {
                        goToPrevPage();
                    } else {
                        goToNextPage();
                    }
                    break;
                case 'Home':
                    e.preventDefault();
                    goToPage(1);
                    break;
                case 'End':
                    e.preventDefault();
                    goToPage(numPages);
                    break;
                case 'F11':
                case 'f':
                    e.preventDefault();
                    toggleImmersive();
                    break;
                case '+':
                case '=':
                    e.preventDefault();
                    zoomIn();
                    break;
                case '-':
                    e.preventDefault();
                    zoomOut();
                    break;
                case '0':
                    e.preventDefault();
                    fitToWidth();
                    break;
                case 'd':
                    if (e.ctrlKey || e.metaKey) {
                        e.preventDefault();
                        toggleChunkVisibility();
                    }
                    break;
                case 'm':
                    e.preventDefault();
                    toggleReadingMode();
                    break;
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [
        pageNumber,
        numPages,
        goToNextPage,
        goToPrevPage,
        goToPage,
        toggleImmersive,
        toggleChunkVisibility,
        toggleReadingMode,
        zoomIn,
        zoomOut,
        fitToWidth,
    ]);

    // Get chunks for current page
    const currentPageChunks = useMemo(() => {
        return chunks.filter(
            (chunk) => chunk.start_page <= pageNumber && chunk.end_page >= pageNumber
        );
    }, [chunks, pageNumber]);

    // Render chunk overlays
    const renderChunkOverlays = useCallback(
        (pageNum: number) => {
            if (!showChunks) return null;

            const pageChunks = chunks.filter(
                (chunk) => chunk.start_page <= pageNum && chunk.end_page >= pageNum
            );

            return pageChunks.map((chunk) => {
                const boxes = chunk.bounding_boxes?.filter((bbox) => bbox.page === pageNum) || [];
                
                return boxes.map((bbox, idx) => (
                    <div
                        key={`${chunk.id}-${idx}`}
                        className={clsx(
                            'absolute border-2 cursor-pointer transition-all',
                            activeChunkId === chunk.id
                                ? 'border-blue-500 bg-blue-500/20'
                                : 'border-yellow-400/50 bg-yellow-400/10 hover:bg-yellow-400/20'
                        )}
                        style={{
                            left: `${(bbox.x0 / 595) * 100}%`,
                            top: `${(bbox.y0 / 842) * 100}%`,
                            width: `${((bbox.x1 - bbox.x0) / 595) * 100}%`,
                            height: `${((bbox.y1 - bbox.y0) / 842) * 100}%`,
                        }}
                        onClick={() => {
                            setActiveChunkId(chunk.id);
                            onChunkClick?.(chunk.id);
                        }}
                        title={`Chunk ${chunk.chunk_index}`}
                    />
                ));
            });
        },
        [chunks, showChunks, activeChunkId, onChunkClick]
    );

    // Render toolbar
    const renderToolbar = () => (
        <div
            className={clsx(
                'flex items-center justify-between p-3 bg-white/90 backdrop-blur-lg border-b border-gray-200 shadow-sm',
                isImmersive && 'absolute top-0 left-0 right-0 z-50 opacity-0 hover:opacity-100 transition-opacity'
            )}
        >
            {/* Left: Navigation */}
            <div className="flex items-center gap-2">
                <button
                    onClick={goToPrevPage}
                    disabled={pageNumber <= 1}
                    className="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    title="上一页 (←/PageUp)"
                >
                    <FiChevronLeft size={20} />
                </button>

                <span className="text-sm font-medium text-gray-700">
                    第 {pageNumber} / {numPages} 页
                </span>

                <button
                    onClick={goToNextPage}
                    disabled={pageNumber >= numPages}
                    className="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    title="下一页 (→/PageDown)"
                >
                    <FiChevronRight size={20} />
                </button>
            </div>

            {/* Center: Mode controls */}
            <div className="flex items-center gap-2">
                <button
                    onClick={toggleReadingMode}
                    className={clsx(
                        'p-2 rounded-lg transition-colors flex items-center gap-2',
                        'hover:bg-gray-100'
                    )}
                    title={`切换到${readingMode === 'page' ? '滚动' : '翻页'}模式 (M)`}
                >
                    {readingMode === 'page' ? <FiBook size={18} /> : <FiList size={18} />}
                    <span className="text-sm">{readingMode === 'page' ? '翻页' : '滚动'}</span>
                </button>

                <button
                    onClick={toggleChunkVisibility}
                    className={clsx(
                        'p-2 rounded-lg transition-colors',
                        showChunks ? 'bg-blue-100 text-blue-600' : 'hover:bg-gray-100'
                    )}
                    title="显示/隐藏分块边界 (Ctrl+D)"
                >
                    {showChunks ? <FiEye size={18} /> : <FiEyeOff size={18} />}
                </button>
            </div>

            {/* Right: Zoom and fullscreen */}
            <div className="flex items-center gap-2">
                <button
                    onClick={zoomOut}
                    className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
                    title="缩小 (-)"
                >
                    <FiZoomOut size={18} />
                </button>

                <span className="text-sm text-gray-600 w-12 text-center">
                    {Math.round(scale * 100)}%
                </span>

                <button
                    onClick={zoomIn}
                    className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
                    title="放大 (+)"
                >
                    <FiZoomIn size={18} />
                </button>

                <button
                    onClick={toggleImmersive}
                    className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
                    title="沉浸式阅读 (F11/F)"
                >
                    {isImmersive ? <FiMinimize2 size={18} /> : <FiMaximize2 size={18} />}
                </button>
            </div>
        </div>
    );

    // Render keyboard shortcuts help
    const renderShortcutsHelp = () => (
        <div className="fixed bottom-4 right-4 bg-black/80 text-white text-xs p-3 rounded-lg opacity-0 hover:opacity-100 transition-opacity z-50">
            <div className="font-bold mb-2">快捷键</div>
            <div className="space-y-1">
                <div>← / → : 上一页/下一页</div>
                <div>Space: 下一页 (Shift+Space: 上一页)</div>
                <div>Home / End: 首页/末页</div>
                <div>+/-: 放大/缩小</div>
                <div>0: 适应宽度</div>
                <div>F / F11: 全屏</div>
                <div>M: 切换阅读模式</div>
                <div>Ctrl+D: 显示分块</div>
            </div>
        </div>
    );

    return (
        <div
            ref={containerRef}
            className={clsx(
                'relative bg-gray-50',
                isImmersive ? 'fixed inset-0 z-50' : 'h-full'
            )}
        >
            {renderToolbar()}

            <div
                className={clsx(
                    'overflow-auto',
                    isImmersive ? 'h-screen' : 'h-[calc(100%-4rem)]'
                )}
            >
                <div className={clsx('mx-auto', readingMode === 'scroll' ? 'py-4' : 'py-8')}>
                    <Document
                        file={fileUrl}
                        onLoadSuccess={onDocumentLoadSuccess}
                        loading={<div className="flex items-center justify-center h-full">加载中...</div>}
                        error={<div className="flex items-center justify-center h-full text-red-500">加载失败</div>}
                    >
                        {readingMode === 'page' ? (
                            // Page mode: single page
                            <div className="relative mx-auto" style={{ width: 'fit-content' }}>
                                <Page
                                    pageNumber={pageNumber}
                                    scale={scale}
                                    renderTextLayer={true}
                                    renderAnnotationLayer={true}
                                    className="shadow-2xl"
                                />
                                <div className="absolute inset-0 pointer-events-none">
                                    {renderChunkOverlays(pageNumber)}
                                </div>
                            </div>
                        ) : (
                            // Scroll mode: all pages
                            Array.from(new Array(numPages), (_, index) => {
                                const pageNum = index + 1;
                                return (
                                    <div
                                        key={pageNum}
                                        ref={(el) => el && pageRefs.current.set(pageNum, el)}
                                        className="relative mx-auto mb-4"
                                        style={{ width: 'fit-content' }}
                                    >
                                        <Page
                                            pageNumber={pageNum}
                                            scale={scale}
                                            renderTextLayer={true}
                                            renderAnnotationLayer={true}
                                            className="shadow-lg"
                                        />
                                        <div className="absolute inset-0 pointer-events-none">
                                            {renderChunkOverlays(pageNum)}
                                        </div>
                                        <div className="text-center text-sm text-gray-500 mt-2">
                                            第 {pageNum} 页
                                        </div>
                                    </div>
                                );
                            })
                        )}
                    </Document>
                </div>
            </div>

            {!isImmersive && renderShortcutsHelp()}
        </div>
    );
}
