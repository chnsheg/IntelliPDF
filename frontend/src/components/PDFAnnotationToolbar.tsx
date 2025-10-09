/**
 * PDF Annotation Toolbar - Simplified
 * 
 * 只包含 PDF.js 原生支持的标注工具
 */

import React from 'react';
import { FiMousePointer, FiEdit3, FiType, FiImage, FiZoomIn, FiZoomOut } from 'react-icons/fi';
import clsx from 'clsx';

interface PDFAnnotationToolbarProps {
    currentMode: number;
    onModeChange: (mode: number) => void;
    onZoomIn: () => void;
    onZoomOut: () => void;
    scale: number;
}

// PDF.js 标注模式常量
const MODES = {
    NONE: 0,        // 选择/查看模式
    FREETEXT: 3,    // 文本框
    INK: 15,        // 画笔/手绘
    STAMP: 13,      // 图章
};

export const PDFAnnotationToolbar: React.FC<PDFAnnotationToolbarProps> = ({
    currentMode,
    onModeChange,
    onZoomIn,
    onZoomOut,
    scale,
}) => {
    return (
        <div className="fixed left-4 top-24 z-50 bg-white rounded-lg shadow-xl border border-gray-200 p-2 flex flex-col gap-1">
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
        </div>
    );
};
