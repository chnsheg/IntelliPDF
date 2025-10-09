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
    const [pageNumber, setPageNumber] = useState<number>(1);
    const [numPages, setNumPages] = useState<number>(0);
    const [scale, setScale] = useState<number>(1.5);
    const [editorMode, setEditorMode] = useState<number>(AnnotationEditorType.NONE);
    const [annotationColor, setAnnotationColor] = useState<string>('#ff0000');
    const [annotationThickness, setAnnotationThickness] = useState<number>(2);

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
     * 渲染当前页面（Canvas + TextLayer + AnnotationEditorLayer）
     */
    useEffect(() => {
        if (!pdfDocument || !canvasRef.current || !textLayerRef.current || !editorLayerRef.current) return;

        let renderTask: any = null;

        const renderPage = async () => {
            try {
                console.log('[PDFViewerNative] Rendering page:', pageNumber, 'editorMode:', editorMode);

                const page = await pdfDocument.getPage(pageNumber);
                const viewport = page.getViewport({ scale });

                // 1. 渲染 Canvas（PDF 内容）
                const canvas = canvasRef.current!;
                const context = canvas.getContext('2d')!;
                canvas.height = viewport.height;
                canvas.width = viewport.width;

                const renderContext = {
                    canvasContext: context,
                    viewport: viewport,
                };

                renderTask = page.render(renderContext);
                await renderTask.promise;

                // 2. 渲染文本层（用于文本选择）
                await renderTextLayer(page, viewport);

                // 3. 初始化标注编辑器层
                await initializeEditorLayer(page, viewport);

                console.log('[PDFViewerNative] Page rendered successfully');
            } catch (error: any) {
                if (error?.name === 'RenderingCancelledException') {
                    console.log('[PDFViewerNative] Rendering cancelled');
                } else {
                    console.error('[PDFViewerNative] Failed to render page:', error);
                }
            }
        };

        renderPage();

        return () => {
            if (renderTask) {
                renderTask.cancel();
            }
        };
    }, [pdfDocument, pageNumber, scale, editorMode]);

    /**
     * 渲染文本层（简化版）
     * 注：完整的 TextLayer 需要 pdfjs-dist/web/pdf_viewer.css
     */
    const renderTextLayer = async (page: PDFPageProxy, viewport: any) => {
        const textLayerDiv = textLayerRef.current!;
        textLayerDiv.innerHTML = '';
        textLayerDiv.style.width = `${viewport.width}px`;
        textLayerDiv.style.height = `${viewport.height}px`;

        const textContent = await page.getTextContent();

        // 简化实现：只渲染文本用于选择
        // 完整实现需要使用 pdfjs-dist/web/text_layer_builder.js
        textContent.items.forEach((item: any) => {
            const tx = pdfjsLib.Util.transform(viewport.transform, item.transform);
            const angle = Math.atan2(tx[1], tx[0]);
            const style = textContent.styles[item.fontName];

            const textDiv = document.createElement('span');
            textDiv.textContent = item.str;
            textDiv.style.position = 'absolute';
            textDiv.style.left = `${tx[4]}px`;
            textDiv.style.top = `${tx[5]}px`;
            textDiv.style.fontSize = `${Math.abs(tx[0])}px`;
            textDiv.style.fontFamily = style?.fontFamily || 'sans-serif';
            textDiv.style.transform = `rotate(${angle}rad)`;
            textDiv.style.transformOrigin = '0 0';
            textDiv.style.whiteSpace = 'pre';
            textDiv.style.color = 'transparent'; // 透明文本，但可选择
            textDiv.style.userSelect = 'text';

            textLayerDiv.appendChild(textDiv);
        });
    };

    /**
     * 渲染已保存的标注（从 annotationStorage 加载）
     */
    const renderSavedAnnotations = useCallback(async (_page: PDFPageProxy, viewport: any) => {
        const annotationLayerDiv = annotationLayerRef.current!;
        annotationLayerDiv.innerHTML = '';
        annotationLayerDiv.style.width = `${viewport.width}px`;
        annotationLayerDiv.style.height = `${viewport.height}px`;

        if (!pdfDocument?.annotationStorage) return;

        const storage = pdfDocument.annotationStorage;
        const serializable = storage.serializable;

        // 遍历所有标注，渲染当前页的标注
        Object.entries(serializable).forEach(([id, data]: [string, any]) => {
            if (data.pageIndex !== pageNumber - 1) return; // 只渲染当前页

            const annotDiv = document.createElement('div');
            annotDiv.className = 'saved-annotation';
            annotDiv.dataset.annotationId = id;
            annotDiv.style.position = 'absolute';

            if (data.annotationType === AnnotationEditorType.INK) {
                // 渲染画笔标注
                const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
                svg.style.position = 'absolute';
                svg.style.width = '100%';
                svg.style.height = '100%';
                svg.style.pointerEvents = 'none';

                const paths = data.paths || [];
                paths.forEach((path: any[]) => {
                    const pathElement = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                    const d = `M ${path.map((p: any) => `${p.x},${p.y}`).join(' L ')}`;
                    pathElement.setAttribute('d', d);
                    pathElement.setAttribute('stroke', `rgb(${data.color?.join(',') || '255,0,0'})`);
                    pathElement.setAttribute('stroke-width', String(data.thickness || 2));
                    pathElement.setAttribute('fill', 'none');
                    svg.appendChild(pathElement);
                });

                annotDiv.appendChild(svg);
            } else if (data.annotationType === AnnotationEditorType.FREETEXT) {
                // 渲染文本标注
                const [x1, y1, x2, y2] = data.rect || [0, 0, 100, 30];
                annotDiv.style.left = `${x1}px`;
                annotDiv.style.top = `${y1}px`;
                annotDiv.style.width = `${x2 - x1}px`;
                annotDiv.style.height = `${y2 - y1}px`;
                annotDiv.style.padding = '4px 8px';
                annotDiv.style.backgroundColor = 'rgba(255, 255, 255, 0.9)';
                annotDiv.style.border = `1px solid rgb(${data.color?.join(',') || '0,0,255'})`;
                annotDiv.style.borderRadius = '4px';
                annotDiv.style.fontSize = '14px';
                annotDiv.textContent = data.contents || '';
            } else if (data.annotationType === AnnotationEditorType.STAMP) {
                // 渲染图章标注
                const [x1, y1, x2, y2] = data.rect || [0, 0, 100, 100];
                annotDiv.style.left = `${x1}px`;
                annotDiv.style.top = `${y1}px`;
                annotDiv.style.width = `${x2 - x1}px`;
                annotDiv.style.height = `${y2 - y1}px`;
                
                if (data.imageData) {
                    const img = document.createElement('img');
                    img.src = data.imageData;
                    img.style.width = '100%';
                    img.style.height = '100%';
                    img.style.objectFit = 'contain';
                    annotDiv.appendChild(img);
                }
            }

            annotationLayerDiv.appendChild(annotDiv);
        });
    }, [pdfDocument, pageNumber]);

    /**
     * 初始化标注编辑器层（核心功能）
     */
    const initializeEditorLayer = useCallback(async (page: PDFPageProxy, viewport: any) => {
        const editorLayerDiv = editorLayerRef.current!;
        editorLayerDiv.innerHTML = '';
        editorLayerDiv.style.width = `${viewport.width}px`;
        editorLayerDiv.style.height = `${viewport.height}px`;

        // 先渲染已保存的标注
        await renderSavedAnnotations(page, viewport);

        // 创建编辑器容器
        const editorContainer = document.createElement('div');
        editorContainer.className = 'annotationEditorLayer';
        editorContainer.style.position = 'absolute';
        editorContainer.style.top = '0';
        editorContainer.style.left = '0';
        editorContainer.style.width = '100%';
        editorContainer.style.height = '100%';

        // 根据当前模式设置编辑器行为
        if (editorMode === AnnotationEditorType.INK) {
            enableInkEditor(editorContainer);
        } else if (editorMode === AnnotationEditorType.FREETEXT) {
            enableFreeTextEditor(editorContainer);
        } else if (editorMode === AnnotationEditorType.STAMP) {
            enableStampEditor(editorContainer);
        } else if (editorMode === AnnotationEditorType.NONE) {
            // 选择模式 - 启用标注选择和删除
            const annotationLayerDiv = annotationLayerRef.current;
            if (annotationLayerDiv) {
                enableSelectMode(annotationLayerDiv);
            }
            editorContainer.classList.add('disabled');
        }

        editorLayerDiv.appendChild(editorContainer);
    }, [editorMode, pageNumber, pdfDocument, saveAnnotations, renderSavedAnnotations]);

    /**
     * 启用选择模式 - 可以选中和删除标注
     */
    const enableSelectMode = useCallback((annotationLayer: HTMLElement) => {
        let selectedAnnotation: HTMLElement | null = null;

        const handleAnnotationClick = (e: MouseEvent) => {
            const target = e.target as HTMLElement;
            const annotDiv = target.closest('.saved-annotation') as HTMLElement;
            
            if (!annotDiv) {
                // 点击空白处，取消选择
                if (selectedAnnotation) {
                    selectedAnnotation.style.outline = '';
                    selectedAnnotation = null;
                }
                return;
            }

            // 选中标注
            if (selectedAnnotation) {
                selectedAnnotation.style.outline = '';
            }
            selectedAnnotation = annotDiv;
            annotDiv.style.outline = '2px solid #0066ff';
            annotDiv.style.outlineOffset = '2px';
        };

        const handleKeyDown = async (e: KeyboardEvent) => {
            if ((e.key === 'Delete' || e.key === 'Backspace') && selectedAnnotation) {
                const annotationId = selectedAnnotation.dataset.annotationId;
                if (annotationId && pdfDocument?.annotationStorage) {
                    // 从 storage 中删除
                    pdfDocument.annotationStorage.remove(annotationId);
                    
                    // 保存更新
                    await saveAnnotations(pdfDocument.annotationStorage.serializable);
                    
                    // 从 DOM 中移除
                    selectedAnnotation.remove();
                    selectedAnnotation = null;
                    
                    console.log('[SelectMode] Deleted annotation:', annotationId);
                }
            }
        };

        annotationLayer.addEventListener('click', handleAnnotationClick);
        document.addEventListener('keydown', handleKeyDown);
        
        return () => {
            annotationLayer.removeEventListener('click', handleAnnotationClick);
            document.removeEventListener('keydown', handleKeyDown);
        };
    }, [pdfDocument, saveAnnotations]);

    /**
     * 启用画笔编辑器
     */
    const enableInkEditor = useCallback((container: HTMLElement) => {
        let isDrawing = false;
        let currentPath: { x: number; y: number }[] = [];
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.style.width = '100%';
        svg.style.height = '100%';
        svg.style.position = 'absolute';
        svg.style.pointerEvents = 'auto';
        container.appendChild(svg);

        // 将 hex 颜色转换为 RGB 数组
        const hexToRgb = (hex: string): [number, number, number] => {
            const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
            return result
                ? [parseInt(result[1], 16) / 255, parseInt(result[2], 16) / 255, parseInt(result[3], 16) / 255]
                : [1, 0, 0];
        };

        const handleMouseDown = (e: MouseEvent) => {
            isDrawing = true;
            const rect = container.getBoundingClientRect();
            currentPath = [{ x: e.clientX - rect.left, y: e.clientY - rect.top }];
        };

        const handleMouseMove = (e: MouseEvent) => {
            if (!isDrawing) return;
            const rect = container.getBoundingClientRect();
            currentPath.push({ x: e.clientX - rect.left, y: e.clientY - rect.top });

            // 实时绘制路径
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            const d = `M ${currentPath.map(p => `${p.x},${p.y}`).join(' L ')}`;
            path.setAttribute('d', d);
            path.setAttribute('stroke', annotationColor);
            path.setAttribute('stroke-width', String(annotationThickness));
            path.setAttribute('fill', 'none');
            svg.innerHTML = '';
            svg.appendChild(path);
        };

        const handleMouseUp = async () => {
            if (isDrawing && currentPath.length > 2) {
                isDrawing = false;

                // 保存标注到 PDF.js annotationStorage
                const annotationData = {
                    annotationType: AnnotationEditorType.INK,
                    pageIndex: pageNumber - 1,
                    paths: [currentPath],
                    color: hexToRgb(annotationColor),
                    thickness: annotationThickness,
                };

                console.log('[InkEditor] Created annotation:', annotationData);

                // 保存到 annotationStorage
                if (pdfDocument?.annotationStorage) {
                    const id = `ink_${Date.now()}_${Math.random()}`;
                    pdfDocument.annotationStorage.setValue(id, annotationData);
                    saveAnnotations(pdfDocument.annotationStorage.serializable);
                }

                currentPath = [];
                svg.innerHTML = '';
            }
        };

        container.addEventListener('mousedown', handleMouseDown);
        container.addEventListener('mousemove', handleMouseMove);
        container.addEventListener('mouseup', handleMouseUp);
    }, [pdfDocument, pageNumber, saveAnnotations, annotationColor, annotationThickness]);

    /**
     * 启用文本编辑器
     */
    const enableFreeTextEditor = useCallback((container: HTMLElement) => {
        const handleClick = (e: MouseEvent) => {
            const rect = container.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            // 创建文本输入框
            const input = document.createElement('input');
            input.type = 'text';
            input.placeholder = '输入文本...';
            input.style.position = 'absolute';
            input.style.left = `${x}px`;
            input.style.top = `${y}px`;
            input.style.fontSize = '16px';
            input.style.padding = '4px 8px';
            input.style.border = '1px solid #0000ff';
            input.style.borderRadius = '4px';
            input.style.backgroundColor = '#ffffff';
            input.style.zIndex = '1000';

            container.appendChild(input);
            input.focus();

            const handleBlur = async () => {
                const text = input.value.trim();
                if (text) {
                    // 将 hex 颜色转换为 RGB 数组
                    const hexToRgb = (hex: string): [number, number, number] => {
                        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
                        return result
                            ? [parseInt(result[1], 16) / 255, parseInt(result[2], 16) / 255, parseInt(result[3], 16) / 255]
                            : [0, 0, 1];
                    };

                    // 保存标注
                    const annotationData = {
                        annotationType: AnnotationEditorType.FREETEXT,
                        pageIndex: pageNumber - 1,
                        rect: [x, y, x + 200, y + 30],
                        contents: text,
                        color: hexToRgb(annotationColor),
                    };

                    console.log('[FreeTextEditor] Created annotation:', annotationData);

                    if (pdfDocument?.annotationStorage) {
                        const id = `freetext_${Date.now()}_${Math.random()}`;
                        pdfDocument.annotationStorage.setValue(id, annotationData);
                        saveAnnotations(pdfDocument.annotationStorage.serializable);
                    }
                }
                input.remove();
            };

            input.addEventListener('blur', handleBlur);
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    input.blur();
                }
            });
        };

        container.addEventListener('click', handleClick);
    }, [pdfDocument, pageNumber, saveAnnotations, annotationColor]);

    /**
     * 启用图章编辑器
     */
    const enableStampEditor = useCallback((container: HTMLElement) => {
        const handleClick = async (e: MouseEvent) => {
            const rect = container.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            // 创建文件选择对话框
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = 'image/*';
            
            input.onchange = async () => {
                const file = input.files?.[0];
                if (!file) return;

                const reader = new FileReader();
                reader.onload = async (evt) => {
                    const imageData = evt.target?.result as string;
                    
                    // 保存标注
                    const annotationData = {
                        annotationType: AnnotationEditorType.STAMP,
                        pageIndex: pageNumber - 1,
                        rect: [x, y, x + 100, y + 100],
                        imageData: imageData,
                    };

                    console.log('[StampEditor] Created annotation');

                    if (pdfDocument?.annotationStorage) {
                        const id = `stamp_${Date.now()}_${Math.random()}`;
                        pdfDocument.annotationStorage.setValue(id, annotationData);
                        saveAnnotations(pdfDocument.annotationStorage.serializable);
                    }
                };
                reader.readAsDataURL(file);
            };

            input.click();
        };

        container.addEventListener('click', handleClick);
    }, [pdfDocument, pageNumber, saveAnnotations]);

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
     * 处理工具变化 - 重新初始化编辑器层
     */
    const handleToolChange = useCallback((mode: number) => {
        console.log('[PDFViewerNative] Tool changed:', mode);
        setEditorMode(mode);

        // 编辑器模式变化后，需要重新渲染当前页以应用新模式
        // useEffect 会自动触发重新渲染
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
                color={annotationColor}
                onColorChange={setAnnotationColor}
                thickness={annotationThickness}
                onThicknessChange={setAnnotationThickness}
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
