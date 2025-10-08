/**
 * Enhanced PDF Viewer with Immersive Reading Mode
 * 支持翻页/滚动模式、快捷键、分块可视化
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { apiService } from '../services/api';
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

interface BookmarkType {
    id: string;
    page_number: number;
    position: { x: number; y: number; width: number; height: number };
    title?: string;
    ai_summary: string;
    color?: string;
}

interface PDFViewerEnhancedProps {
    fileUrl: string;
    documentId: string;
    chunks?: Chunk[];
    bookmarks?: BookmarkType[];
    currentPage?: number;  // External page control
    onPageChange?: (page: number, position?: { x: number; y: number }) => void;
    onChunkClick?: (chunkId: string) => void;
    onTextSelected?: (selection: {
        text: string;
        pageNumber: number;
        position: { x: number; y: number; width: number; height: number };
    }) => void;
    onBookmarkClick?: (bookmarkId: string) => void;
}

export default function PDFViewerEnhanced({
    fileUrl,
    documentId,
    chunks = [],
    bookmarks = [],
    currentPage: externalCurrentPage,
    onPageChange,
    onChunkClick,
    onTextSelected,
    onBookmarkClick,
}: PDFViewerEnhancedProps) {
    // State
    const [numPages, setNumPages] = useState<number>(0);
    const [pageNumber, setPageNumber] = useState<number>(1);
    const [scale, setScale] = useState<number>(1.0);
    const [readingMode, setReadingMode] = useState<ReadingMode>('page');
    const [isImmersive, setIsImmersive] = useState(false);
    const [showChunks, setShowChunks] = useState(false);
    const [showBookmarks, setShowBookmarks] = useState(true); // Show bookmarks by default
    const [activeChunkId, setActiveChunkId] = useState<string | null>(null);
    const [hoveredBookmarkId, setHoveredBookmarkId] = useState<string | null>(null);

    const containerRef = useRef<HTMLDivElement>(null);
    const pageRefs = useRef<Map<number, HTMLDivElement>>(new Map());
    // PDF document and pages references for coordinate conversion
    const pdfDocumentRef = useRef<any>(null);  // PDFDocumentProxy
    const pdfPagesCache = useRef<Map<number, any>>(new Map());  // PDFPageProxy cache
    
    // Annotations state (in-memory). For persistence, we can extend to call backend.
    const [annotations, setAnnotations] = useState<Array<{
        id: string;
        page: number;
        x: number;
        y: number;
        width: number;
        height: number;
        style: 'highlight' | 'underline' | 'strike' | 'tag';
        tagId?: string;
        text: string;
    }>>([]);

    // Load persisted annotations for this document
    useEffect(() => {
        let mounted = true;
        const load = async () => {
            if (!documentId) return;
            try {
                const resp = await apiService.getAnnotationsForDocument(documentId);
                if (!mounted) return;
                // resp.annotations expected
                const items = (resp.annotations || []).map((a: any) => ({
                    id: a.id,
                    page: a.page_number || a.page || 1,
                    x: a.position?.x ?? 0,
                    y: a.position?.y ?? 0,
                    width: a.position?.width ?? 0,
                    height: a.position?.height ?? 0,
                    style: (a.annotation_type || 'highlight') as any,
                    text: a.content || '',
                }));
                setAnnotations(items);
            } catch (e) {
                console.warn('Failed to load annotations', e);
            }
        };
        load();
        return () => { mounted = false; };
    }, [documentId]);

    // Selection toolbar state
    const [selectionInfo, setSelectionInfo] = useState<{
        visible: boolean;
        pageNumber: number | null;
        x: number;  // PDF coordinates
        y: number;
        width: number;
        height: number;
        text: string;
        toolbarX?: number;  // Screen coordinates for toolbar positioning
        toolbarY?: number;
    }>({ visible: false, pageNumber: null, x: 0, y: 0, width: 0, height: 0, text: '' });

    // PDF load success
    const onDocumentLoadSuccess = useCallback(
        (pdf: any) => {  // pdf is PDFDocumentProxy
            setNumPages(pdf.numPages);
            setPageNumber(1);
            // Save document reference for coordinate conversion
            pdfDocumentRef.current = pdf;
            // Clear pages cache
            pdfPagesCache.current.clear();
        },
        []
    );

    // Get or load PDF page for coordinate conversion
    const getPDFPage = useCallback(async (pageNum: number) => {
        // Check cache first
        if (pdfPagesCache.current.has(pageNum)) {
            return pdfPagesCache.current.get(pageNum);
        }
        
        // Load page if not cached
        if (pdfDocumentRef.current) {
            try {
                const page = await pdfDocumentRef.current.getPage(pageNum);
                pdfPagesCache.current.set(pageNum, page);
                return page;
            } catch (error) {
                console.error(`Failed to load PDF page ${pageNum}:`, error);
                return null;
            }
        }
        return null;
    }, []);

    // Convert screen coordinates to PDF coordinates
    const convertScreenToPDF = useCallback(async (
        rect: DOMRect,
        pageElement: HTMLElement,
        pageNum: number
    ): Promise<{ x: number; y: number; width: number; height: number } | null> => {
        const pdfPage = await getPDFPage(pageNum);
        if (!pdfPage) {
            console.warn('PDF page not available for coordinate conversion');
            return null;
        }

        const viewport = pdfPage.getViewport({ scale });
        const pageRect = pageElement.getBoundingClientRect();

        // Calculate relative position to page element
        const relX = rect.left - pageRect.left;
        const relY = rect.top - pageRect.top;
        const relX2 = rect.right - pageRect.left;
        const relY2 = rect.bottom - pageRect.top;

        // Convert to PDF coordinates using viewport
        const [pdfX, pdfY] = viewport.convertToPdfPoint(relX, relY);
        const [pdfX2, pdfY2] = viewport.convertToPdfPoint(relX2, relY2);

        return {
            x: Math.min(pdfX, pdfX2),
            y: Math.min(pdfY, pdfY2),
            width: Math.abs(pdfX2 - pdfX),
            height: Math.abs(pdfY2 - pdfY),
        };
    }, [scale, getPDFPage]);

    // Convert PDF coordinates to screen coordinates for rendering
    const convertPDFToScreen = useCallback(async (
        pdfCoords: { x: number; y: number; width: number; height: number },
        pageNum: number
    ): Promise<{ left: number; top: number; width: number; height: number } | null> => {
        const pdfPage = await getPDFPage(pageNum);
        if (!pdfPage) {
            console.warn('PDF page not available for coordinate conversion');
            return null;
        }

        const viewport = pdfPage.getViewport({ scale });

        // Convert PDF coordinates to viewport coordinates
        const [x1, y1] = viewport.convertToViewportPoint(pdfCoords.x, pdfCoords.y);
        const [x2, y2] = viewport.convertToViewportPoint(
            pdfCoords.x + pdfCoords.width,
            pdfCoords.y + pdfCoords.height
        );

        return {
            left: Math.min(x1, x2),
            top: Math.min(y1, y2),
            width: Math.abs(x2 - x1),
            height: Math.abs(y2 - y1),
        };
    }, [scale, getPDFPage]);

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

    // Listen for external page changes (e.g., from bookmark jumps)
    useEffect(() => {
        if (externalCurrentPage && externalCurrentPage !== pageNumber && numPages > 0) {
            goToPage(externalCurrentPage);
        }
    }, [externalCurrentPage, pageNumber, numPages, goToPage]);

    // Listen for global jump events dispatched by ChatPanel or other components
    useEffect(() => {
        const handleJumpToPage = (e: Event) => {
            try {
                // CustomEvent with detail { page_number }
                const ce = e as CustomEvent;
                const page = Number(ce.detail?.page_number);
                if (Number.isFinite(page)) {
                    goToPage(page);
                }
            } catch (err) {
                console.warn('Invalid jumpToPage event', err);
            }
        };

        const handleJumpToChunk = (e: Event) => {
            try {
                const ce = e as CustomEvent;
                const chunkId = ce.detail?.chunk_id;
                if (chunkId) {
                    // If chunks metadata available, try to find chunk and jump to its start_page
                    const found = chunks.find(c => c.id === chunkId);
                    if (found) {
                        goToPage(found.start_page || 1);
                        setActiveChunkId(found.id);
                        onChunkClick?.(found.id);
                    }
                }
            } catch (err) {
                console.warn('Invalid jumpToChunk event', err);
            }
        };

        window.addEventListener('jumpToPage', handleJumpToPage as EventListener);
        window.addEventListener('jumpToChunk', handleJumpToChunk as EventListener);
        return () => {
            window.removeEventListener('jumpToPage', handleJumpToPage as EventListener);
            window.removeEventListener('jumpToChunk', handleJumpToChunk as EventListener);
        };
    }, [chunks, goToPage, onChunkClick]);

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

    // Handle text selection
    useEffect(() => {
        if (!onTextSelected) return;

        const handleSelection = async () => {
            const selection = window.getSelection();
            if (!selection || selection.isCollapsed) return;

            const selectedText = selection.toString().trim();
            if (selectedText.length < 3) return; // Ignore very short selections

            // Get selection rect
            const range = selection.getRangeAt(0);
            const rect = range.getBoundingClientRect();

            // Get page element for coordinate conversion
            const pageElement = pageRefs.current.get(pageNumber);
            
            // Try to convert to PDF coordinates
            let pdfCoords = null;
            if (pageElement) {
                pdfCoords = await convertScreenToPDF(rect, pageElement, pageNumber);
            }
            
            // Fallback to relative coordinates if PDF conversion fails
            const position = pdfCoords || {
                x: rect.left - (containerRef.current?.getBoundingClientRect().left || 0),
                y: rect.top - (containerRef.current?.getBoundingClientRect().top || 0),
                width: rect.width,
                height: rect.height,
            };

            // Trigger callback
            onTextSelected({
                text: selectedText,
                pageNumber: pageNumber,
                position: position,
            });
            
            // Show selection toolbar near selection (use screen coordinates for toolbar positioning)
            const containerRect = containerRef.current?.getBoundingClientRect();
            const toolbarPosition = containerRect ? {
                x: rect.left - containerRect.left,
                y: rect.top - containerRect.top,
            } : { x: 0, y: 0 };
            
            setSelectionInfo({
                visible: true,
                pageNumber: pageNumber,
                x: position.x,  // PDF coordinates for annotation
                y: position.y,
                width: position.width,
                height: position.height,
                text: selectedText,
                toolbarX: toolbarPosition.x,  // Screen coordinates for toolbar
                toolbarY: toolbarPosition.y,
            });
        };

        // Listen for mouseup event (after text selection)
        document.addEventListener('mouseup', handleSelection);
        return () => document.removeEventListener('mouseup', handleSelection);
    }, [onTextSelected, pageNumber, convertScreenToPDF]);

    // Hide selection toolbar on scroll or click elsewhere
    useEffect(() => {
        const hide = () => setSelectionInfo(prev => ({ ...prev, visible: false }));
        const onDown = (e: MouseEvent) => {
            const el = e.target as HTMLElement;
            if (el && el.closest && el.closest('.selection-toolbar')) return;
            hide();
        };
        window.addEventListener('scroll', hide, true);
        window.addEventListener('mousedown', onDown);
        return () => {
            window.removeEventListener('scroll', hide, true);
            window.removeEventListener('mousedown', onDown);
        };
    }, []);

    // Helper to create annotation and emit event (optimistic + persist)
    const createAnnotation = useCallback(async (style: 'highlight' | 'underline' | 'strike' | 'tag') => {
        if (!selectionInfo.visible || !selectionInfo.pageNumber) return;
        const id = `anno_${Date.now()}`;
        const anno = {
            id,
            page: selectionInfo.pageNumber,
            x: selectionInfo.x,
            y: selectionInfo.y,
            width: selectionInfo.width,
            height: selectionInfo.height,
            style,
            text: selectionInfo.text,
        };

        // Optimistic update
        setAnnotations(prev => [...prev, anno]);

        // Prepare payload for backend
        const payload = {
            document_id: documentId,
            user_id: localStorage.getItem('user_id') || 'anonymous',
            annotation_type: style,
            page_number: selectionInfo.pageNumber,
            position: {
                x: selectionInfo.x,
                y: selectionInfo.y,
                width: selectionInfo.width,
                height: selectionInfo.height,
            },
            color: style === 'highlight' ? '#FCD34D' : undefined,
            content: selectionInfo.text,
            tags: [],
        };

        try {
            const saved = await apiService.createAnnotation(payload);
            // Replace optimistic id with real id
            setAnnotations(prev => prev.map(a => a.id === id ? { ...a, id: saved.id } : a));
            // emit an event so other components (e.g., BookmarkPanel) can listen
            try {
                window.dispatchEvent(new CustomEvent('annotationCreated', { detail: saved }));
            } catch (e) {
                console.warn('Failed to dispatch annotationCreated', e);
            }
        } catch (err) {
            console.error('Failed to save annotation', err);
            // leave optimistic annotation but mark as unsynced (not implemented UI)
        }

        // hide toolbar after creation
        setSelectionInfo(prev => ({ ...prev, visible: false }));
    }, [selectionInfo, documentId]);

    // Dispatch AI question event - 设置对话上下文
    const dispatchAIQuestion = useCallback(() => {
        if (!selectionInfo.visible || !selectionInfo.pageNumber) return;
        
        // 通知父组件选中文本，设置为AI对话的上下文
        if (onTextSelected) {
            onTextSelected({
                text: selectionInfo.text,
                pageNumber: selectionInfo.pageNumber,
                position: {
                    x: selectionInfo.x,
                    y: selectionInfo.y,
                    width: selectionInfo.width,
                    height: selectionInfo.height
                }
            });
        }
        
        // 触发AI问题事件，打开聊天面板并设置上下文
        const payload = {
            documentId,
            page_number: selectionInfo.pageNumber,
            selected_text: selectionInfo.text,
            position: {
                x: selectionInfo.x,
                y: selectionInfo.y,
                width: selectionInfo.width,
                height: selectionInfo.height
            },
            action: 'set_context'  // 标记这是设置上下文，而不是直接提问
        };
        try {
            window.dispatchEvent(new CustomEvent('aiQuestion', { detail: payload }));
        } catch (e) {
            console.warn('Failed to dispatch aiQuestion', e);
        }
        setSelectionInfo(prev => ({ ...prev, visible: false }));
    }, [selectionInfo, documentId, onTextSelected]);

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

    // Render bookmark overlays
    const renderBookmarkOverlays = useCallback(
        (pageNum: number) => {
            if (!showBookmarks) return null;

            const pageBookmarks = bookmarks.filter(b => b.page_number === pageNum);

            return pageBookmarks.map((bookmark) => {
                const isHovered = hoveredBookmarkId === bookmark.id;
                const color = bookmark.color || '#FCD34D';

                // Skip bookmark if position is not defined
                if (!bookmark.position) {
                    console.warn('Bookmark missing position:', bookmark.id);
                    return null;
                }

                return (
                    <div key={bookmark.id} className="relative">
                        {/* Bookmark highlight */}
                        <div
                            className={clsx(
                                'absolute cursor-pointer transition-all duration-300',
                                'border-2 rounded',
                                isHovered ? 'shadow-lg z-20' : 'z-10'
                            )}
                            style={{
                                left: bookmark.position.x,
                                top: bookmark.position.y,
                                width: bookmark.position.width,
                                height: bookmark.position.height,
                                backgroundColor: `${color}40`, // 40 is opacity in hex
                                borderColor: color,
                                borderWidth: isHovered ? '3px' : '2px',
                            }}
                            onMouseEnter={() => setHoveredBookmarkId(bookmark.id)}
                            onMouseLeave={() => setHoveredBookmarkId(null)}
                            onClick={() => onBookmarkClick?.(bookmark.id)}
                            title={bookmark.title || bookmark.ai_summary}
                        >
                            {/* Bookmark icon */}
                            <div
                                className="absolute -top-3 -left-1 text-xl"
                                style={{ color }}
                            >
                                🔖
                            </div>
                        </div>

                        {/* Tooltip on hover */}
                        {isHovered && (
                            <div
                                className="absolute z-30 bg-white rounded-lg shadow-xl border border-gray-200 p-3 max-w-xs"
                                style={{
                                    left: bookmark.position.x,
                                    top: bookmark.position.y + bookmark.position.height + 10,
                                }}
                            >
                                <div className="text-sm font-medium text-gray-900 mb-1">
                                    {bookmark.title || '未命名书签'}
                                </div>
                                <div className="text-xs text-gray-600 line-clamp-3">
                                    {bookmark.ai_summary}
                                </div>
                                <div className="mt-2 text-xs text-gray-400">
                                    点击查看详情
                                </div>
                            </div>
                        )}
                    </div>
                );
            });
        },
        [bookmarks, showBookmarks, hoveredBookmarkId, onBookmarkClick]
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
                                <div className="absolute inset-0 pointer-events-auto">
                                    {renderChunkOverlays(pageNumber)}
                                    {renderBookmarkOverlays(pageNumber)}
                                    {annotations.filter(a => a.page === pageNumber).map(a => (
                                        <div key={a.id} className="absolute pointer-events-none"
                                            style={{
                                                left: a.x, top: a.y, width: a.width, height: a.height,
                                                background: a.style === 'highlight' ? 'rgba(250,235,150,0.45)' : undefined,
                                                textDecoration: a.style === 'underline' ? 'underline' : a.style === 'strike' ? 'line-through' : undefined,
                                                border: a.style === 'tag' ? '2px dashed rgba(251,146,60,0.6)' : undefined
                                            }} />
                                    ))}
                                </div>
                                {selectionInfo.visible && selectionInfo.pageNumber === pageNumber && (
                                    <div className="selection-toolbar absolute" style={{ left: selectionInfo.x, top: Math.max(selectionInfo.y - 44, 4), zIndex: 60 }}>
                                        <div className="flex gap-1 bg-white rounded shadow px-2 py-1">
                                            <button onClick={() => createAnnotation('highlight')} className="text-xs px-2 py-0.5">高亮</button>
                                            <button onClick={() => createAnnotation('underline')} className="text-xs px-2 py-0.5">下划线</button>
                                            <button onClick={() => createAnnotation('strike')} className="text-xs px-2 py-0.5">删除线</button>
                                            <button onClick={() => createAnnotation('tag')} className="text-xs px-2 py-0.5">生成标签</button>
                                            <button onClick={dispatchAIQuestion} className="text-xs px-2 py-0.5 text-blue-600">AI 提问</button>
                                        </div>
                                    </div>
                                )}
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
                                        <div className="absolute inset-0 pointer-events-auto">
                                            {renderChunkOverlays(pageNum)}
                                            {renderBookmarkOverlays(pageNum)}
                                            {annotations.filter(a => a.page === pageNum).map(a => (
                                                <div key={a.id} className="absolute pointer-events-none"
                                                    style={{
                                                        left: a.x, top: a.y, width: a.width, height: a.height,
                                                        background: a.style === 'highlight' ? 'rgba(250,235,150,0.45)' : undefined,
                                                        textDecoration: a.style === 'underline' ? 'underline' : a.style === 'strike' ? 'line-through' : undefined,
                                                        border: a.style === 'tag' ? '2px dashed rgba(251,146,60,0.6)' : undefined
                                                    }} />
                                            ))}
                                            {selectionInfo.visible && selectionInfo.pageNumber === pageNum && (
                                                <div className="selection-toolbar absolute" style={{ left: selectionInfo.x, top: Math.max(selectionInfo.y - 44, 4), zIndex: 60 }}>
                                                    <div className="flex gap-1 bg-white rounded shadow px-2 py-1">
                                                        <button onClick={() => createAnnotation('highlight')} className="text-xs px-2 py-0.5">高亮</button>
                                                        <button onClick={() => createAnnotation('underline')} className="text-xs px-2 py-0.5">下划线</button>
                                                        <button onClick={() => createAnnotation('strike')} className="text-xs px-2 py-0.5">删除线</button>
                                                        <button onClick={() => createAnnotation('tag')} className="text-xs px-2 py-0.5">生成标签</button>
                                                        <button onClick={dispatchAIQuestion} className="text-xs px-2 py-0.5 text-blue-600">AI 提问</button>
                                                    </div>
                                                </div>
                                            )}
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
        </div>
    );
}
