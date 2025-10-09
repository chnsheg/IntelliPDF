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

// PDF.js AnnotationEditorType + 自定义类型
const AnnotationEditorType = {
    DISABLE: -1,
    NONE: 0,
    FREETEXT: 3,
    HIGHLIGHT: 9,
    STAMP: 13,
    INK: 15,
    // 自定义类型（非 PDF.js 标准）
    RECTANGLE: 100,
    CIRCLE: 101,
    ARROW: 102,
    ERASER: 103,
    WAVY_LINE: 104,
    STRIKETHROUGH: 105,
    LASSO: 106,
};

interface Bookmark {
    id: string;
    page_number: number;
    title: string;
    content?: string;
}

export const PDFViewerNative: React.FC<PDFViewerNativeProps & { 
    bookmarks?: Bookmark[];
    onCreateBookmark?: (bookmark: any) => Promise<void>;
    onJumpToBookmark?: (bookmarkId: string) => void;
}> = ({
    documentId,
    pdfUrl,
    bookmarks = [],
    onCreateBookmark,
    onJumpToBookmark,
}) => {
    const containerRef = useRef<HTMLDivElement>(null);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const textLayerRef = useRef<HTMLDivElement>(null);
    const annotationLayerRef = useRef<HTMLDivElement>(null);
    const editorLayerRef = useRef<HTMLDivElement>(null);
    const bookmarkLayerRef = useRef<HTMLDivElement>(null);

    const [pdfDocument, setPdfDocument] = useState<PDFDocumentProxy | null>(null);
    const [pageNumber, setPageNumber] = useState<number>(1);
    const [numPages, setNumPages] = useState<number>(0);
    const [scale, setScale] = useState<number>(2.0); // 提高默认缩放以获得更清晰的显示
    const [editorMode, setEditorMode] = useState<number>(AnnotationEditorType.NONE);
    const [annotationColor, setAnnotationColor] = useState<string>('#ff0000');
    const [annotationThickness, setAnnotationThickness] = useState<number>(2);
    const [fontSize, setFontSize] = useState<number>(16); // 文本字体大小

    const { loadAnnotations, saveAnnotations, isLoading } = usePDFAnnotations(documentId);

    // 声明 renderSavedAnnotations（先声明，后面定义）
    const renderSavedAnnotationsRef = useRef<((page: PDFPageProxy, viewport: any) => Promise<void>) | null>(null);

    // 用于增量渲染单个标注（避免全量重绘）
    const renderSingleAnnotation = useCallback((id: string, data: any, container: HTMLElement) => {
        const annotDiv = document.createElement('div');
        annotDiv.className = 'saved-annotation';
        annotDiv.dataset.annotationId = id;
        annotDiv.style.position = 'absolute';

        if (data.annotationType === AnnotationEditorType.INK) {
            // 渲染画笔标注
            annotDiv.style.left = '0';
            annotDiv.style.top = '0';
            annotDiv.style.width = '100%';
            annotDiv.style.height = '100%';
            annotDiv.style.pointerEvents = 'none';

            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.style.position = 'absolute';
            svg.style.left = '0';
            svg.style.top = '0';
            svg.style.width = '100%';
            svg.style.height = '100%';
            svg.style.pointerEvents = 'none';

            const paths = data.paths || [];
            paths.forEach((path: any[]) => {
                const pathElement = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                const d = `M ${path.map((p: any) => `${p.x},${p.y}`).join(' L ')}`;
                pathElement.setAttribute('d', d);
                const color = data.color
                    ? `rgb(${Math.round(data.color[0] * 255)},${Math.round(data.color[1] * 255)},${Math.round(data.color[2] * 255)})`
                    : 'rgb(255,0,0)';
                pathElement.setAttribute('stroke', color);
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
            const color = data.color
                ? `rgb(${Math.round(data.color[0] * 255)},${Math.round(data.color[1] * 255)},${Math.round(data.color[2] * 255)})`
                : 'rgb(0,0,255)';
            annotDiv.style.border = `2px solid ${color}`;
            annotDiv.style.color = color;
            annotDiv.style.borderRadius = '4px';
            annotDiv.style.fontSize = `${data.fontSize || 16}px`;
            annotDiv.style.pointerEvents = 'auto';
            annotDiv.style.fontWeight = '500';
            annotDiv.textContent = data.contents || '';
        } else if (data.annotationType === AnnotationEditorType.RECTANGLE) {
            // 渲染矩形
            annotDiv.style.left = '0';
            annotDiv.style.top = '0';
            annotDiv.style.width = '100%';
            annotDiv.style.height = '100%';
            annotDiv.style.pointerEvents = 'none';

            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.style.position = 'absolute';
            svg.style.left = '0';
            svg.style.top = '0';
            svg.style.width = '100%';
            svg.style.height = '100%';

            const [x1, y1, x2, y2] = data.rect || [0, 0, 100, 100];
            const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            rect.setAttribute('x', String(x1));
            rect.setAttribute('y', String(y1));
            rect.setAttribute('width', String(x2 - x1));
            rect.setAttribute('height', String(y2 - y1));
            const color = data.color
                ? `rgb(${Math.round(data.color[0] * 255)},${Math.round(data.color[1] * 255)},${Math.round(data.color[2] * 255)})`
                : 'rgb(255,0,0)';
            rect.setAttribute('stroke', color);
            rect.setAttribute('stroke-width', String(data.thickness || 2));
            rect.setAttribute('fill', 'none');
            svg.appendChild(rect);
            annotDiv.appendChild(svg);
        } else if (data.annotationType === AnnotationEditorType.CIRCLE) {
            // 渲染圆形
            annotDiv.style.left = '0';
            annotDiv.style.top = '0';
            annotDiv.style.width = '100%';
            annotDiv.style.height = '100%';
            annotDiv.style.pointerEvents = 'none';

            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.style.position = 'absolute';
            svg.style.left = '0';
            svg.style.top = '0';
            svg.style.width = '100%';
            svg.style.height = '100%';

            const [cx, cy] = data.center || [50, 50];
            const [rx, ry] = data.radius || [40, 40];
            const ellipse = document.createElementNS('http://www.w3.org/2000/svg', 'ellipse');
            ellipse.setAttribute('cx', String(cx));
            ellipse.setAttribute('cy', String(cy));
            ellipse.setAttribute('rx', String(rx));
            ellipse.setAttribute('ry', String(ry));
            const color = data.color
                ? `rgb(${Math.round(data.color[0] * 255)},${Math.round(data.color[1] * 255)},${Math.round(data.color[2] * 255)})`
                : 'rgb(255,0,0)';
            ellipse.setAttribute('stroke', color);
            ellipse.setAttribute('stroke-width', String(data.thickness || 2));
            ellipse.setAttribute('fill', 'none');
            svg.appendChild(ellipse);
            annotDiv.appendChild(svg);
        } else if (data.annotationType === AnnotationEditorType.ARROW) {
            // 渲染箭头
            annotDiv.style.left = '0';
            annotDiv.style.top = '0';
            annotDiv.style.width = '100%';
            annotDiv.style.height = '100%';
            annotDiv.style.pointerEvents = 'none';

            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.style.position = 'absolute';
            svg.style.left = '0';
            svg.style.top = '0';
            svg.style.width = '100%';
            svg.style.height = '100%';

            const [x1, y1] = data.start || [0, 0];
            const [x2, y2] = data.end || [100, 100];

            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', String(x1));
            line.setAttribute('y1', String(y1));
            line.setAttribute('x2', String(x2));
            line.setAttribute('y2', String(y2));
            const color = data.color
                ? `rgb(${Math.round(data.color[0] * 255)},${Math.round(data.color[1] * 255)},${Math.round(data.color[2] * 255)})`
                : 'rgb(255,0,0)';
            line.setAttribute('stroke', color);
            line.setAttribute('stroke-width', String(data.thickness || 2));
            svg.appendChild(line);

            const angle = Math.atan2(y2 - y1, x2 - x1);
            const arrowSize = 15;
            const leftX = x2 - arrowSize * Math.cos(angle - Math.PI / 6);
            const leftY = y2 - arrowSize * Math.sin(angle - Math.PI / 6);
            const rightX = x2 - arrowSize * Math.cos(angle + Math.PI / 6);
            const rightY = y2 - arrowSize * Math.sin(angle + Math.PI / 6);

            const arrowhead = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            arrowhead.setAttribute('d', `M ${leftX},${leftY} L ${x2},${y2} L ${rightX},${rightY}`);
            arrowhead.setAttribute('stroke', color);
            arrowhead.setAttribute('stroke-width', String(data.thickness || 2));
            arrowhead.setAttribute('fill', 'none');
            svg.appendChild(arrowhead);
            annotDiv.appendChild(svg);
        } else if (data.annotationType === AnnotationEditorType.STAMP) {
            // 渲染图章
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
        } else if (data.annotationType === AnnotationEditorType.HIGHLIGHT) {
            // 渲染高亮标注 - 半透明彩色覆盖层
            annotDiv.style.left = '0';
            annotDiv.style.top = '0';
            annotDiv.style.width = '100%';
            annotDiv.style.height = '100%';
            annotDiv.style.pointerEvents = 'none';

            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.style.position = 'absolute';
            svg.style.left = '0';
            svg.style.top = '0';
            svg.style.width = '100%';
            svg.style.height = '100%';

            const rects = data.rects || [];
            const color = data.color
                ? `rgb(${Math.round(data.color[0] * 255)},${Math.round(data.color[1] * 255)},${Math.round(data.color[2] * 255)})`
                : 'rgb(255,255,0)';

            rects.forEach(([x, y, w, h]: number[]) => {
                const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                rect.setAttribute('x', String(x));
                rect.setAttribute('y', String(y));
                rect.setAttribute('width', String(w));
                const height = data.thickness ? data.thickness * 3 : h; // 粗细控制高度
                rect.setAttribute('height', String(height));
                rect.setAttribute('fill', color);
                rect.setAttribute('opacity', '0.4');
                svg.appendChild(rect);
            });

            annotDiv.appendChild(svg);
        } else if (data.annotationType === AnnotationEditorType.WAVY_LINE) {
            // 渲染波浪线
            const [x1, y1] = data.start || [0, 0];
            const [x2, y2] = data.end || [0, 0];

            annotDiv.style.left = '0';
            annotDiv.style.top = '0';
            annotDiv.style.width = '100%';
            annotDiv.style.height = '100%';
            annotDiv.style.pointerEvents = 'auto';

            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.style.position = 'absolute';
            svg.style.left = '0';
            svg.style.top = '0';
            svg.style.width = '100%';
            svg.style.height = '100%';

            const color = data.color
                ? `rgb(${data.color[0]},${data.color[1]},${data.color[2]})`
                : 'rgb(255,0,0)';

            // 创建波浪路径
            const length = Math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2);
            const angle = Math.atan2(y2 - y1, x2 - x1);
            const wavelength = 10;
            const amplitude = (data.thickness || 2) * 2;
            const numWaves = Math.floor(length / wavelength);

            let pathData = `M ${x1} ${y1}`;
            for (let i = 1; i <= numWaves; i++) {
                const t = i / numWaves;
                const x = x1 + t * (x2 - x1);
                const y = y1 + t * (y2 - y1);
                const offset = Math.sin(i * Math.PI) * amplitude;
                const perpX = -Math.sin(angle) * offset;
                const perpY = Math.cos(angle) * offset;
                pathData += ` L ${x + perpX} ${y + perpY}`;
            }
            pathData += ` L ${x2} ${y2}`;

            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.setAttribute('d', pathData);
            path.setAttribute('fill', 'none');
            path.setAttribute('stroke', color);
            path.setAttribute('stroke-width', String(data.thickness || 2));

            svg.appendChild(path);
            annotDiv.appendChild(svg);
        } else if (data.annotationType === AnnotationEditorType.STRIKETHROUGH) {
            // 渲染删除线
            const [x1, y1] = data.start || [0, 0];
            const [x2, y2] = data.end || [0, 0];

            annotDiv.style.left = '0';
            annotDiv.style.top = '0';
            annotDiv.style.width = '100%';
            annotDiv.style.height = '100%';
            annotDiv.style.pointerEvents = 'auto';

            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.style.position = 'absolute';
            svg.style.left = '0';
            svg.style.top = '0';
            svg.style.width = '100%';
            svg.style.height = '100%';

            const color = data.color
                ? `rgb(${data.color[0]},${data.color[1]},${data.color[2]})`
                : 'rgb(255,0,0)';

            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', String(x1));
            line.setAttribute('y1', String(y1));
            line.setAttribute('x2', String(x2));
            line.setAttribute('y2', String(y2));
            line.setAttribute('stroke', color);
            line.setAttribute('stroke-width', String(data.thickness || 2));

            svg.appendChild(line);
            annotDiv.appendChild(svg);
        }

        container.appendChild(annotDiv);
        return annotDiv;
    }, []);

    // 包装 saveAnnotations 以触发增量渲染（避免全量重绘）
    const saveAndRefresh = useCallback(async (annotations: any) => {
        console.log('[saveAndRefresh] Saving annotations (incremental render)');
        await saveAnnotations(annotations);

        // 使用 requestAnimationFrame 优化渲染
        requestAnimationFrame(async () => {
            if (!pdfDocument || !annotationLayerRef.current) return;

            const annotationLayerDiv = annotationLayerRef.current;
            const storage = pdfDocument.annotationStorage;
            const serializable = storage.serializable;
            const annotationsMap = serializable.map || new Map();

            // 获取当前页的所有标注ID
            const existingIds = new Set<string>();
            annotationLayerDiv.querySelectorAll('[data-annotation-id]').forEach((el: any) => {
                existingIds.add(el.dataset.annotationId);
            });

            // 检查新增的标注
            annotationsMap.forEach((data: any, id: string) => {
                if (data.pageIndex !== pageNumber - 1) return;

                if (!existingIds.has(id)) {
                    // 新标注，增量添加
                    console.log('[saveAndRefresh] Adding new annotation:', id);
                    renderSingleAnnotation(id, data, annotationLayerDiv);
                }
            });

            console.log('[saveAndRefresh] Incremental render complete');
        });
    }, [saveAnnotations, pdfDocument, pageNumber, renderSingleAnnotation]);

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

                // 1. 渲染 Canvas（PDF 内容） - 高清渲染
                const canvas = canvasRef.current!;
                const context = canvas.getContext('2d')!;

                // 使用 devicePixelRatio 提升清晰度
                const outputScale = window.devicePixelRatio || 1;
                canvas.width = Math.floor(viewport.width * outputScale);
                canvas.height = Math.floor(viewport.height * outputScale);
                canvas.style.width = `${viewport.width}px`;
                canvas.style.height = `${viewport.height}px`;

                // 缩放 context 以匹配高分辨率
                const transform = outputScale !== 1 ? [outputScale, 0, 0, outputScale, 0, 0] : null;

                const renderContext = {
                    canvasContext: context,
                    viewport: viewport,
                    transform: transform as any,
                };

                renderTask = page.render(renderContext);
                await renderTask.promise;

                // 2. 渲染文本层（用于文本选择）
                await renderTextLayer(page, viewport);

                // 3. 初始化标注编辑器层
                await initializeEditorLayer(page, viewport);

                // 4. 渲染书签可视化层
                renderBookmarkLayer(viewport);

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
        textLayerDiv.style.pointerEvents = 'auto'; // 允许文字选择
        textLayerDiv.style.userSelect = 'text'; // 允许文字选择

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

        if (!pdfDocument?.annotationStorage) {
            console.log('[renderSavedAnnotations] No annotationStorage');
            return;
        }

        const storage = pdfDocument.annotationStorage;
        const serializable = storage.serializable;

        // serializable 包含 map, hash, transfers，实际数据在 map 中
        const annotationsMap = serializable.map || new Map();

        console.log('[renderSavedAnnotations] Total annotations in map:', annotationsMap.size);
        console.log('[renderSavedAnnotations] Current page:', pageNumber);

        // 遍历所有标注，渲染当前页的标注
        let renderedCount = 0;
        annotationsMap.forEach((data: any, id: string) => {
            console.log(`[renderSavedAnnotations] Processing annotation ${id}:`, {
                annotationType: data.annotationType,
                pageIndex: data.pageIndex,
                currentPage: pageNumber - 1
            });

            if (data.pageIndex !== pageNumber - 1) return; // 只渲染当前页

            renderedCount++;

            const annotDiv = document.createElement('div');
            annotDiv.className = 'saved-annotation';
            annotDiv.dataset.annotationId = id;
            annotDiv.style.position = 'absolute';

            if (data.annotationType === AnnotationEditorType.INK) {
                // 渲染画笔标注
                annotDiv.style.left = '0';
                annotDiv.style.top = '0';
                annotDiv.style.width = '100%';
                annotDiv.style.height = '100%';
                annotDiv.style.pointerEvents = 'none';

                const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
                svg.style.position = 'absolute';
                svg.style.left = '0';
                svg.style.top = '0';
                svg.style.width = '100%';
                svg.style.height = '100%';
                svg.style.pointerEvents = 'none';

                const paths = data.paths || [];
                paths.forEach((path: any[]) => {
                    const pathElement = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                    const d = `M ${path.map((p: any) => `${p.x},${p.y}`).join(' L ')}`;
                    pathElement.setAttribute('d', d);
                    // RGB 数组转换为字符串
                    const color = data.color
                        ? `rgb(${Math.round(data.color[0] * 255)},${Math.round(data.color[1] * 255)},${Math.round(data.color[2] * 255)})`
                        : 'rgb(255,0,0)';
                    pathElement.setAttribute('stroke', color);
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

                // RGB 数组转换为字符串
                const color = data.color
                    ? `rgb(${Math.round(data.color[0] * 255)},${Math.round(data.color[1] * 255)},${Math.round(data.color[2] * 255)})`
                    : 'rgb(0,0,255)';
                annotDiv.style.border = `2px solid ${color}`;
                annotDiv.style.color = color;
                annotDiv.style.borderRadius = '4px';
                annotDiv.style.fontSize = `${data.fontSize || 16}px`;
                annotDiv.style.pointerEvents = 'auto';
                annotDiv.style.fontWeight = '500';
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
            } else if (data.annotationType === AnnotationEditorType.RECTANGLE) {
                // 渲染矩形标注
                annotDiv.style.left = '0';
                annotDiv.style.top = '0';
                annotDiv.style.width = '100%';
                annotDiv.style.height = '100%';
                annotDiv.style.pointerEvents = 'none';

                const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
                svg.style.position = 'absolute';
                svg.style.left = '0';
                svg.style.top = '0';
                svg.style.width = '100%';
                svg.style.height = '100%';

                const [x1, y1, x2, y2] = data.rect || [0, 0, 100, 100];
                const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                rect.setAttribute('x', String(x1));
                rect.setAttribute('y', String(y1));
                rect.setAttribute('width', String(x2 - x1));
                rect.setAttribute('height', String(y2 - y1));
                const color = data.color
                    ? `rgb(${Math.round(data.color[0] * 255)},${Math.round(data.color[1] * 255)},${Math.round(data.color[2] * 255)})`
                    : 'rgb(255,0,0)';
                rect.setAttribute('stroke', color);
                rect.setAttribute('stroke-width', String(data.thickness || 2));
                rect.setAttribute('fill', 'none');
                svg.appendChild(rect);
                annotDiv.appendChild(svg);
            } else if (data.annotationType === AnnotationEditorType.CIRCLE) {
                // 渲染圆形标注
                annotDiv.style.left = '0';
                annotDiv.style.top = '0';
                annotDiv.style.width = '100%';
                annotDiv.style.height = '100%';
                annotDiv.style.pointerEvents = 'none';

                const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
                svg.style.position = 'absolute';
                svg.style.left = '0';
                svg.style.top = '0';
                svg.style.width = '100%';
                svg.style.height = '100%';

                const [cx, cy] = data.center || [50, 50];
                const [rx, ry] = data.radius || [40, 40];
                const ellipse = document.createElementNS('http://www.w3.org/2000/svg', 'ellipse');
                ellipse.setAttribute('cx', String(cx));
                ellipse.setAttribute('cy', String(cy));
                ellipse.setAttribute('rx', String(rx));
                ellipse.setAttribute('ry', String(ry));
                const color = data.color
                    ? `rgb(${Math.round(data.color[0] * 255)},${Math.round(data.color[1] * 255)},${Math.round(data.color[2] * 255)})`
                    : 'rgb(255,0,0)';
                ellipse.setAttribute('stroke', color);
                ellipse.setAttribute('stroke-width', String(data.thickness || 2));
                ellipse.setAttribute('fill', 'none');
                svg.appendChild(ellipse);
                annotDiv.appendChild(svg);
            } else if (data.annotationType === AnnotationEditorType.ARROW) {
                // 渲染箭头标注
                annotDiv.style.left = '0';
                annotDiv.style.top = '0';
                annotDiv.style.width = '100%';
                annotDiv.style.height = '100%';
                annotDiv.style.pointerEvents = 'none';

                const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
                svg.style.position = 'absolute';
                svg.style.left = '0';
                svg.style.top = '0';
                svg.style.width = '100%';
                svg.style.height = '100%';

                const [x1, y1] = data.start || [0, 0];
                const [x2, y2] = data.end || [100, 100];

                // 箭头线
                const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                line.setAttribute('x1', String(x1));
                line.setAttribute('y1', String(y1));
                line.setAttribute('x2', String(x2));
                line.setAttribute('y2', String(y2));
                const color = data.color
                    ? `rgb(${Math.round(data.color[0] * 255)},${Math.round(data.color[1] * 255)},${Math.round(data.color[2] * 255)})`
                    : 'rgb(255,0,0)';
                line.setAttribute('stroke', color);
                line.setAttribute('stroke-width', String(data.thickness || 2));
                svg.appendChild(line);

                // 箭头头部
                const angle = Math.atan2(y2 - y1, x2 - x1);
                const arrowSize = 15;
                const leftX = x2 - arrowSize * Math.cos(angle - Math.PI / 6);
                const leftY = y2 - arrowSize * Math.sin(angle - Math.PI / 6);
                const rightX = x2 - arrowSize * Math.cos(angle + Math.PI / 6);
                const rightY = y2 - arrowSize * Math.sin(angle + Math.PI / 6);

                const arrowhead = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                arrowhead.setAttribute('d', `M ${leftX},${leftY} L ${x2},${y2} L ${rightX},${rightY}`);
                arrowhead.setAttribute('stroke', color);
                arrowhead.setAttribute('stroke-width', String(data.thickness || 2));
                arrowhead.setAttribute('fill', 'none');
                svg.appendChild(arrowhead);
                annotDiv.appendChild(svg);
            } else if (data.annotationType === AnnotationEditorType.HIGHLIGHT) {
                // 渲染高亮标注
                annotDiv.style.left = '0';
                annotDiv.style.top = '0';
                annotDiv.style.width = '100%';
                annotDiv.style.height = '100%';
                annotDiv.style.pointerEvents = 'none';

                const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
                svg.style.position = 'absolute';
                svg.style.left = '0';
                svg.style.top = '0';
                svg.style.width = '100%';
                svg.style.height = '100%';

                const rects = data.rects || [];
                const color = data.color
                    ? `rgb(${Math.round(data.color[0] * 255)},${Math.round(data.color[1] * 255)},${Math.round(data.color[2] * 255)})`
                    : 'rgb(255,255,0)';

                rects.forEach(([x, y, w, h]: number[]) => {
                    const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                    rect.setAttribute('x', String(x));
                    rect.setAttribute('y', String(y));
                    rect.setAttribute('width', String(w));
                    const height = data.thickness ? data.thickness * 3 : h;
                    rect.setAttribute('height', String(height));
                    rect.setAttribute('fill', color);
                    rect.setAttribute('opacity', '0.4');
                    svg.appendChild(rect);
                });

                annotDiv.appendChild(svg);
            } else if (data.annotationType === AnnotationEditorType.WAVY_LINE) {
                // 渲染波浪线
                const [x1, y1] = data.start || [0, 0];
                const [x2, y2] = data.end || [0, 0];

                annotDiv.style.left = '0';
                annotDiv.style.top = '0';
                annotDiv.style.width = '100%';
                annotDiv.style.height = '100%';
                annotDiv.style.pointerEvents = 'auto';

                const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
                svg.style.position = 'absolute';
                svg.style.left = '0';
                svg.style.top = '0';
                svg.style.width = '100%';
                svg.style.height = '100%';

                const color = data.color
                    ? `rgb(${data.color[0]},${data.color[1]},${data.color[2]})`
                    : 'rgb(255,0,0)';

                const length = Math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2);
                const angle = Math.atan2(y2 - y1, x2 - x1);
                const wavelength = 10;
                const amplitude = (data.thickness || 2) * 2;
                const numWaves = Math.floor(length / wavelength);

                let pathData = `M ${x1} ${y1}`;
                for (let i = 1; i <= numWaves; i++) {
                    const t = i / numWaves;
                    const x = x1 + t * (x2 - x1);
                    const y = y1 + t * (y2 - y1);
                    const offset = Math.sin(i * Math.PI) * amplitude;
                    const perpX = -Math.sin(angle) * offset;
                    const perpY = Math.cos(angle) * offset;
                    pathData += ` L ${x + perpX} ${y + perpY}`;
                }
                pathData += ` L ${x2} ${y2}`;

                const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                path.setAttribute('d', pathData);
                path.setAttribute('fill', 'none');
                path.setAttribute('stroke', color);
                path.setAttribute('stroke-width', String(data.thickness || 2));

                svg.appendChild(path);
                annotDiv.appendChild(svg);
            } else if (data.annotationType === AnnotationEditorType.STRIKETHROUGH) {
                // 渲染删除线
                const [x1, y1] = data.start || [0, 0];
                const [x2, y2] = data.end || [0, 0];

                annotDiv.style.left = '0';
                annotDiv.style.top = '0';
                annotDiv.style.width = '100%';
                annotDiv.style.height = '100%';
                annotDiv.style.pointerEvents = 'auto';

                const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
                svg.style.position = 'absolute';
                svg.style.left = '0';
                svg.style.top = '0';
                svg.style.width = '100%';
                svg.style.height = '100%';

                const color = data.color
                    ? `rgb(${data.color[0]},${data.color[1]},${data.color[2]})`
                    : 'rgb(255,0,0)';

                const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                line.setAttribute('x1', String(x1));
                line.setAttribute('y1', String(y1));
                line.setAttribute('x2', String(x2));
                line.setAttribute('y2', String(y2));
                line.setAttribute('stroke', color);
                line.setAttribute('stroke-width', String(data.thickness || 2));

                svg.appendChild(line);
                annotDiv.appendChild(svg);
            } else {
                console.warn('[renderSavedAnnotations] Unknown annotation type:', data.annotationType);
            }

            annotationLayerDiv.appendChild(annotDiv);
        });

        console.log(`[renderSavedAnnotations] Rendered ${renderedCount} annotations on page ${pageNumber}`);
    }, [pdfDocument, pageNumber]);

    // 将 renderSavedAnnotations 存储到 ref 中供 saveAndRefresh 使用
    useEffect(() => {
        renderSavedAnnotationsRef.current = renderSavedAnnotations;
    }, [renderSavedAnnotations]);

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
        editorContainer.style.pointerEvents = 'auto'; // 默认允许交互

        // 根据当前模式设置编辑器行为
        if (editorMode === AnnotationEditorType.INK) {
            enableInkEditor(editorContainer);
        } else if (editorMode === AnnotationEditorType.FREETEXT) {
            enableFreeTextEditor(editorContainer);
        } else if (editorMode === AnnotationEditorType.STAMP) {
            enableStampEditor(editorContainer);
        } else if (editorMode === AnnotationEditorType.RECTANGLE) {
            enableRectangleEditor(editorContainer);
        } else if (editorMode === AnnotationEditorType.CIRCLE) {
            enableCircleEditor(editorContainer);
        } else if (editorMode === AnnotationEditorType.ARROW) {
            enableArrowEditor(editorContainer);
        } else if (editorMode === AnnotationEditorType.ERASER) {
            // 橡皮擦模式
            const annotationLayerDiv = annotationLayerRef.current;
            if (annotationLayerDiv) {
                enableEraserMode(annotationLayerDiv);
            }
            editorContainer.classList.add('disabled');
            editorContainer.style.cursor = 'not-allowed';
        } else if (editorMode === AnnotationEditorType.HIGHLIGHT) {
            // 高亮模式 - 文本选择高亮
            const textLayerDiv = textLayerRef.current;
            if (textLayerDiv) {
                enableHighlightMode(textLayerDiv);
            }
            editorContainer.classList.add('disabled');
            editorContainer.style.pointerEvents = 'none';
        } else if (editorMode === AnnotationEditorType.WAVY_LINE) {
            enableWavyLineEditor(editorContainer);
        } else if (editorMode === AnnotationEditorType.STRIKETHROUGH) {
            enableStrikethroughEditor(editorContainer);
        } else if (editorMode === AnnotationEditorType.LASSO) {
            const annotationLayerDiv = annotationLayerRef.current;
            if (annotationLayerDiv) {
                enableLassoMode(annotationLayerDiv);
            }
            editorContainer.classList.add('disabled');
        } else if (editorMode === AnnotationEditorType.NONE) {
            // 选择模式 - 启用标注选择和删除，允许文字选择
            const annotationLayerDiv = annotationLayerRef.current;
            if (annotationLayerDiv) {
                enableSelectMode(annotationLayerDiv);
            }
            editorContainer.classList.add('disabled');
            editorContainer.style.pointerEvents = 'none'; // 不阻挡文字选择
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
    }, [pdfDocument, saveAndRefresh]);

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
                    saveAndRefresh(pdfDocument.annotationStorage.serializable);
                }

                currentPath = [];
                svg.innerHTML = '';
            }
        };

        container.addEventListener('mousedown', handleMouseDown);
        container.addEventListener('mousemove', handleMouseMove);
        container.addEventListener('mouseup', handleMouseUp);
    }, [pdfDocument, pageNumber, saveAndRefresh, annotationColor, annotationThickness]);

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
            input.style.fontSize = `${fontSize}px`;
            input.style.padding = '4px 8px';
            input.style.border = `2px solid ${annotationColor}`;
            input.style.borderRadius = '4px';
            input.style.backgroundColor = '#ffffff';
            input.style.color = annotationColor;
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
                    const textWidth = text.length * (fontSize * 0.6);
                    const textHeight = fontSize * 1.5;
                    const annotationData = {
                        annotationType: AnnotationEditorType.FREETEXT,
                        pageIndex: pageNumber - 1,
                        rect: [x, y, x + textWidth, y + textHeight],
                        contents: text,
                        color: hexToRgb(annotationColor),
                        fontSize: fontSize,
                    };

                    console.log('[FreeTextEditor] Created annotation:', annotationData);

                    if (pdfDocument?.annotationStorage) {
                        const id = `freetext_${Date.now()}_${Math.random()}`;
                        pdfDocument.annotationStorage.setValue(id, annotationData);
                        saveAndRefresh(pdfDocument.annotationStorage.serializable);
                        
                        // 自动创建书签
                        createBookmarkFromNote({ id, ...annotationData });
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
    }, [pdfDocument, pageNumber, saveAndRefresh, annotationColor, fontSize]);

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
                        saveAndRefresh(pdfDocument.annotationStorage.serializable);
                    }
                };
                reader.readAsDataURL(file);
            };

            input.click();
        };

        container.addEventListener('click', handleClick);
    }, [pdfDocument, pageNumber, saveAndRefresh]);

    /**
     * 启用矩形编辑器 - 动态绘制矩形
     */
    const enableRectangleEditor = useCallback((container: HTMLElement) => {
        let isDrawing = false;
        let startX = 0, startY = 0;
        let previewRect: SVGRectElement | null = null;
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.style.width = '100%';
        svg.style.height = '100%';
        svg.style.position = 'absolute';
        svg.style.pointerEvents = 'auto';
        container.appendChild(svg);

        const hexToRgb = (hex: string): [number, number, number] => {
            const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
            return result
                ? [parseInt(result[1], 16) / 255, parseInt(result[2], 16) / 255, parseInt(result[3], 16) / 255]
                : [1, 0, 0];
        };

        const handleMouseDown = (e: MouseEvent) => {
            isDrawing = true;
            const rect = container.getBoundingClientRect();
            startX = e.clientX - rect.left;
            startY = e.clientY - rect.top;
        };

        const handleMouseMove = (e: MouseEvent) => {
            if (!isDrawing) return;
            const rect = container.getBoundingClientRect();
            const currentX = e.clientX - rect.left;
            const currentY = e.clientY - rect.top;

            const x = Math.min(startX, currentX);
            const y = Math.min(startY, currentY);
            const width = Math.abs(currentX - startX);
            const height = Math.abs(currentY - startY);

            if (previewRect) {
                svg.removeChild(previewRect);
            }

            previewRect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            previewRect.setAttribute('x', String(x));
            previewRect.setAttribute('y', String(y));
            previewRect.setAttribute('width', String(width));
            previewRect.setAttribute('height', String(height));
            previewRect.setAttribute('stroke', annotationColor);
            previewRect.setAttribute('stroke-width', String(annotationThickness));
            previewRect.setAttribute('fill', 'none');
            svg.appendChild(previewRect);
        };

        const handleMouseUp = async (e: MouseEvent) => {
            if (!isDrawing) return;
            isDrawing = false;

            const rect = container.getBoundingClientRect();
            const endX = e.clientX - rect.left;
            const endY = e.clientY - rect.top;

            const x = Math.min(startX, endX);
            const y = Math.min(startY, endY);
            const width = Math.abs(endX - startX);
            const height = Math.abs(endY - startY);

            if (width > 5 && height > 5) {
                const annotationData = {
                    annotationType: AnnotationEditorType.RECTANGLE,
                    pageIndex: pageNumber - 1,
                    rect: [x, y, x + width, y + height],
                    color: hexToRgb(annotationColor),
                    thickness: annotationThickness,
                };

                console.log('[RectangleEditor] Created annotation:', annotationData);

                if (pdfDocument?.annotationStorage) {
                    const id = `rectangle_${Date.now()}_${Math.random()}`;
                    pdfDocument.annotationStorage.setValue(id, annotationData);
                    saveAndRefresh(pdfDocument.annotationStorage.serializable);
                }
            }

            if (previewRect) {
                svg.removeChild(previewRect);
                previewRect = null;
            }
        };

        container.addEventListener('mousedown', handleMouseDown);
        container.addEventListener('mousemove', handleMouseMove);
        container.addEventListener('mouseup', handleMouseUp);
    }, [pdfDocument, pageNumber, saveAndRefresh, annotationColor, annotationThickness]);

    /**
     * 启用圆形编辑器 - 动态绘制圆形
     */
    const enableCircleEditor = useCallback((container: HTMLElement) => {
        let isDrawing = false;
        let startX = 0, startY = 0;
        let previewCircle: SVGEllipseElement | null = null;
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.style.width = '100%';
        svg.style.height = '100%';
        svg.style.position = 'absolute';
        svg.style.pointerEvents = 'auto';
        container.appendChild(svg);

        const hexToRgb = (hex: string): [number, number, number] => {
            const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
            return result
                ? [parseInt(result[1], 16) / 255, parseInt(result[2], 16) / 255, parseInt(result[3], 16) / 255]
                : [1, 0, 0];
        };

        const handleMouseDown = (e: MouseEvent) => {
            isDrawing = true;
            const rect = container.getBoundingClientRect();
            startX = e.clientX - rect.left;
            startY = e.clientY - rect.top;
        };

        const handleMouseMove = (e: MouseEvent) => {
            if (!isDrawing) return;
            const rect = container.getBoundingClientRect();
            const currentX = e.clientX - rect.left;
            const currentY = e.clientY - rect.top;

            const cx = (startX + currentX) / 2;
            const cy = (startY + currentY) / 2;
            const rx = Math.abs(currentX - startX) / 2;
            const ry = Math.abs(currentY - startY) / 2;

            if (previewCircle) {
                svg.removeChild(previewCircle);
            }

            previewCircle = document.createElementNS('http://www.w3.org/2000/svg', 'ellipse');
            previewCircle.setAttribute('cx', String(cx));
            previewCircle.setAttribute('cy', String(cy));
            previewCircle.setAttribute('rx', String(rx));
            previewCircle.setAttribute('ry', String(ry));
            previewCircle.setAttribute('stroke', annotationColor);
            previewCircle.setAttribute('stroke-width', String(annotationThickness));
            previewCircle.setAttribute('fill', 'none');
            svg.appendChild(previewCircle);
        };

        const handleMouseUp = async (e: MouseEvent) => {
            if (!isDrawing) return;
            isDrawing = false;

            const rect = container.getBoundingClientRect();
            const endX = e.clientX - rect.left;
            const endY = e.clientY - rect.top;

            const cx = (startX + endX) / 2;
            const cy = (startY + endY) / 2;
            const rx = Math.abs(endX - startX) / 2;
            const ry = Math.abs(endY - startY) / 2;

            if (rx > 5 && ry > 5) {
                const annotationData = {
                    annotationType: AnnotationEditorType.CIRCLE,
                    pageIndex: pageNumber - 1,
                    center: [cx, cy],
                    radius: [rx, ry],
                    color: hexToRgb(annotationColor),
                    thickness: annotationThickness,
                };

                console.log('[CircleEditor] Created annotation:', annotationData);

                if (pdfDocument?.annotationStorage) {
                    const id = `circle_${Date.now()}_${Math.random()}`;
                    pdfDocument.annotationStorage.setValue(id, annotationData);
                    saveAndRefresh(pdfDocument.annotationStorage.serializable);
                }
            }

            if (previewCircle) {
                svg.removeChild(previewCircle);
                previewCircle = null;
            }
        };

        container.addEventListener('mousedown', handleMouseDown);
        container.addEventListener('mousemove', handleMouseMove);
        container.addEventListener('mouseup', handleMouseUp);
    }, [pdfDocument, pageNumber, saveAndRefresh, annotationColor, annotationThickness]);

    /**
     * 启用箭头编辑器 - 动态绘制箭头
     */
    const enableArrowEditor = useCallback((container: HTMLElement) => {
        let isDrawing = false;
        let startX = 0, startY = 0;
        let previewGroup: SVGGElement | null = null;
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.style.width = '100%';
        svg.style.height = '100%';
        svg.style.position = 'absolute';
        svg.style.pointerEvents = 'auto';
        container.appendChild(svg);

        const hexToRgb = (hex: string): [number, number, number] => {
            const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
            return result
                ? [parseInt(result[1], 16) / 255, parseInt(result[2], 16) / 255, parseInt(result[3], 16) / 255]
                : [1, 0, 0];
        };

        const createArrowhead = (x1: number, y1: number, x2: number, y2: number): string => {
            const angle = Math.atan2(y2 - y1, x2 - x1);
            const arrowSize = 15;
            const leftX = x2 - arrowSize * Math.cos(angle - Math.PI / 6);
            const leftY = y2 - arrowSize * Math.sin(angle - Math.PI / 6);
            const rightX = x2 - arrowSize * Math.cos(angle + Math.PI / 6);
            const rightY = y2 - arrowSize * Math.sin(angle + Math.PI / 6);
            return `M ${leftX},${leftY} L ${x2},${y2} L ${rightX},${rightY}`;
        };

        const handleMouseDown = (e: MouseEvent) => {
            isDrawing = true;
            const rect = container.getBoundingClientRect();
            startX = e.clientX - rect.left;
            startY = e.clientY - rect.top;
        };

        const handleMouseMove = (e: MouseEvent) => {
            if (!isDrawing) return;
            const rect = container.getBoundingClientRect();
            const currentX = e.clientX - rect.left;
            const currentY = e.clientY - rect.top;

            if (previewGroup) {
                svg.removeChild(previewGroup);
            }

            previewGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');

            // 箭头线
            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', String(startX));
            line.setAttribute('y1', String(startY));
            line.setAttribute('x2', String(currentX));
            line.setAttribute('y2', String(currentY));
            line.setAttribute('stroke', annotationColor);
            line.setAttribute('stroke-width', String(annotationThickness));
            previewGroup.appendChild(line);

            // 箭头头部
            const arrowhead = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            arrowhead.setAttribute('d', createArrowhead(startX, startY, currentX, currentY));
            arrowhead.setAttribute('stroke', annotationColor);
            arrowhead.setAttribute('stroke-width', String(annotationThickness));
            arrowhead.setAttribute('fill', 'none');
            previewGroup.appendChild(arrowhead);

            svg.appendChild(previewGroup);
        };

        const handleMouseUp = async (e: MouseEvent) => {
            if (!isDrawing) return;
            isDrawing = false;

            const rect = container.getBoundingClientRect();
            const endX = e.clientX - rect.left;
            const endY = e.clientY - rect.top;

            const distance = Math.sqrt((endX - startX) ** 2 + (endY - startY) ** 2);

            if (distance > 10) {
                const annotationData = {
                    annotationType: AnnotationEditorType.ARROW,
                    pageIndex: pageNumber - 1,
                    start: [startX, startY],
                    end: [endX, endY],
                    color: hexToRgb(annotationColor),
                    thickness: annotationThickness,
                };

                console.log('[ArrowEditor] Created annotation:', annotationData);

                if (pdfDocument?.annotationStorage) {
                    const id = `arrow_${Date.now()}_${Math.random()}`;
                    pdfDocument.annotationStorage.setValue(id, annotationData);
                    saveAndRefresh(pdfDocument.annotationStorage.serializable);
                }
            }

            if (previewGroup) {
                svg.removeChild(previewGroup);
                previewGroup = null;
            }
        };

        container.addEventListener('mousedown', handleMouseDown);
        container.addEventListener('mousemove', handleMouseMove);
        container.addEventListener('mouseup', handleMouseUp);
    }, [pdfDocument, pageNumber, saveAndRefresh, annotationColor, annotationThickness]);

    /**
     * 橡皮擦编辑器 - 改进版：显示橡皮擦光标，碰到即删除
     */
    const enableEraserMode = useCallback((container: HTMLElement) => {
        let eraserCursor: HTMLDivElement | null = null;
        const eraserSize = annotationThickness * 10; // 橡皮擦大小根据粗细参数

        // 创建橡皮擦光标
        const createEraserCursor = () => {
            const cursor = document.createElement('div');
            cursor.style.position = 'absolute';
            cursor.style.width = `${eraserSize}px`;
            cursor.style.height = `${eraserSize}px`;
            cursor.style.borderRadius = '50%';
            cursor.style.border = '2px solid #ff0000';
            cursor.style.backgroundColor = 'rgba(255, 0, 0, 0.1)';
            cursor.style.pointerEvents = 'none';
            cursor.style.zIndex = '1000';
            cursor.style.transform = 'translate(-50%, -50%)';
            container.appendChild(cursor);
            return cursor;
        };

        eraserCursor = createEraserCursor();

        const checkCollision = (x: number, y: number): HTMLElement[] => {
            const annotations = container.querySelectorAll('.saved-annotation');
            const collided: HTMLElement[] = [];

            annotations.forEach((annot) => {
                const rect = annot.getBoundingClientRect();
                const containerRect = container.getBoundingClientRect();
                const relativeRect = {
                    left: rect.left - containerRect.left,
                    right: rect.right - containerRect.left,
                    top: rect.top - containerRect.top,
                    bottom: rect.bottom - containerRect.top
                };

                const halfSize = eraserSize / 2;
                if (x + halfSize > relativeRect.left && x - halfSize < relativeRect.right &&
                    y + halfSize > relativeRect.top && y - halfSize < relativeRect.bottom) {
                    collided.push(annot as HTMLElement);
                }
            });

            return collided;
        };

        let isErasing = false;
        const erasedIds = new Set<string>();

        const handleMouseMove = (e: MouseEvent) => {
            const rect = container.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            if (eraserCursor) {
                eraserCursor.style.left = `${x}px`;
                eraserCursor.style.top = `${y}px`;
            }

            if (isErasing) {
                const collided = checkCollision(x, y);
                collided.forEach(annotation => {
                    const id = annotation.dataset.annotationId;
                    if (id && !erasedIds.has(id)) {
                        erasedIds.add(id);
                        annotation.classList.add('erasing');
                    }
                });
            }
        };

        const handleMouseDown = () => {
            isErasing = true;
            erasedIds.clear();
        };

        const handleMouseUp = async () => {
            if (isErasing && erasedIds.size > 0 && pdfDocument?.annotationStorage) {
                const storage = pdfDocument.annotationStorage;
                const serializable = storage.serializable;
                const annotationsMap = serializable.map || new Map();

                // 删除所有碰到的标注
                erasedIds.forEach(id => {
                    const element = container.querySelector(`[data-annotation-id="${id}"]`);
                    if (element) {
                        element.remove();
                    }
                    annotationsMap.delete(id);
                });

                // 保存更新
                await saveAnnotations(serializable);
                console.log('[Eraser] Erased', erasedIds.size, 'annotations');
            }

            isErasing = false;
            erasedIds.clear();
        };

        const handleMouseLeave = () => {
            if (eraserCursor) {
                eraserCursor.style.display = 'none';
            }
        };

        const handleMouseEnter = () => {
            if (eraserCursor) {
                eraserCursor.style.display = 'block';
            }
        };

        container.addEventListener('mousemove', handleMouseMove);
        container.addEventListener('mousedown', handleMouseDown);
        container.addEventListener('mouseup', handleMouseUp);
        container.addEventListener('mouseleave', handleMouseLeave);
        container.addEventListener('mouseenter', handleMouseEnter);

        return () => {
            container.removeEventListener('mousemove', handleMouseMove);
            container.removeEventListener('mousedown', handleMouseDown);
            container.removeEventListener('mouseup', handleMouseUp);
            container.removeEventListener('mouseleave', handleMouseLeave);
            container.removeEventListener('mouseenter', handleMouseEnter);
            if (eraserCursor && eraserCursor.parentNode) {
                eraserCursor.parentNode.removeChild(eraserCursor);
            }
        };
    }, [pdfDocument, saveAnnotations, annotationThickness]);

    /**
     * 高亮模式 - 文本选择自动高亮
     */
    const enableHighlightMode = useCallback((textLayerDiv: HTMLElement) => {
        const hexToRgb = (hex: string): [number, number, number] => {
            const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
            return result ? [
                parseInt(result[1], 16),
                parseInt(result[2], 16),
                parseInt(result[3], 16)
            ] : [255, 0, 0];
        };

        const handleTextSelection = async () => {
            const selection = window.getSelection();
            if (!selection || selection.isCollapsed || selection.rangeCount === 0) return;

            try {
                const range = selection.getRangeAt(0);
                const rects = range.getClientRects();

                if (rects.length === 0) return;

                // 转换为相对页面的坐标
                const containerRect = textLayerDiv.getBoundingClientRect();
                const pageRects = Array.from(rects).map(rect => [
                    rect.left - containerRect.left,
                    rect.top - containerRect.top,
                    rect.width,
                    rect.height
                ]);

                // 生成唯一ID
                const highlightId = `highlight-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

                // 创建高亮标注数据
                const highlightData = {
                    annotationType: AnnotationEditorType.HIGHLIGHT,
                    color: hexToRgb(annotationColor),
                    thickness: annotationThickness,
                    rects: pageRects,
                    pageIndex: pageNumber - 1,
                    rect: [
                        Math.min(...pageRects.map(r => r[0])),
                        Math.min(...pageRects.map(r => r[1])),
                        Math.max(...pageRects.map(r => r[0] + r[2])),
                        Math.max(...pageRects.map(r => r[1] + r[3]))
                    ]
                };

                if (pdfDocument?.annotationStorage) {
                    const storage = pdfDocument.annotationStorage;
                    const serializable = storage.serializable;
                    const annotationsMap = serializable.map || new Map();

                    // 添加到storage
                    annotationsMap.set(highlightId, highlightData);

                    // 保存并刷新
                    await saveAndRefresh(serializable);
                }

                // 清除选择
                selection.removeAllRanges();
            } catch (error) {
                console.error('[Highlight] Error creating highlight:', error);
            }
        };

        textLayerDiv.addEventListener('mouseup', handleTextSelection);

        return () => {
            textLayerDiv.removeEventListener('mouseup', handleTextSelection);
        };
    }, [annotationColor, annotationThickness, pageNumber, pdfDocument, saveAndRefresh]);

    /**
     * 波浪线编辑器
     */
    const enableWavyLineEditor = useCallback((container: HTMLElement) => {
        const hexToRgb = (hex: string): [number, number, number] => {
            const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
            return result ? [
                parseInt(result[1], 16),
                parseInt(result[2], 16),
                parseInt(result[3], 16)
            ] : [255, 0, 0];
        };

        let isDrawing = false;
        let startX = 0, startY = 0, endX = 0, endY = 0;
        let tempLine: SVGElement | null = null;

        const createWavyPath = (x1: number, y1: number, x2: number, y2: number, amplitude: number = 3): string => {
            const length = Math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2);
            const angle = Math.atan2(y2 - y1, x2 - x1);
            const wavelength = 10;
            const numWaves = Math.floor(length / wavelength);

            let path = `M ${x1} ${y1}`;
            for (let i = 0; i <= numWaves; i++) {
                const t = i / numWaves;
                const x = x1 + t * (x2 - x1);
                const y = y1 + t * (y2 - y1);
                const offset = Math.sin(i * Math.PI) * amplitude;
                const perpX = -Math.sin(angle) * offset;
                const perpY = Math.cos(angle) * offset;
                path += ` Q ${x + perpX} ${y + perpY} ${x + (x2 - x1) * wavelength / (2 * length)} ${y + (y2 - y1) * wavelength / (2 * length)}`;
            }

            return path;
        };

        const handleMouseDown = (e: MouseEvent) => {
            const rect = container.getBoundingClientRect();
            startX = e.clientX - rect.left;
            startY = e.clientY - rect.top;
            isDrawing = true;
        };

        const handleMouseMove = (e: MouseEvent) => {
            if (!isDrawing) return;

            const rect = container.getBoundingClientRect();
            endX = e.clientX - rect.left;
            endY = e.clientY - rect.top;

            if (tempLine) tempLine.remove();

            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.style.position = 'absolute';
            svg.style.top = '0';
            svg.style.left = '0';
            svg.style.width = '100%';
            svg.style.height = '100%';
            svg.style.pointerEvents = 'none';

            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.setAttribute('d', createWavyPath(startX, startY, endX, endY, annotationThickness * 2));
            path.setAttribute('fill', 'none');
            path.setAttribute('stroke', annotationColor);
            path.setAttribute('stroke-width', String(annotationThickness));

            svg.appendChild(path);
            container.appendChild(svg);
            tempLine = svg;
        };

        const handleMouseUp = async (e: MouseEvent) => {
            if (!isDrawing) return;
            isDrawing = false;

            const rect = container.getBoundingClientRect();
            endX = e.clientX - rect.left;
            endY = e.clientY - rect.top;

            if (tempLine) tempLine.remove();

            if (Math.abs(endX - startX) > 5 || Math.abs(endY - startY) > 5) {
                const wavyId = `wavy-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
                const wavyData = {
                    annotationType: AnnotationEditorType.WAVY_LINE,
                    color: hexToRgb(annotationColor),
                    thickness: annotationThickness,
                    start: [startX, startY],
                    end: [endX, endY],
                    pageIndex: pageNumber - 1,
                    rect: [
                        Math.min(startX, endX),
                        Math.min(startY, endY),
                        Math.max(startX, endX),
                        Math.max(startY, endY)
                    ]
                };

                if (pdfDocument?.annotationStorage) {
                    const storage = pdfDocument.annotationStorage;
                    const serializable = storage.serializable;
                    const annotationsMap = serializable.map || new Map();
                    annotationsMap.set(wavyId, wavyData);
                    await saveAndRefresh(serializable);
                }
            }
        };

        container.addEventListener('mousedown', handleMouseDown);
        container.addEventListener('mousemove', handleMouseMove);
        container.addEventListener('mouseup', handleMouseUp);

        return () => {
            container.removeEventListener('mousedown', handleMouseDown);
            container.removeEventListener('mousemove', handleMouseMove);
            container.removeEventListener('mouseup', handleMouseUp);
            if (tempLine) tempLine.remove();
        };
    }, [annotationColor, annotationThickness, pageNumber, pdfDocument, saveAndRefresh]);

    /**
     * 删除线编辑器
     */
    const enableStrikethroughEditor = useCallback((container: HTMLElement) => {
        const hexToRgb = (hex: string): [number, number, number] => {
            const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
            return result ? [
                parseInt(result[1], 16),
                parseInt(result[2], 16),
                parseInt(result[3], 16)
            ] : [255, 0, 0];
        };

        let isDrawing = false;
        let startX = 0, startY = 0, endX = 0, endY = 0;
        let tempLine: SVGElement | null = null;

        const handleMouseDown = (e: MouseEvent) => {
            const rect = container.getBoundingClientRect();
            startX = e.clientX - rect.left;
            startY = e.clientY - rect.top;
            isDrawing = true;
        };

        const handleMouseMove = (e: MouseEvent) => {
            if (!isDrawing) return;

            const rect = container.getBoundingClientRect();
            endX = e.clientX - rect.left;
            endY = e.clientY - rect.top;

            if (tempLine) tempLine.remove();

            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.style.position = 'absolute';
            svg.style.top = '0';
            svg.style.left = '0';
            svg.style.width = '100%';
            svg.style.height = '100%';
            svg.style.pointerEvents = 'none';

            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', String(startX));
            line.setAttribute('y1', String(startY));
            line.setAttribute('x2', String(endX));
            line.setAttribute('y2', String(endY));
            line.setAttribute('stroke', annotationColor);
            line.setAttribute('stroke-width', String(annotationThickness));

            svg.appendChild(line);
            container.appendChild(svg);
            tempLine = svg;
        };

        const handleMouseUp = async (e: MouseEvent) => {
            if (!isDrawing) return;
            isDrawing = false;

            const rect = container.getBoundingClientRect();
            endX = e.clientX - rect.left;
            endY = e.clientY - rect.top;

            if (tempLine) tempLine.remove();

            if (Math.abs(endX - startX) > 5 || Math.abs(endY - startY) > 5) {
                const strikeId = `strike-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
                const strikeData = {
                    annotationType: AnnotationEditorType.STRIKETHROUGH,
                    color: hexToRgb(annotationColor),
                    thickness: annotationThickness,
                    start: [startX, startY],
                    end: [endX, endY],
                    pageIndex: pageNumber - 1,
                    rect: [
                        Math.min(startX, endX),
                        Math.min(startY, endY),
                        Math.max(startX, endX),
                        Math.max(startY, endY)
                    ]
                };

                if (pdfDocument?.annotationStorage) {
                    const storage = pdfDocument.annotationStorage;
                    const serializable = storage.serializable;
                    const annotationsMap = serializable.map || new Map();
                    annotationsMap.set(strikeId, strikeData);
                    await saveAndRefresh(serializable);
                }
            }
        };

        container.addEventListener('mousedown', handleMouseDown);
        container.addEventListener('mousemove', handleMouseMove);
        container.addEventListener('mouseup', handleMouseUp);

        return () => {
            container.removeEventListener('mousedown', handleMouseDown);
            container.removeEventListener('mousemove', handleMouseMove);
            container.removeEventListener('mouseup', handleMouseUp);
            if (tempLine) tempLine.remove();
        };
    }, [annotationColor, annotationThickness, pageNumber, pdfDocument, saveAndRefresh]);

    /**
     * 套索选择模式 - 框选多个标注
     */
    const enableLassoMode = useCallback((container: HTMLElement) => {
        let isDrawing = false;
        let lassoPath: Array<{ x: number, y: number }> = [];
        let lassoSvg: SVGElement | null = null;
        let selectedAnnotations = new Set<string>();

        const handleMouseDown = (e: MouseEvent) => {
            const rect = container.getBoundingClientRect();
            lassoPath = [{
                x: e.clientX - rect.left,
                y: e.clientY - rect.top
            }];
            isDrawing = true;
            selectedAnnotations.clear();
        };

        const handleMouseMove = (e: MouseEvent) => {
            if (!isDrawing) return;

            const rect = container.getBoundingClientRect();
            lassoPath.push({
                x: e.clientX - rect.left,
                y: e.clientY - rect.top
            });

            if (lassoSvg) lassoSvg.remove();

            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.style.position = 'absolute';
            svg.style.top = '0';
            svg.style.left = '0';
            svg.style.width = '100%';
            svg.style.height = '100%';
            svg.style.pointerEvents = 'none';

            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            const pathData = lassoPath.reduce((acc, point, i) =>
                acc + (i === 0 ? `M ${point.x} ${point.y}` : ` L ${point.x} ${point.y}`), '');
            path.setAttribute('d', pathData);
            path.setAttribute('fill', 'rgba(128, 0, 128, 0.1)');
            path.setAttribute('stroke', '#800080');
            path.setAttribute('stroke-width', '2');
            path.setAttribute('stroke-dasharray', '5,5');

            svg.appendChild(path);
            container.appendChild(svg);
            lassoSvg = svg;
        };

        const pointInPolygon = (point: { x: number, y: number }, polygon: Array<{ x: number, y: number }>) => {
            let inside = false;
            for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
                const xi = polygon[i].x, yi = polygon[i].y;
                const xj = polygon[j].x, yj = polygon[j].y;
                const intersect = ((yi > point.y) !== (yj > point.y))
                    && (point.x < (xj - xi) * (point.y - yi) / (yj - yi) + xi);
                if (intersect) inside = !inside;
            }
            return inside;
        };

        const handleMouseUp = async () => {
            if (!isDrawing) return;
            isDrawing = false;

            if (lassoSvg) lassoSvg.remove();

            if (lassoPath.length < 3) {
                lassoPath = [];
                return;
            }

            // 检测套索内的标注
            const annotations = container.querySelectorAll('.saved-annotation');
            annotations.forEach((annot) => {
                const rect = annot.getBoundingClientRect();
                const containerRect = container.getBoundingClientRect();
                const center = {
                    x: rect.left - containerRect.left + rect.width / 2,
                    y: rect.top - containerRect.top + rect.height / 2
                };

                if (pointInPolygon(center, lassoPath)) {
                    const id = (annot as HTMLElement).dataset.annotationId;
                    if (id) {
                        selectedAnnotations.add(id);
                        (annot as HTMLElement).style.outline = '3px solid #800080';
                        (annot as HTMLElement).style.outlineOffset = '2px';
                    }
                }
            });

            lassoPath = [];
            console.log('[Lasso] Selected annotations:', selectedAnnotations);
        };

        // 键盘Delete删除选中的标注
        const handleKeyDown = async (e: KeyboardEvent) => {
            if ((e.key === 'Delete' || e.key === 'Backspace') && selectedAnnotations.size > 0) {
                if (pdfDocument?.annotationStorage) {
                    const storage = pdfDocument.annotationStorage;
                    const serializable = storage.serializable;
                    const annotationsMap = serializable.map || new Map();

                    selectedAnnotations.forEach(id => {
                        const element = container.querySelector(`[data-annotation-id="${id}"]`);
                        if (element) element.remove();
                        annotationsMap.delete(id);
                    });

                    await saveAnnotations(serializable);
                    selectedAnnotations.clear();
                    console.log('[Lasso] Deleted selected annotations');
                }
            }
        };

        container.addEventListener('mousedown', handleMouseDown);
        container.addEventListener('mousemove', handleMouseMove);
        container.addEventListener('mouseup', handleMouseUp);
        document.addEventListener('keydown', handleKeyDown);

        return () => {
            container.removeEventListener('mousedown', handleMouseDown);
            container.removeEventListener('mousemove', handleMouseMove);
            container.removeEventListener('mouseup', handleMouseUp);
            document.removeEventListener('keydown', handleKeyDown);
            if (lassoSvg) lassoSvg.remove();
            selectedAnnotations.forEach(id => {
                const element = container.querySelector(`[data-annotation-id="${id}"]`);
                if (element) (element as HTMLElement).style.outline = '';
            });
        };
    }, [pdfDocument, saveAnnotations]);

    /**
     * 渲染书签可视化层 - 在PDF旁边显示书签图标
     */
    const renderBookmarkLayer = useCallback((viewport: any) => {
        const bookmarkLayerDiv = bookmarkLayerRef.current;
        if (!bookmarkLayerDiv) return;

        bookmarkLayerDiv.innerHTML = '';
        bookmarkLayerDiv.style.width = `${viewport.width}px`;
        bookmarkLayerDiv.style.height = `${viewport.height}px`;

        // 过滤当前页的书签
        const pageBookmarks = bookmarks.filter(b => b.page_number === pageNumber);

        pageBookmarks.forEach((bookmark, index) => {
            const bookmarkIcon = document.createElement('div');
            bookmarkIcon.className = 'bookmark-icon';
            bookmarkIcon.dataset.bookmarkId = bookmark.id;
            bookmarkIcon.style.position = 'absolute';
            bookmarkIcon.style.right = '-40px';
            bookmarkIcon.style.top = `${20 + index * 50}px`;
            bookmarkIcon.style.width = '32px';
            bookmarkIcon.style.height = '32px';
            bookmarkIcon.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
            bookmarkIcon.style.borderRadius = '50%';
            bookmarkIcon.style.display = 'flex';
            bookmarkIcon.style.alignItems = 'center';
            bookmarkIcon.style.justifyContent = 'center';
            bookmarkIcon.style.cursor = 'pointer';
            bookmarkIcon.style.boxShadow = '0 2px 8px rgba(0,0,0,0.2)';
            bookmarkIcon.style.transition = 'all 0.3s ease';
            bookmarkIcon.style.zIndex = '100';
            bookmarkIcon.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="white"><path d="M17 3H7c-1.1 0-2 .9-2 2v16l7-3 7 3V5c0-1.1-.9-2-2-2z"/></svg>';
            
            // 悬停效果
            bookmarkIcon.addEventListener('mouseenter', () => {
                bookmarkIcon.style.transform = 'scale(1.2)';
                bookmarkIcon.style.boxShadow = '0 4px 12px rgba(102,126,234,0.4)';
                
                // 显示书签标题提示
                const tooltip = document.createElement('div');
                tooltip.className = 'bookmark-tooltip';
                tooltip.style.position = 'absolute';
                tooltip.style.right = '40px';
                tooltip.style.top = '0';
                tooltip.style.background = 'rgba(0,0,0,0.8)';
                tooltip.style.color = 'white';
                tooltip.style.padding = '8px 12px';
                tooltip.style.borderRadius = '4px';
                tooltip.style.fontSize = '12px';
                tooltip.style.whiteSpace = 'nowrap';
                tooltip.style.maxWidth = '200px';
                tooltip.style.overflow = 'hidden';
                tooltip.style.textOverflow = 'ellipsis';
                tooltip.textContent = bookmark.title || '书签';
                bookmarkIcon.appendChild(tooltip);
            });

            bookmarkIcon.addEventListener('mouseleave', () => {
                bookmarkIcon.style.transform = 'scale(1)';
                bookmarkIcon.style.boxShadow = '0 2px 8px rgba(0,0,0,0.2)';
                const tooltip = bookmarkIcon.querySelector('.bookmark-tooltip');
                if (tooltip) tooltip.remove();
            });

            // 点击跳转
            bookmarkIcon.addEventListener('click', () => {
                if (onJumpToBookmark) {
                    onJumpToBookmark(bookmark.id);
                }
            });

            bookmarkLayerDiv.appendChild(bookmarkIcon);
        });
    }, [bookmarks, pageNumber, onJumpToBookmark]);

    /**
     * 便笺自动创建书签
     */
    const createBookmarkFromNote = useCallback(async (noteData: any) => {
        if (!onCreateBookmark) return;

        try {
            const bookmarkData = {
                document_id: documentId,
                page_number: pageNumber,
                title: noteData.value || '便笺',
                content: noteData.value,
                metadata: {
                    annotation_id: noteData.id,
                    annotation_type: 'FREETEXT',
                    position: noteData.rect,
                    created_from_annotation: true
                }
            };

            await onCreateBookmark(bookmarkData);
            console.log('[PDFViewerNative] Created bookmark from note:', bookmarkData);
        } catch (error) {
            console.error('[PDFViewerNative] Failed to create bookmark from note:', error);
        }
    }, [documentId, pageNumber, onCreateBookmark]);

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
            saveAndRefresh(annotations);
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
    }, [pdfDocument, saveAndRefresh]);

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
                fontSize={fontSize}
                onFontSizeChange={setFontSize}
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

                    {/* 书签可视化层 - AI书签图标 */}
                    <div
                        ref={bookmarkLayerRef}
                        className="absolute top-0 left-0 bookmarkLayer"
                        style={{ pointerEvents: 'none' }}
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
                    {editorMode === AnnotationEditorType.ERASER && `橡皮擦模式：按住鼠标拖动擦除标注 (大小: ${annotationThickness})`}
                </div>
            )}

            <style>{`
                .saved-annotation.erasing {
                    animation: erasing-pulse 0.3s ease-out;
                    opacity: 0;
                    transform: scale(0.8);
                }
                
                @keyframes erasing-pulse {
                    0% {
                        opacity: 1;
                        transform: scale(1);
                    }
                    50% {
                        opacity: 0.5;
                        transform: scale(1.1);
                    }
                    100% {
                        opacity: 0;
                        transform: scale(0.8);
                    }
                }
            `}</style>
        </div>
    );
};
