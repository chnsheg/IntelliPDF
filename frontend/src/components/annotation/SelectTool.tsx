/**
 * SelectTool - 标注选择工具
 * 
 * 功能:
 * - 点击选择标注
 * - 显示选中边框和调整句柄
 * - 管理选中状态
 * - 提供删除、拖拽、调整接口
 */

import React, { useCallback, useEffect, useState } from 'react';

interface Geometry {
    x: number;
    y: number;
    width: number;
    height: number;
}

interface Annotation {
    id: string;
    type: string;
    pageNumber: number;
    geometry: Geometry;
    style?: {
        type?: string;
        color?: string;
        opacity?: number;
        strokeWidth?: number;
    };
}

interface SelectToolProps {
    /** 当前页码 */
    pageNumber: number;
    /** 当前页面的所有标注 */
    annotations: Annotation[];
    /** Canvas 元素引用 */
    canvasRef: React.RefObject<HTMLCanvasElement>;
    /** 选中状态变化回调 */
    onSelectionChange?: (annotationId: string | null) => void;
    /** 删除标注回调 */
    onDelete?: (annotationId: string) => void;
    /** 移动标注回调 */
    onMove?: (annotationId: string, newGeometry: Geometry) => void;
    /** 调整标注回调 */
    onResize?: (annotationId: string, newGeometry: Geometry) => void;
}

/**
 * 检查点是否在矩形内
 */
function isPointInRect(x: number, y: number, geometry: Geometry): boolean {
    return (
        x >= geometry.x &&
        x <= geometry.x + geometry.width &&
        y >= geometry.y &&
        y <= geometry.y + geometry.height
    );
}

/**
 * 检查点是否在圆形内
 */
function isPointInCircle(x: number, y: number, geometry: Geometry): boolean {
    const centerX = geometry.x + geometry.width / 2;
    const centerY = geometry.y + geometry.height / 2;
    const radiusX = geometry.width / 2;
    const radiusY = geometry.height / 2;
    
    // 椭圆公式: ((x-cx)/rx)^2 + ((y-cy)/ry)^2 <= 1
    const dx = (x - centerX) / radiusX;
    const dy = (y - centerY) / radiusY;
    return dx * dx + dy * dy <= 1;
}

/**
 * 检查点是否在箭头路径附近
 */
function isPointNearArrow(x: number, y: number, geometry: Geometry, tolerance: number = 8): boolean {
    const startX = geometry.x;
    const startY = geometry.y;
    const endX = geometry.x + geometry.width;
    const endY = geometry.y + geometry.height;
    
    // 计算点到线段的距离
    const lineLength = Math.sqrt(geometry.width ** 2 + geometry.height ** 2);
    if (lineLength === 0) return false;
    
    const t = Math.max(0, Math.min(1,
        ((x - startX) * (endX - startX) + (y - startY) * (endY - startY)) / (lineLength ** 2)
    ));
    
    const projX = startX + t * (endX - startX);
    const projY = startY + t * (endY - startY);
    
    const distance = Math.sqrt((x - projX) ** 2 + (y - projY) ** 2);
    return distance <= tolerance;
}

/**
 * 检查点击是否命中标注
 */
function hitTest(x: number, y: number, annotation: Annotation): boolean {
    const { type } = annotation.style || {};
    
    switch (type) {
        case 'rectangle':
            return isPointInRect(x, y, annotation.geometry);
        
        case 'circle':
            return isPointInCircle(x, y, annotation.geometry);
        
        case 'arrow':
            return isPointNearArrow(x, y, annotation.geometry);
        
        default:
            return isPointInRect(x, y, annotation.geometry);
    }
}

export const SelectTool: React.FC<SelectToolProps> = ({
    pageNumber,
    annotations,
    canvasRef,
    onSelectionChange,
    onDelete,
    onMove,
    onResize,
}) => {
    const [selectedId, setSelectedId] = useState<string | null>(null);
    const [hoveredId, setHoveredId] = useState<string | null>(null);

    /**
     * 处理 Canvas 点击事件
     */
    const handleCanvasClick = useCallback((event: MouseEvent) => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const rect = canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;

        // 反序遍历（从上往下），优先选择上层标注
        for (let i = annotations.length - 1; i >= 0; i--) {
            const annotation = annotations[i];
            if (hitTest(x, y, annotation)) {
                setSelectedId(annotation.id);
                onSelectionChange?.(annotation.id);
                return;
            }
        }

        // 没有命中任何标注，取消选择
        setSelectedId(null);
        onSelectionChange?.(null);
    }, [annotations, canvasRef, onSelectionChange]);

    /**
     * 处理 Canvas 鼠标移动事件（悬停效果）
     */
    const handleCanvasMouseMove = useCallback((event: MouseEvent) => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const rect = canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;

        // 检查是否悬停在任何标注上
        for (let i = annotations.length - 1; i >= 0; i--) {
            const annotation = annotations[i];
            if (hitTest(x, y, annotation)) {
                setHoveredId(annotation.id);
                canvas.style.cursor = 'pointer';
                return;
            }
        }

        setHoveredId(null);
        canvas.style.cursor = 'default';
    }, [annotations, canvasRef]);

    /**
     * 处理 Delete 键删除
     */
    const handleKeyDown = useCallback((event: KeyboardEvent) => {
        if (event.key === 'Delete' && selectedId && onDelete) {
            event.preventDefault();
            onDelete(selectedId);
            setSelectedId(null);
            onSelectionChange?.(null);
        }
    }, [selectedId, onDelete, onSelectionChange]);

    /**
     * 绑定事件监听
     */
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        canvas.addEventListener('click', handleCanvasClick);
        canvas.addEventListener('mousemove', handleCanvasMouseMove);
        document.addEventListener('keydown', handleKeyDown);

        return () => {
            canvas.removeEventListener('click', handleCanvasClick);
            canvas.removeEventListener('mousemove', handleCanvasMouseMove);
            document.removeEventListener('keydown', handleKeyDown);
        };
    }, [handleCanvasClick, handleCanvasMouseMove, handleKeyDown, canvasRef]);

    /**
     * 绘制选中边框和句柄
     */
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        // 清除之前的选中框（需要重绘整个 canvas）
        // 这里假设父组件会重绘标注，我们只添加选中框

        if (selectedId) {
            const selectedAnnotation = annotations.find(a => a.id === selectedId);
            if (selectedAnnotation) {
                drawSelectionBox(ctx, selectedAnnotation);
            }
        }

        if (hoveredId && hoveredId !== selectedId) {
            const hoveredAnnotation = annotations.find(a => a.id === hoveredId);
            if (hoveredAnnotation) {
                drawHoverBox(ctx, hoveredAnnotation);
            }
        }
    }, [selectedId, hoveredId, annotations, canvasRef]);

    return null; // 无需渲染 DOM，只监听事件和绘制
};

/**
 * 绘制选中边框
 */
function drawSelectionBox(ctx: CanvasRenderingContext2D, annotation: Annotation): void {
    const { x, y, width, height } = annotation.geometry;

    ctx.save();
    
    // 绘制虚线边框
    ctx.strokeStyle = '#2196F3';
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);
    ctx.strokeRect(x - 2, y - 2, width + 4, height + 4);

    // 绘制 8 个调整句柄
    const handleSize = 8;
    const handles = [
        { x: x, y: y },                             // 左上
        { x: x + width / 2, y: y },                 // 上中
        { x: x + width, y: y },                     // 右上
        { x: x + width, y: y + height / 2 },        // 右中
        { x: x + width, y: y + height },            // 右下
        { x: x + width / 2, y: y + height },        // 下中
        { x: x, y: y + height },                    // 左下
        { x: x, y: y + height / 2 },                // 左中
    ];

    ctx.fillStyle = '#FFFFFF';
    ctx.strokeStyle = '#2196F3';
    ctx.lineWidth = 2;
    ctx.setLineDash([]);

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

    ctx.restore();
}

/**
 * 绘制悬停边框
 */
function drawHoverBox(ctx: CanvasRenderingContext2D, annotation: Annotation): void {
    const { x, y, width, height } = annotation.geometry;

    ctx.save();
    ctx.strokeStyle = '#90CAF9';
    ctx.lineWidth = 2;
    ctx.setLineDash([]);
    ctx.strokeRect(x - 1, y - 1, width + 2, height + 2);
    ctx.restore();
}
