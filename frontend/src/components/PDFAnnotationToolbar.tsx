/**
 * PDF Annotation Toolbar - Draggable Floating Toolbar
 * 
 * 只包含 PDF.js 原生支持的标注工具，支持拖动
 */

import React, { useState, useRef, useEffect } from 'react';
import { FiMousePointer, FiEdit3, FiType, FiImage, FiZoomIn, FiZoomOut, FiSquare, FiCircle, FiMove, FiTrash2, FiSlash } from 'react-icons/fi';
import { BsArrowUpRight, BsPencilSquare, BsPentagon } from 'react-icons/bs';
import { MdGesture } from 'react-icons/md';
import clsx from 'clsx';

interface PDFAnnotationToolbarProps {
    currentMode: number;
    onModeChange: (mode: number) => void;
    onZoomIn: () => void;
    onZoomOut: () => void;
    scale: number;
    color?: string;
    onColorChange?: (color: string) => void;
    thickness?: number;
    onThicknessChange?: (thickness: number) => void;
    fontSize?: number;
    onFontSizeChange?: (size: number) => void;
}

// PDF.js 标注模式常量 + 自定义类型
const MODES = {
    NONE: 0,         // 选择/查看模式
    FREETEXT: 3,     // 文本框
    HIGHLIGHT: 9,    // 高亮
    INK: 15,         // 画笔/手绘
    STAMP: 13,       // 图章
    RECTANGLE: 100,  // 矩形
    CIRCLE: 101,     // 圆形
    ARROW: 102,      // 箭头
    ERASER: 103,     // 橡皮擦
    WAVY_LINE: 104,  // 波浪线
    STRIKETHROUGH: 105, // 删除线
    LASSO: 106,      // 套索选择
};

export const PDFAnnotationToolbar: React.FC<PDFAnnotationToolbarProps> = ({
    currentMode,
    onModeChange,
    onZoomIn,
    onZoomOut,
    scale,
    color = '#ff0000',
    onColorChange,
    thickness = 2,
    onThicknessChange,
    fontSize = 16,
    onFontSizeChange,
}) => {
    const colors = ['#ff0000', '#0000ff', '#00ff00', '#ffff00', '#ff00ff', '#ffa500'];
    const thicknesses = [1, 2, 3, 4, 5];
    const fontSizes = [12, 14, 16, 18, 20, 24];

    // 拖动状态
    const [position, setPosition] = useState({ x: 20, y: 100 });
    const [isDragging, setIsDragging] = useState(false);
    const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
    const [isCollapsed, setIsCollapsed] = useState(false); // 折叠状态
    const toolbarRef = useRef<HTMLDivElement>(null);

    // 处理拖动开始
    const handleDragStart = (e: React.MouseEvent) => {
        if (toolbarRef.current) {
            const rect = toolbarRef.current.getBoundingClientRect();
            setDragOffset({
                x: e.clientX - rect.left,
                y: e.clientY - rect.top
            });
            setIsDragging(true);
        }
    };

    // 处理拖动
    useEffect(() => {
        if (!isDragging) return;

        const handleMouseMove = (e: MouseEvent) => {
            setPosition({
                x: e.clientX - dragOffset.x,
                y: e.clientY - dragOffset.y
            });
        };

        const handleMouseUp = () => {
            setIsDragging(false);
        };

        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);

        return () => {
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
        };
    }, [isDragging, dragOffset]);

    return (
        <div
            ref={toolbarRef}
            className="fixed z-50 bg-white rounded-lg shadow-xl border border-gray-200 p-2 flex flex-col gap-1"
            style={{
                left: `${position.x}px`,
                top: `${position.y}px`,
                cursor: isDragging ? 'grabbing' : 'auto'
            }}
        >
            {/* 拖动手柄 */}
            <div
                className="flex items-center justify-between px-2 py-1 bg-gray-50 rounded -mx-2 -mt-2 mb-1"
            >
                <div
                    className="flex-1 cursor-grab active:cursor-grabbing flex items-center gap-2"
                    onMouseDown={handleDragStart}
                >
                    <FiMove size={14} className="text-gray-400" />
                    <span className="text-xs text-gray-600 font-medium">标注工具</span>
                </div>
                <button
                    onClick={() => setIsCollapsed(!isCollapsed)}
                    className="p-1 hover:bg-gray-200 rounded transition-colors"
                    title={isCollapsed ? "展开" : "折叠"}
                >
                    <span className="text-gray-600 text-sm">{isCollapsed ? '⊕' : '⊖'}</span>
                </button>
            </div>

            {!isCollapsed && (
                <>
                    {/* 选择工具 */}
                    <button
                        onClick={() => onModeChange(MODES.NONE)}
                        className={clsx(
                            'p-2.5 rounded-lg transition-colors flex items-center gap-2 text-sm',
                            currentMode === MODES.NONE
                                ? 'bg-blue-50 text-blue-600 font-medium'
                                : 'hover:bg-gray-100 text-gray-700'
                        )}
                        title="选择工具 (V)"
                    >
                        <FiMousePointer size={18} />
                        <span>选择</span>
                    </button>

                    <div className="h-px bg-gray-200 my-1"></div>

                    {/* 画笔工具 */}
                    <button
                        onClick={() => onModeChange(MODES.INK)}
                        className={clsx(
                            'p-2.5 rounded-lg transition-colors flex items-center gap-2 text-sm',
                            currentMode === MODES.INK
                                ? 'bg-blue-50 text-blue-600 font-medium'
                                : 'hover:bg-gray-100 text-gray-700'
                        )}
                        title="画笔工具 (P)"
                    >
                        <FiEdit3 size={18} />
                        <span>画笔</span>
                    </button>

                    {/* 文本框工具 */}
                    <button
                        onClick={() => onModeChange(MODES.FREETEXT)}
                        className={clsx(
                            'p-2.5 rounded-lg transition-colors flex items-center gap-2 text-sm',
                            currentMode === MODES.FREETEXT
                                ? 'bg-blue-50 text-blue-600 font-medium'
                                : 'hover:bg-gray-100 text-gray-700'
                        )}
                        title="文本框 (T)"
                    >
                        <FiType size={18} />
                        <span>文本</span>
                    </button>

                    {/* 高亮工具 */}
                    <button
                        onClick={() => onModeChange(MODES.HIGHLIGHT)}
                        className={clsx(
                            'p-2.5 rounded-lg transition-colors flex items-center gap-2 text-sm',
                            currentMode === MODES.HIGHLIGHT
                                ? 'bg-yellow-50 text-yellow-600 font-medium'
                                : 'hover:bg-gray-100 text-gray-700'
                        )}
                        title="高亮工具 (H)"
                    >
                        <BsPencilSquare size={18} />
                        <span>高亮</span>
                    </button>

                    {/* 图章工具 */}
                    <button
                        onClick={() => onModeChange(MODES.STAMP)}
                        className={clsx(
                            'p-2.5 rounded-lg transition-colors flex items-center gap-2 text-sm',
                            currentMode === MODES.STAMP
                                ? 'bg-blue-50 text-blue-600 font-medium'
                                : 'hover:bg-gray-100 text-gray-700'
                        )}
                        title="图章 (S)"
                    >
                        <FiImage size={18} />
                        <span>图章</span>
                    </button>

                    <div className="h-px bg-gray-200 my-1"></div>

                    {/* 矩形工具 */}
                    <button
                        onClick={() => onModeChange(MODES.RECTANGLE)}
                        className={clsx(
                            'p-2.5 rounded-lg transition-colors flex items-center gap-2 text-sm',
                            currentMode === MODES.RECTANGLE
                                ? 'bg-blue-50 text-blue-600 font-medium'
                                : 'hover:bg-gray-100 text-gray-700'
                        )}
                        title="矩形 (R)"
                    >
                        <FiSquare size={18} />
                        <span>矩形</span>
                    </button>

                    {/* 圆形工具 */}
                    <button
                        onClick={() => onModeChange(MODES.CIRCLE)}
                        className={clsx(
                            'p-2.5 rounded-lg transition-colors flex items-center gap-2 text-sm',
                            currentMode === MODES.CIRCLE
                                ? 'bg-blue-50 text-blue-600 font-medium'
                                : 'hover:bg-gray-100 text-gray-700'
                        )}
                        title="圆形 (C)"
                    >
                        <FiCircle size={18} />
                        <span>圆形</span>
                    </button>

                    {/* 箭头工具 */}
                    <button
                        onClick={() => onModeChange(MODES.ARROW)}
                        className={clsx(
                            'p-2.5 rounded-lg transition-colors flex items-center gap-2 text-sm',
                            currentMode === MODES.ARROW
                                ? 'bg-blue-50 text-blue-600 font-medium'
                                : 'hover:bg-gray-100 text-gray-700'
                        )}
                        title="箭头 (A)"
                    >
                        <BsArrowUpRight size={18} />
                        <span>箭头</span>
                    </button>

                    <div className="h-px bg-gray-200 my-1"></div>

                    {/* 波浪线工具 */}
                    <button
                        onClick={() => onModeChange(MODES.WAVY_LINE)}
                        className={clsx(
                            'p-2.5 rounded-lg transition-colors flex items-center gap-2 text-sm',
                            currentMode === MODES.WAVY_LINE
                                ? 'bg-blue-50 text-blue-600 font-medium'
                                : 'hover:bg-gray-100 text-gray-700'
                        )}
                        title="波浪线"
                    >
                        <MdGesture size={18} />
                        <span>波浪线</span>
                    </button>

                    {/* 删除线工具 */}
                    <button
                        onClick={() => onModeChange(MODES.STRIKETHROUGH)}
                        className={clsx(
                            'p-2.5 rounded-lg transition-colors flex items-center gap-2 text-sm',
                            currentMode === MODES.STRIKETHROUGH
                                ? 'bg-blue-50 text-blue-600 font-medium'
                                : 'hover:bg-gray-100 text-gray-700'
                        )}
                        title="删除线"
                    >
                        <FiSlash size={18} />
                        <span>删除线</span>
                    </button>

                    <div className="h-px bg-gray-200 my-1"></div>

                    {/* 套索工具 */}
                    <button
                        onClick={() => onModeChange(MODES.LASSO)}
                        className={clsx(
                            'p-2.5 rounded-lg transition-colors flex items-center gap-2 text-sm',
                            currentMode === MODES.LASSO
                                ? 'bg-purple-50 text-purple-600 font-medium'
                                : 'hover:bg-gray-100 text-gray-700'
                        )}
                        title="套索选择"
                    >
                        <BsPentagon size={18} />
                        <span>套索</span>
                    </button>

                    {/* 橡皮擦工具 */}
                    <button
                        onClick={() => onModeChange(MODES.ERASER)}
                        className={clsx(
                            'p-2.5 rounded-lg transition-colors flex items-center gap-2 text-sm',
                            currentMode === MODES.ERASER
                                ? 'bg-red-50 text-red-600 font-medium'
                                : 'hover:bg-gray-100 text-gray-700'
                        )}
                        title="橡皮擦 (E)"
                    >
                        <FiTrash2 size={18} />
                        <span>橡皮擦</span>
                    </button>

                    <div className="h-px bg-gray-200 my-1"></div>

                    {/* 颜色选择 */}
                    {(currentMode === MODES.INK || currentMode === MODES.FREETEXT || currentMode === MODES.HIGHLIGHT ||
                        currentMode === MODES.RECTANGLE || currentMode === MODES.CIRCLE || currentMode === MODES.ARROW ||
                        currentMode === MODES.WAVY_LINE || currentMode === MODES.STRIKETHROUGH) && onColorChange && (
                            <>
                                <div className="px-2 py-1 text-xs text-gray-500 font-medium">
                                    颜色
                                </div>
                                <div className="px-2 py-1 grid grid-cols-3 gap-1">
                                    {colors.map((c) => (
                                        <button
                                            key={c}
                                            onClick={() => onColorChange(c)}
                                            className={clsx(
                                                'w-6 h-6 rounded border-2 transition-all',
                                                color === c ? 'border-gray-900 scale-110' : 'border-gray-300'
                                            )}
                                            style={{ backgroundColor: c }}
                                            title={c}
                                        />
                                    ))}
                                </div>
                            </>
                        )}

                    {/* 字体大小选择 - 仅文本工具 */}
                    {currentMode === MODES.FREETEXT && onFontSizeChange && (
                        <>
                            <div className="px-2 py-1 text-xs text-gray-500 font-medium">
                                字号
                            </div>
                            <div className="px-2 py-1 grid grid-cols-3 gap-1">
                                {fontSizes.map((size) => (
                                    <button
                                        key={size}
                                        onClick={() => onFontSizeChange(size)}
                                        className={clsx(
                                            'px-2 py-1 rounded text-xs transition-all',
                                            fontSize === size
                                                ? 'bg-blue-500 text-white font-medium'
                                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                        )}
                                        title={`${size}px`}
                                    >
                                        {size}
                                    </button>
                                ))}
                            </div>
                        </>
                    )}

                    {/* 粗细选择 - 支持所有绘图工具、高亮、橡皮擦、波浪线和删除线 */}
                    {(currentMode === MODES.INK || currentMode === MODES.HIGHLIGHT || currentMode === MODES.RECTANGLE ||
                        currentMode === MODES.CIRCLE || currentMode === MODES.ARROW || currentMode === MODES.ERASER ||
                        currentMode === MODES.WAVY_LINE || currentMode === MODES.STRIKETHROUGH) && onThicknessChange && (
                            <>
                                <div className="px-2 py-1 text-xs text-gray-500 font-medium">
                                    {currentMode === MODES.HIGHLIGHT ? '高度' : currentMode === MODES.ERASER ? '大小' : '粗细'}
                                </div>
                                <div className="px-2 py-1 flex gap-1">
                                    {thicknesses.map((t) => (
                                        <button
                                            key={t}
                                            onClick={() => onThicknessChange(t)}
                                            className={clsx(
                                                'w-8 h-8 rounded flex items-center justify-center transition-all',
                                                thickness === t ? 'bg-blue-100 border-2 border-blue-500' : 'bg-gray-100 border border-gray-300'
                                            )}
                                            title={`${currentMode === MODES.ERASER ? '橡皮擦大小' : '线条粗细'}: ${t}px`}
                                        >
                                            <div
                                                className="rounded-full"
                                                style={{
                                                    width: `${t * 2}px`,
                                                    height: `${t * 2}px`,
                                                    backgroundColor: thickness === t ? '#3b82f6' : '#6b7280'
                                                }}
                                            />
                                        </button>
                                    ))}
                                </div>
                            </>
                        )}

                    <div className="h-px bg-gray-200 my-1"></div>

                    {/* 缩放控制 */}
                    <div className="px-2 py-1 text-xs text-gray-500 font-medium">
                        缩放
                    </div>

                    <button
                        onClick={onZoomIn}
                        className="p-2 rounded-lg hover:bg-gray-100 text-gray-700 flex items-center justify-center"
                        title="放大 (+)"
                    >
                        <FiZoomIn size={18} />
                    </button>

                    <span className="text-xs text-center text-gray-600">
                        {Math.round(scale * 100)}%
                    </span>

                    <button
                        onClick={onZoomOut}
                        className="p-2 rounded-lg hover:bg-gray-100 text-gray-700 flex items-center justify-center"
                        title="缩小 (-)"
                    >
                        <FiZoomOut size={18} />
                    </button>
                </>
            )}
        </div>
    );
};
