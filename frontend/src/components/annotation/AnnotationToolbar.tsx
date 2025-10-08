/**
 * Annotation Toolbar Component
 * 
 * Floating toolbar for annotation tools
 */

import { FiSquare, FiCircle, FiArrowRight, FiMessageSquare, FiMousePointer } from 'react-icons/fi';
import clsx from 'clsx';

type ShapeType = 'rectangle' | 'circle' | 'line' | 'arrow' | 'polygon' | null;
type AnnotationMode = 'text' | 'shape' | 'ink' | 'note' | 'select' | null;

interface AnnotationToolbarProps {
    mode: AnnotationMode;
    shapeTool: ShapeType;
    onModeChange: (mode: AnnotationMode) => void;
    onShapeToolChange: (tool: ShapeType) => void;
    onCancel: () => void;
}

export const AnnotationToolbar: React.FC<AnnotationToolbarProps> = ({
    mode,
    shapeTool,
    onModeChange,
    onShapeToolChange,
    onCancel,
}) => {
    return (
        <div className="fixed left-4 top-24 z-50 bg-white rounded-lg shadow-xl border border-gray-200 p-2">
            <div className="flex flex-col gap-1">
                {/* Select tool */}
                <button
                    onClick={() => {
                        onModeChange(null);
                        onCancel();
                    }}
                    className={clsx(
                        'p-2.5 rounded-lg transition-colors flex items-center gap-2 text-sm',
                        mode === null
                            ? 'bg-blue-50 text-blue-600 font-medium'
                            : 'hover:bg-gray-100 text-gray-700'
                    )}
                    title="选择工具 (V)"
                >
                    <FiMousePointer size={18} />
                    <span>选择</span>
                </button>

                {/* Divider */}
                <div className="h-px bg-gray-200 my-1"></div>

                {/* Text markup (handled by selection toolbar) */}
                <div className="px-2 py-1 text-xs text-gray-500 font-medium">
                    文本标注
                </div>
                <div className="px-2 py-1 text-xs text-gray-600">
                    选中文字即可标注
                </div>

                {/* Divider */}
                <div className="h-px bg-gray-200 my-1"></div>

                {/* Shape tools */}
                <div className="px-2 py-1 text-xs text-gray-500 font-medium">
                    图形工具
                </div>

                <button
                    onClick={() => {
                        onModeChange('shape');
                        onShapeToolChange('rectangle');
                    }}
                    className={clsx(
                        'p-2.5 rounded-lg transition-colors flex items-center gap-2 text-sm',
                        mode === 'shape' && shapeTool === 'rectangle'
                            ? 'bg-blue-50 text-blue-600 font-medium'
                            : 'hover:bg-gray-100 text-gray-700'
                    )}
                    title="矩形 (R)"
                >
                    <FiSquare size={18} />
                    <span>矩形</span>
                </button>

                <button
                    onClick={() => {
                        onModeChange('shape');
                        onShapeToolChange('circle');
                    }}
                    className={clsx(
                        'p-2.5 rounded-lg transition-colors flex items-center gap-2 text-sm',
                        mode === 'shape' && shapeTool === 'circle'
                            ? 'bg-blue-50 text-blue-600 font-medium'
                            : 'hover:bg-gray-100 text-gray-700'
                    )}
                    title="圆形 (C)"
                >
                    <FiCircle size={18} />
                    <span>圆形</span>
                </button>

                <button
                    onClick={() => {
                        onModeChange('shape');
                        onShapeToolChange('arrow');
                    }}
                    className={clsx(
                        'p-2.5 rounded-lg transition-colors flex items-center gap-2 text-sm',
                        mode === 'shape' && shapeTool === 'arrow'
                            ? 'bg-blue-50 text-blue-600 font-medium'
                            : 'hover:bg-gray-100 text-gray-700'
                    )}
                    title="箭头 (A)"
                >
                    <FiArrowRight size={18} />
                    <span>箭头</span>
                </button>

                {/* Divider */}
                <div className="h-px bg-gray-200 my-1"></div>

                {/* Note tool */}
                <button
                    onClick={() => {
                        onModeChange('note');
                    }}
                    className={clsx(
                        'p-2.5 rounded-lg transition-colors flex items-center gap-2 text-sm',
                        mode === 'note'
                            ? 'bg-yellow-50 text-yellow-700 font-medium'
                            : 'hover:bg-gray-100 text-gray-700'
                    )}
                    title="便笺 (N)"
                >
                    <FiMessageSquare size={18} />
                    <span>便笺</span>
                </button>

                {/* Instruction */}
                {mode === 'shape' && shapeTool && (
                    <>
                        <div className="h-px bg-gray-200 my-1"></div>
                        <div className="px-2 py-1 text-xs text-blue-600 bg-blue-50 rounded">
                            <div className="font-medium mb-1">绘制 {
                                shapeTool === 'rectangle' ? '矩形' :
                                    shapeTool === 'circle' ? '圆形' :
                                        shapeTool === 'arrow' ? '箭头' : '图形'
                            }</div>
                            <div className="text-blue-500">
                                点击拖拽绘制
                                <br />
                                ESC 取消
                            </div>
                        </div>
                    </>
                )}

                {mode === 'note' && (
                    <>
                        <div className="h-px bg-gray-200 my-1"></div>
                        <div className="px-2 py-1 text-xs text-yellow-700 bg-yellow-50 rounded">
                            <div className="font-medium mb-1">添加便笺</div>
                            <div className="text-yellow-600">
                                点击页面放置
                                <br />
                                ESC 取消
                            </div>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};
