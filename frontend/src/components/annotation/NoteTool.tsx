/**
 * NoteTool - 便笺标注工具
 * 
 * 功能:
 * - 点击 PDF 页面放置便笺图标
 * - 点击便笺图标打开编辑框
 * - 支持文本内容编辑
 * - 便笺拖拽移动
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { FiMessageSquare, FiX, FiSave } from 'react-icons/fi';

interface NoteData {
    id: string;
    pageNumber: number;
    position: {
        x: number;
        y: number;
    };
    content: string;
    color: string;
    author?: string;
    createdAt?: string;
}

interface NoteToolProps {
    /** 当前页码 */
    pageNumber: number;
    /** PDF 页面对象 */
    pdfPage: any;
    /** 缩放比例 */
    scale: number;
    /** 现有的便笺列表 */
    notes?: NoteData[];
    /** 便笺创建完成回调 */
    onNoteComplete: (note: NoteData) => void;
    /** 便笺更新回调 */
    onNoteUpdate?: (noteId: string, content: string) => void;
    /** 便笺删除回调 */
    onNoteDelete?: (noteId: string) => void;
    /** 取消回调 */
    onCancel: () => void;
}

export const NoteTool: React.FC<NoteToolProps> = ({
    pageNumber,
    pdfPage,
    scale,
    notes = [],
    onNoteComplete,
    onNoteUpdate,
    onNoteDelete,
    onCancel,
}) => {
    const [isPlacing, setIsPlacing] = useState(true);
    const [editingNoteId, setEditingNoteId] = useState<string | null>(null);
    const [editContent, setEditContent] = useState('');
    const [currentColor, setCurrentColor] = useState('#FFD54F');

    const overlayRef = useRef<HTMLDivElement>(null);

    /**
     * 处理点击事件 - 放置新便笺
     */
    const handleClick = useCallback((event: React.MouseEvent<HTMLDivElement>) => {
        if (!isPlacing) return;

        const rect = event.currentTarget.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;

        // 转换为 PDF 坐标
        const viewport = pdfPage.getViewport({ scale });
        const pdfX = x / scale;
        const pdfY = viewport.height / scale - y / scale;

        // 创建新便笺
        const newNote: NoteData = {
            id: `note-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            pageNumber,
            position: { x: pdfX, y: pdfY },
            content: '',
            color: currentColor,
            author: localStorage.getItem('user_name') || 'Anonymous',
            createdAt: new Date().toISOString(),
        };

        // 立即进入编辑模式
        setIsPlacing(false);
        setEditingNoteId(newNote.id);
        setEditContent('');

        // 通知父组件（但先不保存，等用户输入内容）
        onNoteComplete(newNote);
    }, [isPlacing, pageNumber, pdfPage, scale, currentColor, onNoteComplete]);

    /**
     * 保存便笺内容
     */
    const handleSaveNote = useCallback(() => {
        if (!editingNoteId || !editContent.trim()) {
            alert('请输入便笺内容');
            return;
        }

        if (onNoteUpdate) {
            onNoteUpdate(editingNoteId, editContent);
        }

        setEditingNoteId(null);
        setEditContent('');
        setIsPlacing(true); // 可以继续放置新便笺
    }, [editingNoteId, editContent, onNoteUpdate]);

    /**
     * 取消编辑
     */
    const handleCancelEdit = useCallback(() => {
        if (editingNoteId && !editContent.trim()) {
            // 如果是新便笺且没有内容，删除它
            if (onNoteDelete) {
                onNoteDelete(editingNoteId);
            }
        }

        setEditingNoteId(null);
        setEditContent('');
        setIsPlacing(true);
    }, [editingNoteId, editContent, onNoteDelete]);

    /**
     * 处理 ESC 键退出工具
     */
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape') {
                if (editingNoteId) {
                    handleCancelEdit();
                } else {
                    onCancel();
                }
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [editingNoteId, handleCancelEdit, onCancel]);

    /**
     * 渲染便笺图标
     */
    const renderNoteIcon = useCallback((note: NoteData) => {
        const viewport = pdfPage.getViewport({ scale });
        const screenX = note.position.x * scale;
        const screenY = (viewport.height / scale - note.position.y) * scale;

        const isEditing = note.id === editingNoteId;

        return (
            <div
                key={note.id}
                className="absolute cursor-pointer transform -translate-x-1/2 -translate-y-1/2"
                style={{
                    left: `${screenX}px`,
                    top: `${screenY}px`,
                }}
                onClick={(e) => {
                    e.stopPropagation();
                    if (!isEditing) {
                        setEditingNoteId(note.id);
                        setEditContent(note.content);
                        setIsPlacing(false);
                    }
                }}
            >
                <div
                    className="w-10 h-10 rounded-full flex items-center justify-center shadow-lg transition-transform hover:scale-110"
                    style={{
                        backgroundColor: note.color,
                        border: isEditing ? '3px solid #2196F3' : '2px solid rgba(0,0,0,0.2)',
                    }}
                >
                    <FiMessageSquare size={20} className="text-gray-800" />
                </div>
                {note.content && (
                    <div className="absolute top-12 left-1/2 transform -translate-x-1/2 bg-white px-2 py-1 rounded shadow text-xs max-w-xs truncate whitespace-nowrap">
                        {note.content}
                    </div>
                )}
            </div>
        );
    }, [pdfPage, scale, editingNoteId]);

    /**
     * 渲染编辑弹出框
     */
    const renderEditPopup = useCallback(() => {
        if (!editingNoteId) return null;

        const note = notes.find(n => n.id === editingNoteId);
        if (!note) return null;

        const viewport = pdfPage.getViewport({ scale });
        const screenX = note.position.x * scale;
        const screenY = (viewport.height / scale - note.position.y) * scale;

        return (
            <div
                className="absolute z-50 bg-white rounded-lg shadow-2xl border-2 border-blue-400"
                style={{
                    left: `${screenX + 30}px`,
                    top: `${screenY - 60}px`,
                    width: '320px',
                }}
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex items-center justify-between px-4 py-2 bg-blue-50 border-b">
                    <div className="flex items-center gap-2">
                        <FiMessageSquare size={16} className="text-blue-600" />
                        <span className="text-sm font-medium text-gray-700">编辑便笺</span>
                    </div>
                    <button
                        onClick={handleCancelEdit}
                        className="p-1 hover:bg-blue-100 rounded transition-colors"
                    >
                        <FiX size={16} className="text-gray-600" />
                    </button>
                </div>

                {/* Content */}
                <div className="p-4">
                    <textarea
                        autoFocus
                        value={editContent}
                        onChange={(e) => setEditContent(e.target.value)}
                        placeholder="输入便笺内容..."
                        className="w-full h-32 px-3 py-2 border border-gray-300 rounded resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                </div>

                {/* Footer */}
                <div className="flex items-center justify-between px-4 py-3 bg-gray-50 border-t">
                    <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-500">颜色:</span>
                        {['#FFD54F', '#FF8A65', '#81C784', '#64B5F6', '#BA68C8'].map(color => (
                            <button
                                key={color}
                                onClick={() => setCurrentColor(color)}
                                className="w-6 h-6 rounded-full border-2 hover:scale-110 transition-transform"
                                style={{
                                    backgroundColor: color,
                                    borderColor: currentColor === color ? '#2196F3' : 'transparent',
                                }}
                            />
                        ))}
                    </div>
                    <button
                        onClick={handleSaveNote}
                        className="flex items-center gap-1 px-4 py-1.5 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors text-sm"
                    >
                        <FiSave size={14} />
                        保存
                    </button>
                </div>
            </div>
        );
    }, [editingNoteId, notes, pdfPage, scale, editContent, currentColor, handleSaveNote, handleCancelEdit]);

    return (
        <>
            {/* 点击覆盖层 */}
            {isPlacing && (
                <div
                    ref={overlayRef}
                    className="absolute inset-0 cursor-crosshair z-40"
                    onClick={handleClick}
                    style={{ backgroundColor: 'rgba(255, 213, 79, 0.05)' }}
                >
                    <div className="absolute top-4 left-1/2 transform -translate-x-1/2 bg-yellow-100 px-4 py-2 rounded-lg shadow-md border border-yellow-300">
                        <p className="text-sm text-gray-700">
                            <FiMessageSquare className="inline mr-2" />
                            点击页面放置便笺 | <kbd className="px-1 py-0.5 bg-white rounded text-xs">ESC</kbd> 取消
                        </p>
                    </div>
                </div>
            )}

            {/* 渲染所有便笺图标 */}
            {notes.map(renderNoteIcon)}

            {/* 编辑弹出框 */}
            {renderEditPopup()}
        </>
    );
};
