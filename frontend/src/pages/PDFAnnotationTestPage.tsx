/**
 * PDF.js 原生标注系统测试页面
 * 用于测试 PDFViewerNative 组件
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { PDFViewerNative } from '../components/PDFViewerNative';
import apiService from '../services/api';

export default function PDFAnnotationTestPage() {
    const navigate = useNavigate();
    const [documents, setDocuments] = useState<any[]>([]);
    const [selectedDoc, setSelectedDoc] = useState<any | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    // 加载文档列表
    useEffect(() => {
        const loadDocuments = async () => {
            try {
                const response = await apiService.getDocuments();
                const docs = response.items || [];
                setDocuments(docs);
                if (docs.length > 0) {
                    setSelectedDoc(docs[0]);
                }
            } catch (error) {
                console.error('Failed to load documents:', error);
            } finally {
                setIsLoading(false);
            }
        };

        loadDocuments();
    }, []);

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                    <p className="text-gray-600">加载文档列表...</p>
                </div>
            </div>
        );
    }

    if (documents.length === 0) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                    <p className="text-xl text-gray-600 mb-4">暂无文档</p>
                    <button
                        onClick={() => navigate('/upload')}
                        className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                    >
                        上传 PDF
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="flex flex-col h-screen bg-gray-50">
            {/* 顶部栏 */}
            <div className="bg-white border-b shadow-sm p-4 flex items-center gap-4">
                <button
                    onClick={() => navigate(-1)}
                    className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                >
                    ← 返回
                </button>

                <div className="flex-1">
                    <h1 className="text-xl font-bold text-gray-900">PDF.js 原生标注测试</h1>
                    <p className="text-sm text-gray-500">测试画笔、文本框等标注功能</p>
                </div>

                {/* 文档选择器 */}
                <select
                    value={selectedDoc?.id || ''}
                    onChange={(e) => {
                        const doc = documents.find(d => d.id === e.target.value);
                        setSelectedDoc(doc);
                    }}
                    className="px-4 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                    {documents.map(doc => (
                        <option key={doc.id} value={doc.id}>
                            {doc.title}
                        </option>
                    ))}
                </select>
            </div>

            {/* PDF 查看器 */}
            {selectedDoc && (
                <div className="flex-1 overflow-hidden">
                    <PDFViewerNative
                        key={selectedDoc.id}
                        documentId={selectedDoc.id}
                        pdfUrl={`http://localhost:8000${selectedDoc.file_path}`}
                    />
                </div>
            )}
        </div>
    );
}
