/**
 * Home Page - Document list
 */

import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { FiFileText, FiClock, FiCheckCircle } from 'react-icons/fi';
import { apiService } from '../services/api';
import { useIsMobile } from '../hooks/useResponsive';
import type { Document } from '../types';

export default function HomePage() {
    const isMobile = useIsMobile();

    const { data, isLoading, error } = useQuery({
        queryKey: ['documents'],
        queryFn: () => apiService.getDocuments(1, 20),
    });

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="animate-spin w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-center">
                    <p className="text-red-600 mb-2">加载失败</p>
                    <p className="text-gray-600 text-sm">{(error as Error).message}</p>
                </div>
            </div>
        );
    }

    const documents = data?.items || [];

    return (
        <div className="max-w-7xl mx-auto px-4 py-6">
            {/* Header */}
            <div className="mb-6">
                <h1 className="text-2xl md:text-3xl font-bold text-gray-900">
                    我的文档
                </h1>
                <p className="text-gray-600 mt-1">
                    共 {data?.total || 0} 个文档
                </p>
            </div>

            {/* Document grid */}
            {documents.length === 0 ? (
                <div className="text-center py-12">
                    <FiFileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-600 mb-4">还没有上传任何文档</p>
                    <Link to="/upload" className="btn btn-primary">
                        上传第一个文档
                    </Link>
                </div>
            ) : (
                <div
                    className={
                        isMobile
                            ? 'space-y-4'
                            : 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'
                    }
                >
                    {documents.map((doc: Document) => (
                        <DocumentCard key={doc.id} document={doc} />
                    ))}
                </div>
            )}
        </div>
    );
}

function DocumentCard({ document }: { document: Document }) {
    const statusConfig = {
        completed: { icon: FiCheckCircle, color: 'text-green-600', label: '已完成' },
        processing: { icon: FiClock, color: 'text-yellow-600', label: '处理中' },
        failed: { icon: FiClock, color: 'text-red-600', label: '失败' },
        pending: { icon: FiClock, color: 'text-gray-600', label: '等待中' },
    };

    const status = statusConfig[document.status];
    const StatusIcon = status.icon;

    return (
        <Link
            to={`/document/${document.id}`}
            className="card hover:shadow-md transition-shadow cursor-pointer"
        >
            <div className="flex items-start gap-3">
                <div className="flex-shrink-0">
                    <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
                        <FiFileText className="w-6 h-6 text-primary-600" />
                    </div>
                </div>

                <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-gray-900 truncate">
                        {document.filename}
                    </h3>
                    <div className="flex items-center gap-2 mt-1 text-sm text-gray-600">
                        <StatusIcon className={`w-4 h-4 ${status.color}`} />
                        <span>{status.label}</span>
                        <span>•</span>
                        <span>{document.chunk_count} 块</span>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                        {new Date(document.created_at).toLocaleDateString('zh-CN')}
                    </p>
                </div>
            </div>
        </Link>
    );
}
