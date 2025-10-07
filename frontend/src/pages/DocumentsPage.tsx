/**
 * Documents Management Page with advanced features
 */

import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
    FiSearch,
    FiDownload,
    FiTrash2,
    FiEye,
    FiClock,
    FiFileText,
    FiCheckSquare,
    FiSquare,
    FiRefreshCw,
} from 'react-icons/fi';
import clsx from 'clsx';
import { apiService } from '../services/api';
import { useToast } from '../components/Toast';
import { Spinner, CardSkeleton } from '../components/Loading';

export default function DocumentsPage() {
    const navigate = useNavigate();
    const queryClient = useQueryClient();
    const { showToast } = useToast();
    const [searchQuery, setSearchQuery] = useState('');
    const [statusFilter, setStatusFilter] = useState<string>('all');
    const [sortBy, setSortBy] = useState<'created_at' | 'title' | 'file_size'>('created_at');
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
    const [selectedDocs, setSelectedDocs] = useState<Set<string>>(new Set());

    // Fetch documents
    const { data: documents, isLoading } = useQuery({
        queryKey: ['documents', searchQuery, statusFilter, sortBy, sortOrder],
        queryFn: async () => {
            const data = await apiService.searchDocuments({
                query: searchQuery || undefined,
                status: statusFilter !== 'all' ? statusFilter : undefined,
                sort_by: sortBy,
                sort_order: sortOrder,
                limit: 50,
            });
            return data;
        },
    });

    // Fetch statistics
    const { data: stats } = useQuery({
        queryKey: ['document-stats'],
        queryFn: async () => {
            // 使用基础统计 API（enhanced API 暂不可用）
            const data = await apiService.getDocumentStatistics();
            return data || {};
        },
    });

    // Batch delete mutation
    const deleteMutation = useMutation({
        mutationFn: async (docIds: string[]) => {
            return apiService.batchDeleteDocuments({ document_ids: docIds });
        },
        onSuccess: () => {
            showToast('success', '文档删除成功');
            setSelectedDocs(new Set());
            queryClient.invalidateQueries({ queryKey: ['documents'] });
            queryClient.invalidateQueries({ queryKey: ['document-stats'] });
        },
        onError: () => {
            showToast('error', '删除失败,请重试');
        },
    });

    // Filter documents
    const filteredDocuments = useMemo(() => {
        if (!documents) return [];
        return documents;
    }, [documents]);

    // Selection handlers
    const toggleSelectAll = () => {
        if (selectedDocs.size === filteredDocuments.length) {
            setSelectedDocs(new Set());
        } else {
            setSelectedDocs(new Set(filteredDocuments.map((d: any) => d.id)));
        }
    };

    const toggleSelect = (docId: string) => {
        const newSelected = new Set(selectedDocs);
        if (newSelected.has(docId)) {
            newSelected.delete(docId);
        } else {
            newSelected.add(docId);
        }
        setSelectedDocs(newSelected);
    };

    const handleBatchDelete = () => {
        if (selectedDocs.size === 0) return;

        if (confirm(`确定要删除选中的 ${selectedDocs.size} 个文档吗？`)) {
            deleteMutation.mutate(Array.from(selectedDocs));
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white p-6">
            {/* Header */}
            <div className="mb-8 animate-fadeInUp">
                <h1 className="text-3xl font-bold bg-gradient-to-r from-primary-600 to-accent-600 bg-clip-text text-transparent mb-2">
                    文档管理
                </h1>
                <p className="text-gray-600">管理和搜索您的所有文档</p>
            </div>

            {/* Statistics Cards */}
            {stats && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8 animate-fadeInUp" style={{ animationDelay: '100ms' }}>
                    <div className="card-glass p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-600 mb-1">总文档数</p>
                                <p className="text-3xl font-bold text-primary-600">
                                    {stats.total}
                                </p>
                            </div>
                            <FiFileText className="w-12 h-12 text-primary-500 opacity-20" />
                        </div>
                    </div>

                    <div className="card-glass p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-600 mb-1">已完成</p>
                                <p className="text-3xl font-bold text-green-600">
                                    {stats.by_status?.completed || 0}
                                </p>
                            </div>
                            <FiCheckSquare className="w-12 h-12 text-green-500 opacity-20" />
                        </div>
                    </div>

                    <div className="card-glass p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-600 mb-1">处理中</p>
                                <p className="text-3xl font-bold text-orange-600">
                                    {stats.by_status?.processing || 0}
                                </p>
                            </div>
                            <FiClock className="w-12 h-12 text-orange-500 opacity-20" />
                        </div>
                    </div>

                    <div className="card-glass p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-600 mb-1">存储空间</p>
                                <p className="text-2xl font-bold text-purple-600">
                                    {(stats.total_size / 1024 / 1024).toFixed(2)} MB
                                </p>
                            </div>
                            <FiDownload className="w-12 h-12 text-purple-500 opacity-20" />
                        </div>
                    </div>
                </div>
            )}

            {/* Toolbar */}
            <div className="card-glass p-4 mb-6 animate-fadeInUp" style={{ animationDelay: '200ms' }}>
                <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
                    {/* Search */}
                    <div className="flex-1 w-full md:w-auto">
                        <div className="relative">
                            <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                placeholder="搜索文档标题或文件名..."
                                className="w-full pl-10 pr-4 py-2 border-2 border-gray-200 rounded-lg focus:border-primary-500 focus:ring-4 focus:ring-primary-500/10 transition-all duration-300 outline-none"
                            />
                        </div>
                    </div>

                    {/* Filters */}
                    <div className="flex gap-2 flex-wrap">
                        <select
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                            className="px-4 py-2 border-2 border-gray-200 rounded-lg focus:border-primary-500 focus:ring-4 focus:ring-primary-500/10 transition-all duration-300 outline-none"
                        >
                            <option value="all">所有状态</option>
                            <option value="completed">已完成</option>
                            <option value="processing">处理中</option>
                            <option value="failed">失败</option>
                        </select>

                        <select
                            value={sortBy}
                            onChange={(e) => setSortBy(e.target.value as any)}
                            className="px-4 py-2 border-2 border-gray-200 rounded-lg focus:border-primary-500 focus:ring-4 focus:ring-primary-500/10 transition-all duration-300 outline-none"
                        >
                            <option value="created_at">创建时间</option>
                            <option value="title">标题</option>
                            <option value="file_size">文件大小</option>
                        </select>

                        <button
                            onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                            className="px-4 py-2 border-2 border-gray-200 rounded-lg hover:border-primary-500 transition-all duration-300"
                        >
                            {sortOrder === 'asc' ? '↑' : '↓'}
                        </button>

                        <button
                            onClick={() => queryClient.invalidateQueries({ queryKey: ['documents'] })}
                            className="px-4 py-2 bg-gradient-to-r from-primary-600 to-accent-600 text-white rounded-lg hover:shadow-lg transition-all duration-300 flex items-center gap-2"
                        >
                            <FiRefreshCw className="w-4 h-4" />
                            刷新
                        </button>
                    </div>
                </div>

                {/* Batch Actions */}
                {selectedDocs.size > 0 && (
                    <div className="mt-4 pt-4 border-t border-gray-200 flex items-center justify-between">
                        <span className="text-sm text-gray-600">
                            已选择 <strong>{selectedDocs.size}</strong> 个文档
                        </span>
                        <button
                            onClick={handleBatchDelete}
                            disabled={deleteMutation.isPending}
                            className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-all duration-300 flex items-center gap-2 disabled:opacity-50"
                        >
                            {deleteMutation.isPending ? (
                                <Spinner size="sm" />
                            ) : (
                                <FiTrash2 className="w-4 h-4" />
                            )}
                            批量删除
                        </button>
                    </div>
                )}
            </div>

            {/* Documents List */}
            {isLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {[...Array(6)].map((_, i) => (
                        <CardSkeleton key={i} />
                    ))}
                </div>
            ) : filteredDocuments.length === 0 ? (
                <div className="text-center py-16 animate-fadeIn">
                    <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
                        <FiFileText className="w-10 h-10 text-gray-400" />
                    </div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">
                        暂无文档
                    </h3>
                    <p className="text-gray-600 mb-4">
                        {searchQuery ? '没有找到匹配的文档' : '开始上传您的第一个文档吧'}
                    </p>
                    <button
                        onClick={() => navigate('/upload')}
                        className="px-6 py-3 bg-gradient-to-r from-primary-600 to-accent-600 text-white rounded-xl hover:shadow-lg transition-all duration-300"
                    >
                        上传文档
                    </button>
                </div>
            ) : (
                <div className="space-y-4">
                    {/* Select All */}
                    <div className="flex items-center gap-2 px-2">
                        <button
                            onClick={toggleSelectAll}
                            className="p-2 hover:bg-gray-100 rounded transition-colors"
                        >
                            {selectedDocs.size === filteredDocuments.length ? (
                                <FiCheckSquare className="w-5 h-5 text-primary-600" />
                            ) : (
                                <FiSquare className="w-5 h-5 text-gray-400" />
                            )}
                        </button>
                        <span className="text-sm text-gray-600">全选</span>
                    </div>

                    {/* Document Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {filteredDocuments.map((doc: any, index: number) => (
                            <div
                                key={doc.id}
                                className="card-glass p-6 animate-fadeInUp hover:shadow-xl transition-all duration-300"
                                style={{ animationDelay: `${index * 50}ms` }}
                            >
                                <div className="flex items-start justify-between mb-4">
                                    <button
                                        onClick={() => toggleSelect(doc.id)}
                                        className="p-1 hover:bg-gray-100 rounded transition-colors"
                                    >
                                        {selectedDocs.has(doc.id) ? (
                                            <FiCheckSquare className="w-5 h-5 text-primary-600" />
                                        ) : (
                                            <FiSquare className="w-5 h-5 text-gray-400" />
                                        )}
                                    </button>
                                    <span
                                        className={clsx(
                                            'px-2 py-1 rounded-full text-xs font-medium',
                                            doc.processing_status === 'completed' && 'bg-green-100 text-green-700',
                                            doc.processing_status === 'processing' && 'bg-orange-100 text-orange-700',
                                            doc.processing_status === 'failed' && 'bg-red-100 text-red-700'
                                        )}
                                    >
                                        {doc.processing_status === 'completed' && '已完成'}
                                        {doc.processing_status === 'processing' && '处理中'}
                                        {doc.processing_status === 'failed' && '失败'}
                                    </span>
                                </div>

                                <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
                                    {doc.title || doc.original_filename}
                                </h3>

                                <div className="space-y-2 text-sm text-gray-600 mb-4">
                                    <p>📄 {doc.total_pages} 页</p>
                                    <p>📦 {(doc.file_size / 1024 / 1024).toFixed(2)} MB</p>
                                    <p>🕐 {new Date(doc.created_at).toLocaleDateString('zh-CN')}</p>
                                </div>

                                <button
                                    onClick={() => navigate(`/document/${doc.id}`)}
                                    className="w-full px-4 py-2 bg-gradient-to-r from-primary-600 to-accent-600 text-white rounded-lg hover:shadow-lg transition-all duration-300 flex items-center justify-center gap-2"
                                >
                                    <FiEye className="w-4 h-4" />
                                    查看文档
                                </button>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
