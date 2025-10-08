/**
 * BookmarkPanel - 增强版书签管理面板
 * 
 * 功能：
 * - 显示、搜索、筛选书签
 * - 编辑书签（标题、笔记、标签）
 * - 跳转到书签位置
 * - 删除书签
 * - 按页码/创建时间排序
 */

import React, { useEffect, useState, useMemo } from 'react';
import {
    FiSearch,
    FiRefreshCw,
    FiEdit2,
    FiTrash2,
    FiBookmark,
    FiX,
    FiSave,
    FiChevronDown,
    FiChevronUp,
    FiFilter,
    FiPlus
} from 'react-icons/fi';
import apiService from '../services/api';
import type { Bookmark } from '../types';

interface Props {
    documentId?: string;
    onJumpTo?: (page: number, position: { x: number; y: number }) => void;
    currentSelection?: {
        text: string;
        pageNumber: number;
        position: { x: number; y: number; width: number; height: number };
    };
}

type SortBy = 'page' | 'created' | 'title';

const BookmarkPanel: React.FC<Props> = ({ documentId, onJumpTo, currentSelection }) => {
    // State
    const [bookmarks, setBookmarks] = useState<Bookmark[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [sortBy, setSortBy] = useState<SortBy>('page');
    const [expandedId, setExpandedId] = useState<string | null>(null);
    const [editingId, setEditingId] = useState<string | null>(null);
    const [editForm, setEditForm] = useState<{
        title: string;
        user_notes: string;
        tags: string[];
    }>({ title: '', user_notes: '', tags: [] });

    // Manual bookmark creation state
    const [isCreating, setIsCreating] = useState(false);
    const [createForm, setCreateForm] = useState<{
        page_number: number;
        title: string;
        selected_text: string;
        user_notes: string;
    }>({ page_number: 1, title: '', selected_text: '', user_notes: '' });

    useEffect(() => {
        loadBookmarks();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [documentId]);

    async function loadBookmarks() {
        setLoading(true);
        setError(null);
        try {
            const params: any = {};
            if (documentId) params.document_id = documentId;
            const data = await apiService.getBookmarks(params);
            setBookmarks(data.bookmarks || []);
        } catch (err: any) {
            setError(err?.response?.data?.detail || err?.message || '加载书签失败');
        } finally {
            setLoading(false);
        }
    }

    // 过滤和排序
    const filteredAndSortedBookmarks = useMemo(() => {
        let result = [...bookmarks];

        // 搜索过滤
        if (searchQuery.trim()) {
            const query = searchQuery.toLowerCase();
            result = result.filter(b =>
                b.title?.toLowerCase().includes(query) ||
                b.ai_summary.toLowerCase().includes(query) ||
                b.selected_text.toLowerCase().includes(query) ||
                b.user_notes?.toLowerCase().includes(query) ||
                b.tags?.some(tag => tag.toLowerCase().includes(query))
            );
        }

        // 排序
        result.sort((a, b) => {
            switch (sortBy) {
                case 'page':
                    return a.page_number - b.page_number;
                case 'created':
                    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
                case 'title':
                    const titleA = a.title || a.selected_text.slice(0, 50);
                    const titleB = b.title || b.selected_text.slice(0, 50);
                    return titleA.localeCompare(titleB);
                default:
                    return 0;
            }
        });

        return result;
    }, [bookmarks, searchQuery, sortBy]);

    function handleJump(bookmark: Bookmark) {
        // 触发全局跳转事件
        window.dispatchEvent(new CustomEvent('jumpToPage', {
            detail: { page_number: bookmark.page_number }
        }));

        // 同时调用回调（如果存在）
        if (onJumpTo) {
            onJumpTo(bookmark.page_number, {
                x: bookmark.position.x,
                y: bookmark.position.y
            });
        }
    }

    function startEdit(bookmark: Bookmark) {
        setEditingId(bookmark.id);
        setEditForm({
            title: bookmark.title || '',
            user_notes: bookmark.user_notes || '',
            tags: bookmark.tags || []
        });
    }

    function cancelEdit() {
        setEditingId(null);
        setEditForm({ title: '', user_notes: '', tags: [] });
    }

    async function saveEdit(bookmarkId: string) {
        try {
            const updated = await apiService.updateBookmark(bookmarkId, {
                title: editForm.title.trim() || undefined,
                user_notes: editForm.user_notes.trim() || undefined,
                tags: editForm.tags.length > 0 ? editForm.tags : undefined
            });
            setBookmarks(prev => prev.map(b => b.id === bookmarkId ? updated : b));
            setEditingId(null);
        } catch (err: any) {
            alert('保存失败: ' + (err?.response?.data?.detail || err?.message));
        }
    }

    async function handleDelete(bookmarkId: string) {
        if (!confirm('确定删除此书签？')) return;
        try {
            await apiService.deleteBookmark(bookmarkId);
            setBookmarks(prev => prev.filter(b => b.id !== bookmarkId));
        } catch (err: any) {
            alert('删除失败: ' + (err?.response?.data?.detail || err?.message));
        }
    }

    function toggleExpand(bookmarkId: string) {
        setExpandedId(prev => prev === bookmarkId ? null : bookmarkId);
    }

    // Manual bookmark creation
    function startCreating() {
        if (!currentSelection) {
            alert('请先在 PDF 上选中一段文字，然后再创建书签');
            return;
        }

        setIsCreating(true);
        setCreateForm({
            page_number: currentSelection.pageNumber,
            title: '',
            selected_text: currentSelection.text,
            user_notes: ''
        });
    }

    function cancelCreating() {
        setIsCreating(false);
        setCreateForm({ page_number: 1, title: '', selected_text: '', user_notes: '' });
    }

    async function handleCreate() {
        if (!documentId) {
            alert('缺少文档 ID');
            return;
        }
        if (!createForm.selected_text.trim()) {
            alert('请输入书签内容');
            return;
        }
        if (!currentSelection) {
            alert('选中的文字位置信息丢失，请重新选择文字');
            return;
        }

        setLoading(true);
        try {
            const newBookmark = await apiService.createBookmark({
                document_id: documentId,
                page_number: currentSelection.pageNumber,
                selected_text: createForm.selected_text.trim(),
                title: createForm.title.trim() || undefined,
                user_notes: createForm.user_notes.trim() || undefined,
                position: currentSelection.position, // Use actual selection position
                ai_summary: createForm.selected_text.trim() // Use selected text as summary
            });
            setBookmarks(prev => [...prev, newBookmark]);
            cancelCreating();
        } catch (err: any) {
            alert('创建失败: ' + (err?.response?.data?.detail || err?.message));
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="flex flex-col h-full bg-white shadow-lg rounded-lg overflow-hidden">
            {/* Header */}
            <div className="px-4 py-3 bg-gradient-to-r from-blue-500 to-indigo-600 text-white">
                <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                        <FiBookmark className="w-5 h-5" />
                        <h3 className="text-lg font-semibold">书签目录</h3>
                        {bookmarks.length > 0 && (
                            <span className="text-xs bg-white/20 px-2 py-0.5 rounded-full">
                                {filteredAndSortedBookmarks.length}/{bookmarks.length}
                            </span>
                        )}
                    </div>
                    <div className="flex gap-1">
                        <button
                            className="p-1.5 hover:bg-white/20 rounded transition-colors"
                            onClick={startCreating}
                            disabled={loading || isCreating}
                            title="添加书签"
                        >
                            <FiPlus className="w-4 h-4" />
                        </button>
                        <button
                            className="p-1.5 hover:bg-white/20 rounded transition-colors"
                            onClick={loadBookmarks}
                            disabled={loading}
                            title="刷新"
                        >
                            <FiRefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                        </button>
                    </div>
                </div>

                {/* Search Bar */}
                <div className="relative">
                    <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/60" />
                    <input
                        type="text"
                        placeholder="搜索书签内容、标题、标签..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-9 pr-3 py-2 bg-white/10 border border-white/20 rounded text-sm text-white placeholder-white/50 focus:outline-none focus:bg-white/20"
                    />
                </div>
            </div>

            {/* Sort Controls */}
            <div className="px-4 py-2 bg-gray-50 border-b flex items-center gap-2">
                <FiFilter className="w-4 h-4 text-gray-500" />
                <span className="text-xs text-gray-600">排序:</span>
                <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value as SortBy)}
                    className="text-xs border border-gray-300 rounded px-2 py-1 focus:outline-none focus:border-blue-500"
                >
                    <option value="page">页码</option>
                    <option value="created">创建时间</option>
                    <option value="title">标题</option>
                </select>
            </div>

            {/* Create Bookmark Form */}
            {isCreating && (
                <div className="px-4 py-3 bg-blue-50 border-b">
                    <div className="flex items-center justify-between mb-2">
                        <h4 className="text-sm font-semibold text-gray-700">新建书签</h4>
                        <button
                            onClick={cancelCreating}
                            className="text-gray-500 hover:text-gray-700"
                            title="取消"
                        >
                            <FiX className="w-4 h-4" />
                        </button>
                    </div>
                    <div className="space-y-2">
                        {/* Show current selection info */}
                        {currentSelection && (
                            <div className="p-2 bg-blue-100 border border-blue-200 rounded text-xs">
                                <div className="font-semibold text-blue-800 mb-1">
                                    选中位置: 第 {currentSelection.pageNumber} 页
                                </div>
                                <div className="text-blue-700 max-h-12 overflow-y-auto">
                                    {currentSelection.text.substring(0, 100)}
                                    {currentSelection.text.length > 100 && '...'}
                                </div>
                            </div>
                        )}

                        <div>
                            <label className="block text-xs text-gray-600 mb-1">书签内容 *</label>
                            <textarea
                                value={createForm.selected_text}
                                onChange={(e) => setCreateForm(prev => ({ ...prev, selected_text: e.target.value }))}
                                className="w-full px-2 py-1 text-sm border rounded focus:outline-none focus:border-blue-500 resize-none"
                                rows={3}
                                placeholder="已自动填充选中的文字，可以编辑..."
                                readOnly={false}
                            />
                        </div>
                        <div>
                            <label className="block text-xs text-gray-600 mb-1">标题（可选）</label>
                            <input
                                type="text"
                                value={createForm.title}
                                onChange={(e) => setCreateForm(prev => ({ ...prev, title: e.target.value }))}
                                className="w-full px-2 py-1 text-sm border rounded focus:outline-none focus:border-blue-500"
                                placeholder="输入书签标题..."
                            />
                        </div>
                        <div>
                            <label className="block text-xs text-gray-600 mb-1">笔记（可选）</label>
                            <textarea
                                value={createForm.user_notes}
                                onChange={(e) => setCreateForm(prev => ({ ...prev, user_notes: e.target.value }))}
                                className="w-full px-2 py-1 text-sm border rounded focus:outline-none focus:border-blue-500 resize-none"
                                rows={2}
                                placeholder="添加笔记..."
                            />
                        </div>
                        <div className="flex justify-end gap-2 pt-2">
                            <button
                                onClick={cancelCreating}
                                className="px-3 py-1 text-sm text-gray-600 hover:bg-gray-100 rounded transition-colors"
                            >
                                取消
                            </button>
                            <button
                                onClick={handleCreate}
                                disabled={!createForm.selected_text.trim() || loading}
                                className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                            >
                                创建
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Loading/Error States */}
            {loading && (
                <div className="flex-1 flex items-center justify-center">
                    <div className="text-center">
                        <FiRefreshCw className="w-8 h-8 text-blue-500 animate-spin mx-auto mb-2" />
                        <p className="text-sm text-gray-500">加载中...</p>
                    </div>
                </div>
            )}

            {error && !loading && (
                <div className="mx-4 mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-sm text-red-600">{error}</p>
                    <button
                        className="mt-2 text-xs text-red-700 underline"
                        onClick={loadBookmarks}
                    >
                        重试
                    </button>
                </div>
            )}

            {/* Empty State */}
            {!loading && !error && filteredAndSortedBookmarks.length === 0 && (
                <div className="flex-1 flex items-center justify-center">
                    <div className="text-center px-4">
                        <FiBookmark className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                        <p className="text-sm text-gray-500">
                            {searchQuery ? '未找到匹配的书签' : '还没有书签'}
                        </p>
                        <p className="text-xs text-gray-400 mt-1">
                            {searchQuery ? '尝试修改搜索关键词' : '选中PDF文本并与AI对话后可生成书签'}
                        </p>
                    </div>
                </div>
            )}

            {/* Bookmark List */}
            {!loading && !error && filteredAndSortedBookmarks.length > 0 && (
                <div className="flex-1 overflow-y-auto">
                    <ul className="divide-y divide-gray-200">
                        {filteredAndSortedBookmarks.map(bookmark => {
                            const isExpanded = expandedId === bookmark.id;
                            const isEditing = editingId === bookmark.id;

                            return (
                                <li
                                    key={bookmark.id}
                                    className="px-4 py-3 hover:bg-gray-50 transition-colors"
                                    style={{ borderLeftWidth: '4px', borderLeftColor: bookmark.color || '#FCD34D' }}
                                >
                                    {/* Bookmark Header */}
                                    <div className="flex items-start justify-between gap-2">
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2">
                                                <button
                                                    onClick={() => toggleExpand(bookmark.id)}
                                                    className="text-gray-400 hover:text-gray-600"
                                                >
                                                    {isExpanded ? <FiChevronUp /> : <FiChevronDown />}
                                                </button>
                                                <h4 className="font-medium text-sm truncate">
                                                    {bookmark.title || bookmark.selected_text.slice(0, 60) + '...'}
                                                </h4>
                                            </div>
                                            <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
                                                <span>第 {bookmark.page_number} 页</span>
                                                {bookmark.tags && bookmark.tags.length > 0 && (
                                                    <>
                                                        <span>•</span>
                                                        <div className="flex gap-1">
                                                            {bookmark.tags.slice(0, 2).map((tag, i) => (
                                                                <span key={i} className="px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded">
                                                                    {tag}
                                                                </span>
                                                            ))}
                                                            {bookmark.tags.length > 2 && (
                                                                <span className="px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded">
                                                                    +{bookmark.tags.length - 2}
                                                                </span>
                                                            )}
                                                        </div>
                                                    </>
                                                )}
                                            </div>
                                        </div>

                                        {/* Actions */}
                                        <div className="flex items-center gap-1">
                                            <button
                                                onClick={() => handleJump(bookmark)}
                                                className="p-1.5 text-blue-600 hover:bg-blue-50 rounded transition-colors"
                                                title="跳转"
                                            >
                                                <FiBookmark className="w-4 h-4" />
                                            </button>
                                            {!isEditing && (
                                                <button
                                                    onClick={() => startEdit(bookmark)}
                                                    className="p-1.5 text-gray-600 hover:bg-gray-100 rounded transition-colors"
                                                    title="编辑"
                                                >
                                                    <FiEdit2 className="w-4 h-4" />
                                                </button>
                                            )}
                                            <button
                                                onClick={() => handleDelete(bookmark.id)}
                                                className="p-1.5 text-red-600 hover:bg-red-50 rounded transition-colors"
                                                title="删除"
                                            >
                                                <FiTrash2 className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </div>

                                    {/* AI Summary */}
                                    <div className="mt-2 text-sm text-gray-700 bg-blue-50 p-2 rounded">
                                        <span className="font-medium text-blue-700">AI摘要: </span>
                                        {bookmark.ai_summary}
                                    </div>

                                    {/* Expanded Content */}
                                    {isExpanded && (
                                        <div className="mt-3 space-y-2 text-sm">
                                            {/* Edit Form */}
                                            {isEditing ? (
                                                <div className="space-y-3 p-3 bg-gray-50 rounded">
                                                    <div>
                                                        <label className="block text-xs font-medium text-gray-700 mb-1">
                                                            标题
                                                        </label>
                                                        <input
                                                            type="text"
                                                            value={editForm.title}
                                                            onChange={(e) => setEditForm(prev => ({ ...prev, title: e.target.value }))}
                                                            className="w-full px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:border-blue-500"
                                                            placeholder="书签标题"
                                                        />
                                                    </div>
                                                    <div>
                                                        <label className="block text-xs font-medium text-gray-700 mb-1">
                                                            笔记
                                                        </label>
                                                        <textarea
                                                            value={editForm.user_notes}
                                                            onChange={(e) => setEditForm(prev => ({ ...prev, user_notes: e.target.value }))}
                                                            className="w-full px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:border-blue-500"
                                                            rows={3}
                                                            placeholder="添加您的笔记..."
                                                        />
                                                    </div>
                                                    <div>
                                                        <label className="block text-xs font-medium text-gray-700 mb-1">
                                                            标签 (用逗号分隔)
                                                        </label>
                                                        <input
                                                            type="text"
                                                            value={editForm.tags.join(', ')}
                                                            onChange={(e) => setEditForm(prev => ({
                                                                ...prev,
                                                                tags: e.target.value.split(',').map(t => t.trim()).filter(Boolean)
                                                            }))}
                                                            className="w-full px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:border-blue-500"
                                                            placeholder="标签1, 标签2, ..."
                                                        />
                                                    </div>
                                                    <div className="flex gap-2">
                                                        <button
                                                            onClick={() => saveEdit(bookmark.id)}
                                                            className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white rounded text-xs hover:bg-blue-700"
                                                        >
                                                            <FiSave className="w-3 h-3" />
                                                            保存
                                                        </button>
                                                        <button
                                                            onClick={cancelEdit}
                                                            className="flex items-center gap-1 px-3 py-1.5 bg-gray-200 text-gray-700 rounded text-xs hover:bg-gray-300"
                                                        >
                                                            <FiX className="w-3 h-3" />
                                                            取消
                                                        </button>
                                                    </div>
                                                </div>
                                            ) : (
                                                <>
                                                    {/* Selected Text */}
                                                    <div>
                                                        <span className="font-medium text-gray-700">选中文本:</span>
                                                        <p className="mt-1 text-gray-600 bg-yellow-50 p-2 rounded text-xs">
                                                            {bookmark.selected_text}
                                                        </p>
                                                    </div>

                                                    {/* User Notes */}
                                                    {bookmark.user_notes && (
                                                        <div>
                                                            <span className="font-medium text-gray-700">我的笔记:</span>
                                                            <p className="mt-1 text-gray-600 bg-green-50 p-2 rounded text-xs">
                                                                {bookmark.user_notes}
                                                            </p>
                                                        </div>
                                                    )}

                                                    {/* Metadata */}
                                                    <div className="text-xs text-gray-500 pt-2 border-t">
                                                        创建时间: {new Date(bookmark.created_at).toLocaleString('zh-CN')}
                                                    </div>
                                                </>
                                            )}
                                        </div>
                                    )}
                                </li>
                            );
                        })}
                    </ul>
                </div>
            )}
        </div>
    );
};

export default BookmarkPanel;
