/**
 * PDF Viewer - Simplified Version
 * 
 * 使用 PDF.js 原生 AnnotationEditorLayer 实现标注功能
 * 移除所有自定义 Canvas 标注代码
 */

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';
import { PDFAnnotationToolbar } from './PDFAnnotationToolbar';
import { usePDFAnnotations } from '../hooks/usePDFAnnotations';

// 配置 PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

interface PDFViewerSimplifiedProps {
    documentId: string;
    pdfUrl: string;
}

// PDF.js AnnotationEditorMode 枚举
const AnnotationEditorMode = {
    NONE: 0,        // 无编辑
    FREETEXT: 3,    // 文本框
    INK: 15,        // 画笔
    STAMP: 13,      // 图章
    HIGHLIGHT: 9,   // 高亮（实验性）
};

export const PDFViewerSimplified: React.FC<PDFViewerSimplifiedProps> = ({
    documentId,
    pdfUrl,
}) => {
    const [numPages, setNumPages] = useState<number>(0);
    const [pageNumber, setPageNumber] = useState<number>(1);
    const [scale, setScale] = useState<number>(1.0);
    const [pdfDocument, setPdfDocument] = useState<any>(null);
    
    // ⭐ 标注编辑模式
    const [editorMode, setEditorMode] = useState<number>(AnnotationEditorMode.NONE);
    
    // 使用自定义 Hook 管理标注
    const {
        loadAnnotations,
        saveAnnotations,
        isLoading,
    } = usePDFAnnotations(documentId);

    /**
     * 文档加载完成
     */
    const onDocumentLoadSuccess = useCallback(({ numPages, ...pdf }: any) => {
        console.log('PDF loaded:', { numPages });
        setNumPages(numPages);
        setPdfDocument(pdf);
        
        // 加载已保存的标注
        loadAnnotations(pdf);
    }, [loadAnnotations]);

    /**
     * 监听标注变化
     */
    useEffect(() => {
        if (!pdfDocument) return;

        const handleAnnotationChange = (event: any) => {
            console.log('Annotation changed:', event);
            
            // 获取标注数据
            const storage = pdfDocument.annotationStorage;
            const serializableAnnotations = storage.serializable;
            
            console.log('Serializable annotations:', serializableAnnotations);
            
            // 自动保存到后端
            saveAnnotations(serializableAnnotations);
        };

        // 监听标注编辑器状态变化
        const eventBus = pdfDocument._eventBus || pdfDocument.eventBus;
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
        console.log('Tool changed:', mode);
        setEditorMode(mode);
    }, []);

    /**
     * 缩放控制
     */
    const handleZoomIn = useCallback(() => {
        setScale(prev => Math.min(prev + 0.1, 3.0));
    }, []);

    const handleZoomOut = useCallback(() => {
        setScale(prev => Math.max(prev - 0.1, 0.5));
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
            <div className="flex items-center justify-center gap-4 p-4 bg-white border-b">
                <button
                    onClick={goToPrevPage}
                    disabled={pageNumber <= 1}
                    className="px-4 py-2 bg-blue-500 text-white rounded disabled:bg-gray-300"
                >
                    上一页
                </button>
                
                <span className="text-sm">
                    第 {pageNumber} / {numPages} 页
                </span>
                
                <button
                    onClick={goToNextPage}
                    disabled={pageNumber >= numPages}
                    className="px-4 py-2 bg-blue-500 text-white rounded disabled:bg-gray-300"
                >
                    下一页
                </button>

                <div className="ml-4 flex items-center gap-2">
                    <button
                        onClick={handleZoomOut}
                        className="px-3 py-1 bg-gray-200 rounded hover:bg-gray-300"
                    >
                        -
                    </button>
                    <span className="text-sm">{Math.round(scale * 100)}%</span>
                    <button
                        onClick={handleZoomIn}
                        className="px-3 py-1 bg-gray-200 rounded hover:bg-gray-300"
                    >
                        +
                    </button>
                </div>
            </div>

            {/* PDF 内容区域 */}
            <div className="flex-1 overflow-auto p-8">
                <div className="mx-auto" style={{ width: 'fit-content' }}>
                    <Document
                        file={pdfUrl}
                        onLoadSuccess={onDocumentLoadSuccess}
                        loading={
                            <div className="flex items-center justify-center p-8">
                                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
                            </div>
                        }
                        error={
                            <div className="text-red-500 p-4">
                                PDF 加载失败，请刷新页面重试
                            </div>
                        }
                    >
                        <Page
                            pageNumber={pageNumber}
                            scale={scale}
                            renderTextLayer={true}
                            renderAnnotationLayer={true}
                            // ⭐ 关键：启用标注编辑模式
                            {...(editorMode !== AnnotationEditorMode.NONE && {
                                annotationMode: editorMode,
                            })}
                            className="shadow-lg"
                        />
                    </Document>
                </div>
            </div>

            {/* 加载状态提示 */}
            {isLoading && (
                <div className="fixed bottom-4 right-4 bg-white rounded-lg shadow-lg p-4">
                    <div className="flex items-center gap-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                        <span className="text-sm">保存中...</span>
                    </div>
                </div>
            )}
        </div>
    );
};
