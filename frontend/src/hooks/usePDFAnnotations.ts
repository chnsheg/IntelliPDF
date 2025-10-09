/**
 * usePDFAnnotations Hook
 * 
 * 管理 PDF.js 标注的加载和保存
 */

import { useState, useCallback } from 'react';
import { apiService } from '../services/api';

export const usePDFAnnotations = (documentId: string) => {
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    /**
     * 加载标注数据并恢复到 PDF.js
     */
    const loadAnnotations = useCallback(async (pdfDocument: any) => {
        try {
            setIsLoading(true);
            setError(null);

            // 从后端获取标注数据
            const response = await apiService.getAnnotationsForDocument(documentId);
            const annotations = response.annotations || [];

            console.log('Loaded annotations:', annotations);

            if (!pdfDocument || !pdfDocument.annotationStorage) {
                console.warn('PDF document or annotationStorage not available');
                return;
            }

            // 恢复标注到 PDF.js AnnotationStorage
            const storage = pdfDocument.annotationStorage;
            
            // 清空现有标注
            storage.resetModified();

            // 将标注数据恢复到 storage
            annotations.forEach((ann: any) => {
                if (ann.data && typeof ann.data === 'object') {
                    // 如果是我们自定义格式，提取 pdfjs_data
                    const pdfjs_data = ann.data.pdfjs_data || ann.data;
                    
                    // 设置到 storage
                    if (pdfjs_data.id) {
                        storage.setValue(pdfjs_data.id, pdfjs_data);
                    }
                }
            });

            console.log('Annotations restored to PDF.js');
        } catch (err) {
            console.error('Failed to load annotations:', err);
            setError('加载标注失败');
        } finally {
            setIsLoading(false);
        }
    }, [documentId]);

    /**
     * 保存标注到后端
     */
    const saveAnnotations = useCallback(async (serializableData: any) => {
        try {
            setIsLoading(true);
            setError(null);

            console.log('Saving annotations:', serializableData);

            // 转换为数组格式
            const annotationsArray = Object.entries(serializableData).map(([id, data]) => ({
                id,
                document_id: documentId,
                user_id: localStorage.getItem('user_id') || 'anonymous',
                annotation_type: 'pdfjs',
                page_number: (data as any).pageIndex + 1 || 1,
                data: {
                    pdfjs_data: data,  // 直接存储 PDF.js 数据
                },
                tags: [],
            }));

            // 批量保存
            if (annotationsArray.length > 0) {
                await apiService.batchCreateAnnotations(annotationsArray);
                console.log('Annotations saved successfully');
            }
        } catch (err) {
            console.error('Failed to save annotations:', err);
            setError('保存标注失败');
        } finally {
            setIsLoading(false);
        }
    }, [documentId]);

    /**
     * 删除所有标注
     */
    const clearAnnotations = useCallback(async () => {
        try {
            setIsLoading(true);
            setError(null);

            // TODO: 调用删除 API
            await apiService.deleteAnnotationsByDocument(documentId);
            
            console.log('Annotations cleared');
        } catch (err) {
            console.error('Failed to clear annotations:', err);
            setError('删除标注失败');
        } finally {
            setIsLoading(false);
        }
    }, [documentId]);

    return {
        loadAnnotations,
        saveAnnotations,
        clearAnnotations,
        isLoading,
        error,
    };
};
