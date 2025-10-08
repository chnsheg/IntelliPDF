/**
 * DraggableAnnotation - 可拖拽的标注覆盖层
 * 
 * 功能:
 * - 检测标注点击
 * - 拖拽移动标注
 * - 实时预览位置
 * - 保存到后端
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';

interface Geometry {
    x: number;
    y: number;
    width: number;
    height: number;
}

interface Annotation {
    id: string;
    pageNumber: number;
    geometry: Geometry;
    type: string;
    style?: any;
}

interface DraggableAnnotationProps {
    /** 当前页码 */
    pageNumber: number;
    /** 当前页面的标注 */
    annotations: Annotation[];
    /** 缩放比例 */
    scale: number;
    /** PDF 页面对象 */
    pdfPage: any;
    /** 选中的标注ID */
    selectedAnnotationId: string | null;
    /** 选择标注回调 */
    onSelect: (annotationId: string | null) => void;
    /** 移动完成回调 */
    onMoveComplete: (annotationId: string, newGeometry: Geometry) => void;
}

export const DraggableAnnotation: React.FC<DraggableAnnotationProps> = ({
    pageNumber,
    annotations,
    scale,
    pdfPage,
    selectedAnnotationId,
    onSelect,
    onMoveComplete,
}) => {
    const [isDragging, setIsDragging] = useState(false);
    const [dragStartPos, setDragStartPos] = useState<{ x: number; y: number } | null>(null);
    const [dragOffset, setDragOffset] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
    const overlayRef = useRef<HTMLDivElement>(null);

    /**
     * 检查点击是否命中标注
     */
    const hitTest = useCallback((x: number, y: number, annotation: Annotation): boolean => {
        const { geometry } = annotation;
        
        // 转换为屏幕坐标
        const viewport = pdfPage.getViewport({ scale });
        const screenX = geometry.x * scale;
        const screenY = (viewport.height / scale - geometry.y - geometry.height) * scale;
        const screenWidth = geometry.width * scale;
        const screenHeight = geometry.height * scale;

        return (
            x >= screenX &&
            x <= screenX + screenWidth &&
            y >= screenY &&
            y <= screenY + screenHeight
        );
    }, [pdfPage, scale]);

    /**
     * 处理鼠标按下
     */
    const handleMouseDown = useCallback((event: React.MouseEvent<HTMLDivElement>) => {
        if (!overlayRef.current) return;

        const rect = overlayRef.current.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;

        // 检查是否点击了选中的标注
        if (selectedAnnotationId) {
            const selectedAnnotation = annotations.find(a => a.id === selectedAnnotationId);
            if (selectedAnnotation && hitTest(x, y, selectedAnnotation)) {
                // 开始拖拽
                setIsDragging(true);
                setDragStartPos({ x, y });
                setDragOffset({ x: 0, y: 0 });
                event.stopPropagation();
                return;
            }
        }

        // 检查是否点击了其他标注
        for (let i = annotations.length - 1; i >= 0; i--) {
            const annotation = annotations[i];
            if (hitTest(x, y, annotation)) {
                onSelect(annotation.id);
                event.stopPropagation();
                return;
            }
        }

        // 没有命中任何标注，取消选择
        onSelect(null);
    }, [annotations, selectedAnnotationId, hitTest, onSelect]);

    /**
     * 处理鼠标移动
     */
    const handleMouseMove = useCallback((event: React.MouseEvent<HTMLDivElement>) => {
        if (!isDragging || !dragStartPos || !overlayRef.current) return;

        const rect = overlayRef.current.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;

        const dx = x - dragStartPos.x;
        const dy = y - dragStartPos.y;

        setDragOffset({ x: dx, y: dy });
    }, [isDragging, dragStartPos]);

    /**
     * 处理鼠标释放
     */
    const handleMouseUp = useCallback(() => {
        if (!isDragging || !selectedAnnotationId) return;

        const selectedAnnotation = annotations.find(a => a.id === selectedAnnotationId);
        if (!selectedAnnotation) return;

        // 转换偏移量为 PDF 坐标
        const viewport = pdfPage.getViewport({ scale });
        const pdfDx = dragOffset.x / scale;
        const pdfDy = -dragOffset.y / scale; // Y轴反向

        // 计算新的几何位置
        const newGeometry: Geometry = {
            x: selectedAnnotation.geometry.x + pdfDx,
            y: selectedAnnotation.geometry.y + pdfDy,
            width: selectedAnnotation.geometry.width,
            height: selectedAnnotation.geometry.height,
        };

        // 边界检查
        newGeometry.x = Math.max(0, Math.min(newGeometry.x, viewport.width / scale - newGeometry.width));
        newGeometry.y = Math.max(0, Math.min(newGeometry.y, viewport.height / scale - newGeometry.height));

        // 通知父组件
        if (Math.abs(dragOffset.x) > 2 || Math.abs(dragOffset.y) > 2) {
            onMoveComplete(selectedAnnotationId, newGeometry);
        }

        // 重置状态
        setIsDragging(false);
        setDragStartPos(null);
        setDragOffset({ x: 0, y: 0 });
    }, [isDragging, selectedAnnotationId, annotations, pdfPage, scale, dragOffset, onMoveComplete]);

    /**
     * 渲染选中边框和拖拽预览
     */
    const renderSelectionBox = () => {
        if (!selectedAnnotationId) return null;

        const selectedAnnotation = annotations.find(a => a.id === selectedAnnotationId);
        if (!selectedAnnotation) return null;

        const { geometry } = selectedAnnotation;
        const viewport = pdfPage.getViewport({ scale });
        
        let left = geometry.x * scale + dragOffset.x;
        let top = (viewport.height / scale - geometry.y - geometry.height) * scale + dragOffset.y;
        const width = geometry.width * scale;
        const height = geometry.height * scale;

        return (
            <div
                key={`selection-${selectedAnnotation.id}`}
                className="absolute pointer-events-none"
                style={{
                    left: `${left}px`,
                    top: `${top}px`,
                    width: `${width}px`,
                    height: `${height}px`,
                    border: '2px dashed #2196F3',
                    backgroundColor: isDragging ? 'rgba(33, 150, 243, 0.1)' : 'transparent',
                    cursor: isDragging ? 'grabbing' : 'grab',
                }}
            >
                {/* 调整句柄 (4个角) */}
                {!isDragging && (
                    <>
                        {['nw', 'ne', 'sw', 'se'].map(position => (
                            <div
                                key={position}
                                className="absolute w-3 h-3 bg-white border-2 border-blue-500 rounded-sm"
                                style={{
                                    left: position.includes('w') ? '-6px' : undefined,
                                    right: position.includes('e') ? '-6px' : undefined,
                                    top: position.includes('n') ? '-6px' : undefined,
                                    bottom: position.includes('s') ? '-6px' : undefined,
                                    cursor: `${position}-resize`,
                                }}
                            />
                        ))}
                    </>
                )}
            </div>
        );
    };

    /**
     * 设置鼠标样式
     */
    useEffect(() => {
        if (!overlayRef.current) return;

        if (isDragging) {
            overlayRef.current.style.cursor = 'grabbing';
        } else if (selectedAnnotationId) {
            overlayRef.current.style.cursor = 'grab';
        } else {
            overlayRef.current.style.cursor = 'default';
        }
    }, [isDragging, selectedAnnotationId]);

    return (
        <div
            ref={overlayRef}
            className="absolute inset-0 z-30"
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
        >
            {renderSelectionBox()}
        </div>
    );
};
