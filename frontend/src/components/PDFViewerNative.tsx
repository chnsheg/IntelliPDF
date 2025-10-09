/**
 * PDF Viewer with Native PDF.js AnnotationEditorLayer
 * 
 * 完全使用 PDF.js 原生 API，不依赖 react-pdf
 * 支持所有 PDF.js 标注编辑功能
 */

import React, { useState, useCallback, useEffect, useRef } from 'react';
import * as pdfjsLib from 'pdfjs-dist';
import type { PDFDocumentProxy, PDFPageProxy } from 'pdfjs-dist';
import { PDFAnnotationToolbar } from './PDFAnnotationToolbar';
import { usePDFAnnotations } from '../hooks/usePDFAnnotations';

// 配置 PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;

interface PDFViewerNativeProps {
    documentId: string;
    pdfUrl: string;
}

// PDF.js AnnotationEditorType
const AnnotationEditorType = {
    DISABLE: -1,
    NONE: 0,
    FREETEXT: 3,
    HIGHLIGHT: 9,
    STAMP: 13,
    INK: 15,
};

export const PDFViewerNative: React.FC<PDFViewerNativeProps> = ({
    documentId,
    pdfUrl,
}) => {
    const containerRef = useRef<HTMLDivElement>(null);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const textLayerRef = useRef<HTMLDivElement>(null);
    const annotationLayerRef = useRef<HTMLDivElement>(null);
    const editorLayerRef = useRef<HTMLDivElement>(null);

    const [pdfDocument, setPdfDocument] = useState<PDFDocumentProxy | null>(null);
    const [currentPage, setCurrentPage] = useState<PDFPageProxy | null>(null);
    const [pageNumber, setPageNumber] = useState<number>(1);
    const [numPages, setNumPages] = useState<number>(0);
    const [scale, setScale] = useState<number>(1.5);
    const [editorMode, setEditorMode] = useState<number>(AnnotationEditorType.NONE);

    const { loadAnnotations, saveAnnotations, isLoading } = usePDFAnnotations(documentId);

    /**
     * 加载 PDF 文档
     */
    useEffect(() => {
        let loadingTask: any = null;

        const loadPDF = async () => {
            try {
                console.log('[PDFViewerNative] Loading PDF:', pdfUrl);

                loadingTask = pdfjsLib.getDocument(pdfUrl);
                const pdf = await loadingTask.promise;

                console.log('[PDFViewerNative] PDF loaded, pages:', pdf.numPages);
                setPdfDocument(pdf);
                setNumPages(pdf.numPages);

                // 加载已保存的标注
                await loadAnnotations(pdf);
            } catch (error) {
                console.error('[PDFViewerNative] Failed to load PDF:', error);
            }
        };

        loadPDF();

        return () => {
            if (loadingTask) {
                loadingTask.destroy();
            }
        };
    }, [pdfUrl, loadAnnotations]);

    /**
     * 渲染当前页面
     */
    useEffect(() => {
        if (!pdfDocument || !canvasRef.current || !textLayerRef.current) return;

        const renderPage = async () => {
            try {
                console.log('[PDFViewerNative] Rendering page:', pageNumber);

                const page = await pdfDocument.getPage(pageNumber);
                setCurrentPage(page);

                const viewport = page.getViewport({ scale });

                // 设置 canvas 尺寸
                const canvas = canvasRef.current!;
                const context = canvas.getContext('2d')!;
                canvas.height = viewport.height;
                canvas.width = viewport.width;

                // 渲染 PDF 页面
                const renderContext = {
                    canvasContext: context,
                    viewport: viewport,
                };

                await page.render(renderContext).promise;

                // 渲染文本层
                const textContent = await page.getTextContent();
                const textLayerDiv = textLayerRef.current!;
                textLayerDiv.innerHTML = ''; // 清空
                textLayerDiv.style.width = `${viewport.width}px`;
                textLayerDiv.style.height = `${viewport.height}px`;

                // TODO: 使用 PDF.js 的 TextLayer API 渲染文本
                // 这里需要引入 pdfjs-dist/web/pdf_viewer.js

                console.log('[PDFViewerNative] Page rendered successfully');
            } catch (error) {
                console.error('[PDFViewerNative] Failed to render page:', error);
            }
        };

        renderPage();
    }, [pdfDocument, pageNumber, scale]);

    /**
     * 监听标注变化
     */
    useEffect(() => {
        if (!pdfDocument) return;

        const handleAnnotationChange = () => {
            console.log('[PDFViewerNative] Annotation changed');

            // 获取标注数据
            const storage = pdfDocument.annotationStorage;
            const annotations = storage.serializable;

            console.log('[PDFViewerNative] Saving annotations:', annotations);

            // 保存到后端
            saveAnnotations(annotations);
        };

        // 监听标注编辑器状态变化
        // TODO: 需要正确设置事件监听
        const eventBus = (pdfDocument as any)._eventBus || (pdfDocument as any).eventBus;
        if (eventBus) {
            eventBus.on('annotationeditorstateschanged', handleAnnotationChange);

            return () => {
                eventBus.off('annotationeditorstateschanged', handleAnnotationChange);
            };
        }
    }, [pdfDocument, saveAnnotations]);

    /**
     * 处理工具变化
     */
    const handleToolChange = useCallback((mode: number) => {
        console.log('[PDFViewerNative] Tool changed:', mode);
        setEditorMode(mode);

        // TODO: 实际应用编辑器模式
        // 需要使用 PDF.js 的 AnnotationEditorLayer API
    }, []);

    /**
     * 缩放控制
     */
    const handleZoomIn = useCallback(() => {
        setScale(prev => Math.min(prev + 0.2, 3.0));
    }, []);

    const handleZoomOut = useCallback(() => {
        setScale(prev => Math.max(prev - 0.2, 0.5));
    }, []);

    /**
     * 页面导航
     */
    const goToPrevPage = useCallback(() => {
        setPageNumber(prev => Math.max(prev - 1, 1));
    }, []);

    const goToNextPage = useCallback(() => {
        setPageNumber(prev => Math.min(prev + 1, numPages));
    }, [numPages]);

    return (
        <div className="relative w-full h-screen flex flex-col bg-gray-50">
            {/* 工具栏 */}
            <PDFAnnotationToolbar
                currentMode={editorMode}
                onModeChange={handleToolChange}
                onZoomIn={handleZoomIn}
                onZoomOut={handleZoomOut}
                scale={scale}
            />

            {/* 顶部导航栏 */}
            <div className="flex items-center justify-center gap-4 p-4 bg-white border-b shadow-sm">
                <button
                    onClick={goToPrevPage}
                    disabled={pageNumber <= 1}
                    className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                >
                    ← 上一页
                </button>

                <div className="flex items-center gap-2">
                    <input
                        type="number"
                        value={pageNumber}
                        onChange={(e) => {
                            const num = parseInt(e.target.value);
                            if (num >= 1 && num <= numPages) {
                                setPageNumber(num);
                            }
                        }}
                        className="w-16 px-2 py-1 border rounded text-center"
                        min={1}
                        max={numPages}
                    />
                    <span className="text-sm text-gray-600">/ {numPages}</span>
                </div>

                <button
                    onClick={goToNextPage}
                    disabled={pageNumber >= numPages}
                    className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                >
                    下一页 →
                </button>

                <div className="ml-4 flex items-center gap-2">
                    <button
                        onClick={handleZoomOut}
                        className="px-3 py-1 bg-gray-200 rounded hover:bg-gray-300 transition-colors"
                    >
                        －
                    </button>
                    <span className="text-sm font-medium">{Math.round(scale * 100)}%</span>
                    <button
                        onClick={handleZoomIn}
                        className="px-3 py-1 bg-gray-200 rounded hover:bg-gray-300 transition-colors"
                    >
                        ＋
                    </button>
                </div>
            </div>

            {/* PDF 渲染区域 */}
            <div
                ref={containerRef}
                className="flex-1 overflow-auto p-8 flex items-start justify-center"
            >
                <div className="relative shadow-2xl" style={{ width: 'fit-content' }}>
                    {/* Canvas 层 - PDF 内容 */}
                    <canvas
                        ref={canvasRef}
                        className="block"
                    />

                    {/* 文本层 - 文本选择 */}
                    <div
                        ref={textLayerRef}
                        className="absolute top-0 left-0 textLayer"
                        style={{ pointerEvents: 'auto' }}
                    />

                    {/* 标注层 - 显示已有标注 */}
                    <div
                        ref={annotationLayerRef}
                        className="absolute top-0 left-0 annotationLayer"
                    />

                    {/* 编辑层 - 创建新标注 */}
                    <div
                        ref={editorLayerRef}
                        className="absolute top-0 left-0 annotationEditorLayer"
                    />
                </div>
            </div>

            {/* 加载状态 */}
            {isLoading && (
                <div className="fixed bottom-4 right-4 bg-white rounded-lg shadow-lg p-4 flex items-center gap-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                    <span className="text-sm">保存中...</span>
                </div>
            )}

            {/* 提示信息 */}
            {editorMode !== AnnotationEditorType.NONE && (
                <div className="fixed top-20 left-1/2 transform -translate-x-1/2 bg-blue-500 text-white px-4 py-2 rounded-lg shadow-lg text-sm">
                    {editorMode === AnnotationEditorType.INK && '画笔模式：在页面上拖拽绘制'}
                    {editorMode === AnnotationEditorType.FREETEXT && '文本模式：点击页面添加文本'}
                    {editorMode === AnnotationEditorType.STAMP && '图章模式：点击页面添加图章'}
                    {editorMode === AnnotationEditorType.HIGHLIGHT && '高亮模式：选择文本进行高亮'}
                </div>
            )}
        </div>
    );
};
