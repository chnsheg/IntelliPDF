/**
 * 标注 Canvas 渲染组件
 * 使用 Canvas 覆盖层渲染所有标注
 */

import React, { useEffect, useRef } from 'react';
import type { PDFPageProxy } from 'pdfjs-dist';
import type {
    Annotation,
    TextMarkupAnnotation,
    ShapeAnnotation,
    InkAnnotation,
    NoteAnnotation
} from '../../types/annotation';
import { pdfCoordinateService } from '../../services/annotation/pdfCoordinates';
import { hexToRgba } from '../../utils/annotation';

interface AnnotationCanvasProps {
    /** 页码 */
    pageNumber: number;
    /** 标注列表 */
    annotations: Annotation[];
    /** 缩放比例 */
    scale: number;
    /** PDF 页面对象 */
    pdfPage: PDFPageProxy | null;
    /** 点击标注回调 */
    onAnnotationClick?: (annotationId: string) => void;
    /** 选中的标注ID列表 */
    selectedAnnotationIds?: string[];
}

export const AnnotationCanvas: React.FC<AnnotationCanvasProps> = ({
    pageNumber,
    annotations,
    scale,
    pdfPage,
    onAnnotationClick,
    selectedAnnotationIds = []
}) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    useEffect(() => {
        if (!canvasRef.current || !pdfPage) return;

        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        // 获取视口
        const viewport = pdfPage.getViewport({ scale });

        // 设置画布尺寸
        canvas.width = viewport.width;
        canvas.height = viewport.height;

        // 清空画布
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        console.log(`[AnnotationCanvas] Page ${pageNumber}:`, {
            totalAnnotations: annotations.length,
            annotationTypes: annotations.map(a => ({ id: a.id, type: a.type, pageNumber: (a as any).pageNumber }))
        });

        // 筛选当前页面的标注
        const pageAnnotations = annotations.filter(a => {
            if (a.type === 'text-markup') {
                return a.pdfCoordinates.pageNumber === pageNumber;
            }
            return (a as any).pageNumber === pageNumber;
        });

        console.log(`[AnnotationCanvas] Page ${pageNumber} filtered:`, {
            count: pageAnnotations.length,
            annotations: pageAnnotations.map(a => ({ id: a.id, type: a.type }))
        });

        // 渲染每个标注
        pageAnnotations.forEach(annotation => {
            const isSelected = selectedAnnotationIds.includes(annotation.id);
            console.log(`[AnnotationCanvas] Rendering annotation:`, { id: annotation.id, type: annotation.type });
            renderAnnotation(ctx, annotation, viewport, isSelected);
        });
    }, [pageNumber, annotations, scale, pdfPage, selectedAnnotationIds]);

    /**
     * 渲染单个标注
     */
    const renderAnnotation = (
        ctx: CanvasRenderingContext2D,
        annotation: Annotation,
        viewport: any,
        isSelected: boolean
    ) => {
        switch (annotation.type) {
            case 'text-markup':
                renderTextMarkup(ctx, annotation, viewport, isSelected);
                break;
            case 'shape':
                renderShape(ctx, annotation, viewport, isSelected);
                break;
            case 'ink':
                renderInk(ctx, annotation, viewport, isSelected);
                break;
            case 'note':
                renderNote(ctx, annotation, viewport, isSelected);
                break;
        }
    };

    /**
     * 渲染文本标注（高亮、下划线等）
     */
    const renderTextMarkup = (
        ctx: CanvasRenderingContext2D,
        annotation: TextMarkupAnnotation,
        viewport: any,
        isSelected: boolean
    ) => {
        const { quadPoints } = annotation.pdfCoordinates;
        const { style } = annotation;

        quadPoints.forEach(quad => {
            const screenCoords = pdfCoordinateService.quadPointToScreen(quad, viewport);
            const { points } = screenCoords;

            // 绘制路径
            ctx.beginPath();
            points.forEach((point, index) => {
                if (index === 0) {
                    ctx.moveTo(point[0], point[1]);
                } else {
                    ctx.lineTo(point[0], point[1]);
                }
            });
            ctx.closePath();

            // 应用样式
            const color = hexToRgba(style.color, style.opacity);

            switch (style.type) {
                case 'highlight':
                    ctx.fillStyle = color;
                    ctx.fill();
                    break;

                case 'underline':
                    ctx.strokeStyle = color;
                    ctx.lineWidth = 2;
                    ctx.beginPath();
                    ctx.moveTo(points[0][0], points[0][1]);
                    ctx.lineTo(points[1][0], points[1][1]);
                    ctx.stroke();
                    break;

                case 'strikethrough':
                    ctx.strokeStyle = color;
                    ctx.lineWidth = 2;
                    const midY = (points[0][1] + points[2][1]) / 2;
                    ctx.beginPath();
                    ctx.moveTo(points[0][0], midY);
                    ctx.lineTo(points[1][0], midY);
                    ctx.stroke();
                    break;

                case 'squiggly':
                    ctx.strokeStyle = color;
                    ctx.lineWidth = 1;
                    drawSquigglyLine(
                        ctx,
                        points[0][0],
                        points[0][1],
                        points[1][0],
                        points[1][1]
                    );
                    break;
            }

            // 绘制选中框
            if (isSelected) {
                drawSelectionBox(ctx, screenCoords);
            }
        });
    };

    /**
     * 渲染图形标注
     */
    const renderShape = (
        ctx: CanvasRenderingContext2D,
        annotation: ShapeAnnotation,
        viewport: any,
        isSelected: boolean
    ) => {
        console.log('[renderShape] Annotation:', {
            id: annotation.id,
            type: annotation.type,
            geometry: annotation.geometry,
            style: annotation.style,
            'style.type': annotation.style.type,
            'style.color': annotation.style.color
        });

        const { style } = annotation;
        
        // 🔥 关键检查：如果 style.type 不存在，无法渲染
        if (!style.type) {
            console.error('[renderShape] ❌ style.type is undefined! Cannot render shape. Style:', style);
            return;
        }
        
        const color = hexToRgba(style.color, style.opacity);

        ctx.strokeStyle = color;
        ctx.lineWidth = style.strokeWidth;

        // 设置线条样式
        if (style.lineStyle === 'dashed') {
            ctx.setLineDash([5, 5]);
        } else if (style.lineStyle === 'dotted') {
            ctx.setLineDash([2, 2]);
        } else {
            ctx.setLineDash([]);
        }

        // 填充样式
        if (style.fillColor) {
            ctx.fillStyle = hexToRgba(style.fillColor, style.fillOpacity || 0.3);
        }

        console.log('[renderShape] Has rect:', !!annotation.geometry.rect, 'Has points:', !!annotation.geometry.points);

        if (annotation.geometry.rect) {
            const rect = pdfCoordinateService.rectangleToScreen(
                annotation.geometry.rect,
                viewport
            );
            
            console.log('[renderShape] Drawing rect:', rect);

            // 支持 'square' 和 'rectangle' (前端发送的是 'rectangle')
            if (style.type === 'square' || style.type === 'rectangle') {
                ctx.strokeRect(rect.x, rect.y, rect.width, rect.height);
                if (style.fillColor) {
                    ctx.fillRect(rect.x, rect.y, rect.width, rect.height);
                }
            } else if (style.type === 'circle') {
                const centerX = rect.x + rect.width / 2;
                const centerY = rect.y + rect.height / 2;
                const radiusX = rect.width / 2;
                const radiusY = rect.height / 2;

                ctx.beginPath();
                ctx.ellipse(centerX, centerY, radiusX, radiusY, 0, 0, 2 * Math.PI);
                ctx.stroke();
                if (style.fillColor) {
                    ctx.fill();
                }
            }

            if (isSelected) {
                drawSelectionBox(ctx, rect);
            }
        } else if (annotation.geometry.points) {
            const points = pdfCoordinateService.pathToScreen(
                annotation.geometry.points,
                viewport
            );

            if (style.type === 'polygon') {
                ctx.beginPath();
                points.forEach((point, index) => {
                    if (index === 0) {
                        ctx.moveTo(point.x, point.y);
                    } else {
                        ctx.lineTo(point.x, point.y);
                    }
                });
                ctx.closePath();
                ctx.stroke();
                if (style.fillColor) {
                    ctx.fill();
                }
            } else if (style.type === 'line' || style.type === 'arrow') {
                ctx.beginPath();
                ctx.moveTo(points[0].x, points[0].y);
                ctx.lineTo(points[1].x, points[1].y);
                ctx.stroke();

                // 绘制箭头
                if (style.type === 'arrow' && style.arrowType !== 'none') {
                    drawArrowHead(
                        ctx,
                        points[0].x,
                        points[0].y,
                        points[1].x,
                        points[1].y,
                        style.arrowType || 'open'
                    );
                }
            }
        }

        ctx.setLineDash([]);  // 重置
    };

    /**
     * 渲染画笔标注
     */
    const renderInk = (
        ctx: CanvasRenderingContext2D,
        annotation: InkAnnotation,
        viewport: any,
        isSelected: boolean
    ) => {
        const { style, paths } = annotation;

        ctx.strokeStyle = hexToRgba(style.color, style.opacity);
        ctx.lineWidth = style.strokeWidth;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';

        paths.forEach(path => {
            const screenPoints = pdfCoordinateService.pathToScreen(
                path.points,
                viewport
            );

            if (screenPoints.length < 2) return;

            ctx.beginPath();
            ctx.moveTo(screenPoints[0].x, screenPoints[0].y);

            for (let i = 1; i < screenPoints.length; i++) {
                ctx.lineTo(screenPoints[i].x, screenPoints[i].y);
            }

            ctx.stroke();
        });
    };

    /**
     * 渲染便签标注
     */
    const renderNote = (
        ctx: CanvasRenderingContext2D,
        annotation: NoteAnnotation,
        viewport: any,
        isSelected: boolean
    ) => {
        // 兼容 position 和 point 两种字段名
        const notePoint = (annotation as any).position || annotation.point;
        if (!notePoint) {
            console.warn('Note annotation missing position/point:', annotation);
            return;
        }

        const point = pdfCoordinateService.pointToScreen(
            notePoint,
            viewport
        );

        // 兼容不同的颜色字段结构
        const noteColor = (annotation as any).color || annotation.style?.color || '#FFD54F';
        const noteOpacity = annotation.style?.opacity || 1.0;
        const iconType = annotation.style?.iconType || 'comment';

        // 绘制便签图标
        const iconSize = 24;
        ctx.fillStyle = hexToRgba(noteColor, noteOpacity);

        ctx.beginPath();
        ctx.arc(point.x, point.y, iconSize / 2, 0, 2 * Math.PI);
        ctx.fill();

        // 绘制图标内容（根据 iconType）
        ctx.fillStyle = '#FFFFFF';
        ctx.font = '14px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        const icon = getIconChar(iconType);
        ctx.fillText(icon, point.x, point.y);

        if (isSelected) {
            ctx.strokeStyle = '#0066FF';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.arc(point.x, point.y, iconSize / 2 + 3, 0, 2 * Math.PI);
            ctx.stroke();
        }
    };

    /**
     * 绘制波浪线
     */
    const drawSquigglyLine = (
        ctx: CanvasRenderingContext2D,
        x1: number,
        y1: number,
        x2: number,
        y2: number
    ) => {
        const amplitude = 2;
        const frequency = 0.3;
        const length = Math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2);
        const steps = Math.floor(length / 2);

        ctx.beginPath();
        for (let i = 0; i <= steps; i++) {
            const t = i / steps;
            const x = x1 + (x2 - x1) * t;
            const y = y1 + (y2 - y1) * t + Math.sin(i * frequency * Math.PI) * amplitude;

            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        }
        ctx.stroke();
    };

    /**
     * 绘制箭头头部
     */
    const drawArrowHead = (
        ctx: CanvasRenderingContext2D,
        x1: number,
        y1: number,
        x2: number,
        y2: number,
        type: string
    ) => {
        const angle = Math.atan2(y2 - y1, x2 - x1);
        const headLength = 15;

        ctx.beginPath();
        ctx.moveTo(x2, y2);
        ctx.lineTo(
            x2 - headLength * Math.cos(angle - Math.PI / 6),
            y2 - headLength * Math.sin(angle - Math.PI / 6)
        );

        if (type === 'closed') {
            ctx.lineTo(
                x2 - headLength * Math.cos(angle + Math.PI / 6),
                y2 - headLength * Math.sin(angle + Math.PI / 6)
            );
            ctx.closePath();
            ctx.fill();
        } else {
            ctx.moveTo(x2, y2);
            ctx.lineTo(
                x2 - headLength * Math.cos(angle + Math.PI / 6),
                y2 - headLength * Math.sin(angle + Math.PI / 6)
            );
        }
        ctx.stroke();
    };

    /**
     * 绘制选中框
     */
    const drawSelectionBox = (
        ctx: CanvasRenderingContext2D,
        rect: { x: number; y: number; width: number; height: number }
    ) => {
        ctx.strokeStyle = '#0066FF';
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 5]);
        ctx.strokeRect(rect.x - 2, rect.y - 2, rect.width + 4, rect.height + 4);
        ctx.setLineDash([]);

        // 绘制调整手柄
        const handleSize = 6;
        const handles = [
            { x: rect.x, y: rect.y },  // 左上
            { x: rect.x + rect.width, y: rect.y },  // 右上
            { x: rect.x, y: rect.y + rect.height },  // 左下
            { x: rect.x + rect.width, y: rect.y + rect.height }  // 右下
        ];

        ctx.fillStyle = '#FFFFFF';
        ctx.strokeStyle = '#0066FF';
        ctx.lineWidth = 1;

        handles.forEach(handle => {
            ctx.fillRect(
                handle.x - handleSize / 2,
                handle.y - handleSize / 2,
                handleSize,
                handleSize
            );
            ctx.strokeRect(
                handle.x - handleSize / 2,
                handle.y - handleSize / 2,
                handleSize,
                handleSize
            );
        });
    };

    /**
     * 获取便签图标字符
     */
    const getIconChar = (iconType: string): string => {
        const icons: Record<string, string> = {
            comment: '💬',
            help: '❓',
            note: '📝',
            paragraph: '¶',
            insert: '➕',
            key: '🔑'
        };
        return icons[iconType] || '📝';
    };

    return (
        <canvas
            ref={canvasRef}
            className="absolute top-0 left-0 pointer-events-none"
            style={{ zIndex: 10 }}
        />
    );
};
