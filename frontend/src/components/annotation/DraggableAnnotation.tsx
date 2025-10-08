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
    geometry?: Geometry;  // 可选，便笺等标注类型没有 geometry
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

interface DraggableAnnotationPropsExtended extends DraggableAnnotationProps {
    /** 调整大小完成回调 */
    onResizeComplete?: (annotationId: string, newGeometry: Geometry) => void;
}

export const DraggableAnnotation: React.FC<DraggableAnnotationPropsExtended> = ({
    pageNumber,
    annotations,
    scale,
    pdfPage,
    selectedAnnotationId,
    onSelect,
    onMoveComplete,
    onResizeComplete,
}) => {
    const [isDragging, setIsDragging] = useState(false);
    const [isResizing, setIsResizing] = useState(false);
    const [resizeHandle, setResizeHandle] = useState<string | null>(null);
    const [dragStartPos, setDragStartPos] = useState<{ x: number; y: number } | null>(null);
    const [dragOffset, setDragOffset] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
    const [resizeStart, setResizeStart] = useState<Geometry | null>(null);
    const overlayRef = useRef<HTMLDivElement>(null);

    /**
     * 检查点击是否命中标注
     */
    const hitTest = useCallback((x: number, y: number, annotation: Annotation): boolean => {
        const { geometry } = annotation;
        
        // 跳过没有 geometry 的标注（例如便笺）
        if (!geometry) {
            return false;
        }
        
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
     * 检查是否点击了调整句柄
     */
    const getResizeHandle = useCallback((x: number, y: number, geometry: Geometry): string | null => {
        const viewport = pdfPage.getViewport({ scale });
        const screenX = geometry.x * scale;
        const screenY = (viewport.height / scale - geometry.y - geometry.height) * scale;
        const screenWidth = geometry.width * scale;
        const screenHeight = geometry.height * scale;

        const handleSize = 12; // 句柄大小
        const handles = {
            'nw': { x: screenX, y: screenY },
            'ne': { x: screenX + screenWidth, y: screenY },
            'sw': { x: screenX, y: screenY + screenHeight },
            'se': { x: screenX + screenWidth, y: screenY + screenHeight },
        };

        for (const [handle, pos] of Object.entries(handles)) {
            if (Math.abs(x - pos.x) <= handleSize && Math.abs(y - pos.y) <= handleSize) {
                return handle;
            }
        }

        return null;
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
            if (selectedAnnotation && selectedAnnotation.geometry) {
                // 检查是否点击了调整句柄
                const handle = getResizeHandle(x, y, selectedAnnotation.geometry);
                if (handle) {
                    setIsResizing(true);
                    setResizeHandle(handle);
                    setDragStartPos({ x, y });
                    setResizeStart(selectedAnnotation.geometry);
                    event.stopPropagation();
                    return;
                }

                // 检查是否点击了标注本身
                if (hitTest(x, y, selectedAnnotation)) {
                    // 开始拖拽
                    setIsDragging(true);
                    setDragStartPos({ x, y });
                    setDragOffset({ x: 0, y: 0 });
                    event.stopPropagation();
                    return;
                }
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
    }, [annotations, selectedAnnotationId, hitTest, getResizeHandle, onSelect]);

    /**
     * 处理鼠标移动
     */
    const handleMouseMove = useCallback((event: React.MouseEvent<HTMLDivElement>) => {
        if (!overlayRef.current || !dragStartPos) return;
        if (!isDragging && !isResizing) return;

        const rect = overlayRef.current.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;

        const dx = x - dragStartPos.x;
        const dy = y - dragStartPos.y;

        if (isDragging) {
            // 拖拽移动
            setDragOffset({ x: dx, y: dy });
        } else if (isResizing && resizeStart && resizeHandle) {
            // 调整大小 - 直接更新 dragOffset 用于实时预览
            // 转换为 PDF 坐标偏移量
            const pdfDx = dx / scale;
            const pdfDy = -dy / scale; // Y 轴反转

            let newWidth = resizeStart.width;
            let newHeight = resizeStart.height;
            let newX = resizeStart.x;
            let newY = resizeStart.y;

            switch (resizeHandle) {
                case 'nw': // 左上角
                    newX = resizeStart.x + pdfDx;
                    newY = resizeStart.y + pdfDy;
                    newWidth = resizeStart.width - pdfDx;
                    newHeight = resizeStart.height - pdfDy;
                    break;
                case 'ne': // 右上角
                    newY = resizeStart.y + pdfDy;
                    newWidth = resizeStart.width + pdfDx;
                    newHeight = resizeStart.height - pdfDy;
                    break;
                case 'sw': // 左下角
                    newX = resizeStart.x + pdfDx;
                    newWidth = resizeStart.width - pdfDx;
                    newHeight = resizeStart.height + pdfDy;
                    break;
                case 'se': // 右下角
                    newWidth = resizeStart.width + pdfDx;
                    newHeight = resizeStart.height + pdfDy;
                    break;
            }

            // 应用最小尺寸约束
            const minSize = 20 / scale; // 最小尺寸 20px
            newWidth = Math.max(minSize, newWidth);
            newHeight = Math.max(minSize, newHeight);

            // 计算偏移量用于实时预览
            setDragOffset({ 
                x: (newX - resizeStart.x) * scale, 
                y: -(newY - resizeStart.y) * scale 
            });
        }
    }, [isDragging, isResizing, dragStartPos, resizeStart, resizeHandle, scale]);

    /**
     * 处理鼠标释放
     */
    const handleMouseUp = useCallback(() => {
        if (!selectedAnnotationId) return;
        if (!isDragging && !isResizing) return;

        const selectedAnnotation = annotations.find(a => a.id === selectedAnnotationId);
        if (!selectedAnnotation || !selectedAnnotation.geometry) return;

        const viewport = pdfPage.getViewport({ scale });

        if (isDragging) {
            // 拖拽移动完成
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
        } else if (isResizing && resizeStart && resizeHandle) {
            // 调整大小完成
            const pdfDx = dragOffset.x / scale;
            const pdfDy = -dragOffset.y / scale;

            let newWidth = resizeStart.width;
            let newHeight = resizeStart.height;
            let newX = resizeStart.x;
            let newY = resizeStart.y;

            switch (resizeHandle) {
                case 'nw': // 左上角
                    newX = resizeStart.x + pdfDx;
                    newY = resizeStart.y + pdfDy;
                    newWidth = resizeStart.width - pdfDx;
                    newHeight = resizeStart.height - pdfDy;
                    break;
                case 'ne': // 右上角
                    newY = resizeStart.y + pdfDy;
                    newWidth = resizeStart.width + pdfDx;
                    newHeight = resizeStart.height - pdfDy;
                    break;
                case 'sw': // 左下角
                    newX = resizeStart.x + pdfDx;
                    newWidth = resizeStart.width - pdfDx;
                    newHeight = resizeStart.height + pdfDy;
                    break;
                case 'se': // 右下角
                    newWidth = resizeStart.width + pdfDx;
                    newHeight = resizeStart.height + pdfDy;
                    break;
            }

            // 应用最小尺寸约束
            const minSize = 20 / scale;
            newWidth = Math.max(minSize, newWidth);
            newHeight = Math.max(minSize, newHeight);

            // 边界检查
            newX = Math.max(0, Math.min(newX, viewport.width / scale - newWidth));
            newY = Math.max(0, Math.min(newY, viewport.height / scale - newHeight));

            const newGeometry: Geometry = {
                x: newX,
                y: newY,
                width: newWidth,
                height: newHeight,
            };

            // 通知父组件
            if (onResizeComplete) {
                onResizeComplete(selectedAnnotationId, newGeometry);
            }

            // 重置状态
            setIsResizing(false);
            setResizeHandle(null);
            setResizeStart(null);
        }

        setDragStartPos(null);
        setDragOffset({ x: 0, y: 0 });
    }, [isDragging, isResizing, selectedAnnotationId, annotations, pdfPage, scale, dragOffset, resizeStart, resizeHandle, onMoveComplete, onResizeComplete]);

    /**
     * 渲染选中边框和拖拽预览
     */
    const renderSelectionBox = () => {
        if (!selectedAnnotationId) return null;

        const selectedAnnotation = annotations.find(a => a.id === selectedAnnotationId);
        if (!selectedAnnotation || !selectedAnnotation.geometry) return null;

        const { geometry } = selectedAnnotation;
        const viewport = pdfPage.getViewport({ scale });
        
        let left, top, width, height;

        if (isResizing && resizeStart && resizeHandle) {
            // 调整大小时，计算新的尺寸和位置
            const pdfDx = dragOffset.x / scale;
            const pdfDy = -dragOffset.y / scale;

            let newWidth = resizeStart.width;
            let newHeight = resizeStart.height;
            let newX = resizeStart.x;
            let newY = resizeStart.y;

            switch (resizeHandle) {
                case 'nw':
                    newX = resizeStart.x + pdfDx;
                    newY = resizeStart.y + pdfDy;
                    newWidth = resizeStart.width - pdfDx;
                    newHeight = resizeStart.height - pdfDy;
                    break;
                case 'ne':
                    newY = resizeStart.y + pdfDy;
                    newWidth = resizeStart.width + pdfDx;
                    newHeight = resizeStart.height - pdfDy;
                    break;
                case 'sw':
                    newX = resizeStart.x + pdfDx;
                    newWidth = resizeStart.width - pdfDx;
                    newHeight = resizeStart.height + pdfDy;
                    break;
                case 'se':
                    newWidth = resizeStart.width + pdfDx;
                    newHeight = resizeStart.height + pdfDy;
                    break;
            }

            const minSize = 20 / scale;
            newWidth = Math.max(minSize, newWidth);
            newHeight = Math.max(minSize, newHeight);

            left = newX * scale;
            top = (viewport.height / scale - newY - newHeight) * scale;
            width = newWidth * scale;
            height = newHeight * scale;
        } else {
            // 拖拽移动或静止状态
            left = geometry.x * scale + dragOffset.x;
            top = (viewport.height / scale - geometry.y - geometry.height) * scale + dragOffset.y;
            width = geometry.width * scale;
            height = geometry.height * scale;
        }

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
                    backgroundColor: isDragging || isResizing ? 'rgba(33, 150, 243, 0.1)' : 'transparent',
                    cursor: isDragging ? 'grabbing' : isResizing ? 'nwse-resize' : 'grab',
                }}
            >
                {/* 调整句柄 (4个角) */}
                {!isDragging && !isResizing && (
                    <>
                        {['nw', 'ne', 'sw', 'se'].map(position => (
                            <div
                                key={position}
                                className="absolute w-3 h-3 bg-white border-2 border-blue-500 rounded-sm pointer-events-auto"
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
