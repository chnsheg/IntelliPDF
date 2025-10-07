/**
 * PDF Viewer Component with responsive design
 */

import { useState, useCallback } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import {
    FiChevronLeft,
    FiChevronRight,
    FiZoomIn,
    FiZoomOut,
    FiMaximize,
    FiDownload,
} from 'react-icons/fi';
import { useIsMobile } from '../hooks/useResponsive';
import clsx from 'clsx';

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
    const [isFullscreen, setIsFullscreen] = useState(false);
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
        setPageNumber((prev) => Math.max(prev - 1, 1));
        onPageChange?.(Math.max(pageNumber - 1, 1));
    }, [pageNumber, onPageChange]);

    const goToNextPage = useCallback(() => {
        setPageNumber((prev) => Math.min(prev + 1, numPages));
        onPageChange?.(Math.min(pageNumber + 1, numPages));
    }, [pageNumber, numPages, onPageChange]);

    // Zoom handlers
    const zoomIn = useCallback(() => {
        setScale((prev) => Math.min(prev + 0.2, 3.0));
    }, []);

    const zoomOut = useCallback(() => {
        setScale((prev) => Math.max(prev - 0.2, 0.5));
    }, []);

    // Fullscreen handler
    const toggleFullscreen = useCallback(() => {
        setIsFullscreen((prev) => !prev);
    }, []);

    return (
        <div
            className={clsx(
                'flex flex-col bg-gray-100',
                isFullscreen ? 'fixed inset-0 z-50' : 'h-full'
            )}
        >
            {/* Toolbar */}
            <div className="bg-white border-b border-gray-200 px-4 py-2 flex items-center justify-between no-print">
                {/* Left: Navigation */}
                <div className="flex items-center gap-2">
                    <button
                        onClick={goToPrevPage}
                        disabled={pageNumber <= 1}
                        className="btn-icon"
                        aria-label="上一页"
                    >
                        <FiChevronLeft className="w-5 h-5" />
                    </button>

                    <div className="flex items-center gap-2 text-sm">
                        <input
                            type="number"
                            value={pageNumber}
                            onChange={(e) => {
                                const page = parseInt(e.target.value);
                                if (page >= 1 && page <= numPages) {
                                    setPageNumber(page);
                                    onPageChange?.(page);
                                }
                            }}
                            className="w-16 px-2 py-1 border border-gray-300 rounded text-center"
                            min={1}
                            max={numPages}
                        />
                        <span className="text-gray-600">/ {numPages}</span>
                    </div>

                    <button
                        onClick={goToNextPage}
                        disabled={pageNumber >= numPages}
                        className="btn-icon"
                        aria-label="下一页"
                    >
                        <FiChevronRight className="w-5 h-5" />
                    </button>
                </div>

                {/* Center: Zoom controls (hidden on mobile) */}
                {!isMobile && (
                    <div className="flex items-center gap-2">
                        <button
                            onClick={zoomOut}
                            disabled={scale <= 0.5}
                            className="btn-icon"
                            aria-label="缩小"
                        >
                            <FiZoomOut className="w-5 h-5" />
                        </button>

                        <span className="text-sm text-gray-600 min-w-[60px] text-center">
                            {Math.round(scale * 100)}%
                        </span>

                        <button
                            onClick={zoomIn}
                            disabled={scale >= 3.0}
                            className="btn-icon"
                            aria-label="放大"
                        >
                            <FiZoomIn className="w-5 h-5" />
                        </button>
                    </div>
                )}

                {/* Right: Actions */}
                <div className="flex items-center gap-2">
                    <button
                        onClick={toggleFullscreen}
                        className="btn-icon"
                        aria-label={isFullscreen ? '退出全屏' : '全屏'}
                    >
                        <FiMaximize className="w-5 h-5" />
                    </button>

                    <a
                        href={fileUrl}
                        download
                        className="btn-icon"
                        aria-label="下载PDF"
                    >
                        <FiDownload className="w-5 h-5" />
                    </a>
                </div>
            </div>

            {/* PDF Content */}
            <div className="flex-1 overflow-auto flex items-center justify-center p-4">
                <Document
                    file={fileUrl}
                    onLoadSuccess={onDocumentLoadSuccess}
                    loading={
                        <div className="flex items-center justify-center p-8">
                            <div className="animate-spin w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full" />
                            <span className="ml-3 text-gray-600">加载PDF中...</span>
                        </div>
                    }
                    error={
                        <div className="text-center p-8">
                            <p className="text-red-600 mb-2">PDF 加载失败</p>
                            <p className="text-sm text-gray-600">请检查文件是否存在</p>
                        </div>
                    }
                >
                    <Page
                        pageNumber={pageNumber}
                        scale={scale}
                        className="shadow-lg"
                        renderTextLayer={true}
                        renderAnnotationLayer={true}
                        loading={
                            <div className="flex items-center justify-center p-8">
                                <div className="animate-spin w-6 h-6 border-4 border-primary-600 border-t-transparent rounded-full" />
                            </div>
                        }
                    />
                </Document>
            </div>

            {/* Mobile zoom controls (bottom overlay) */}
            {isMobile && (
                <div className="fixed bottom-20 right-4 flex flex-col gap-2 no-print">
                    <button
                        onClick={zoomIn}
                        disabled={scale >= 3.0}
                        className="w-12 h-12 bg-white rounded-full shadow-lg flex items-center justify-center hover:bg-gray-50"
                        aria-label="放大"
                    >
                        <FiZoomIn className="w-6 h-6 text-gray-700" />
                    </button>
                    <button
                        onClick={zoomOut}
                        disabled={scale <= 0.5}
                        className="w-12 h-12 bg-white rounded-full shadow-lg flex items-center justify-center hover:bg-gray-50"
                        aria-label="缩小"
                    >
                        <FiZoomOut className="w-6 h-6 text-gray-700" />
                    </button>
                </div>
            )}
        </div>
    );
}
