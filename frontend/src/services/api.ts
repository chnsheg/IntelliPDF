/**
 * API service for backend communication
 */

import axios from 'axios';
import type { AxiosInstance, AxiosProgressEvent } from 'axios';
import type {
    Document,
    DocumentStatistics,
    Chunk,
    ChatRequest,
    ChatResponse,
    ApiResponse,
    PaginatedResponse,
    UploadProgress,
} from '../types';

class ApiService {
    private client: AxiosInstance;

    constructor() {
        this.client = axios.create({
            baseURL: import.meta.env.VITE_API_URL || '/api/v1',
            timeout: 60000,
            headers: {
                'Content-Type': 'application/json',
            },
        });

        // Request interceptor
        this.client.interceptors.request.use(
            (config) => {
                // Add auth token if available
                const token = localStorage.getItem('auth_token');
                if (token) {
                    config.headers.Authorization = `Bearer ${token}`;
                }
                return config;
            },
            (error) => Promise.reject(error)
        );

        // Response interceptor
        this.client.interceptors.response.use(
            (response) => response,
            (error) => {
                if (error.response?.status === 401) {
                    // Handle unauthorized
                    localStorage.removeItem('auth_token');
                    window.location.href = '/login';
                }
                return Promise.reject(error);
            }
        );
    }

    // Health check - 注意：health endpoint 在根路径，不在 /api/v1 下
    async healthCheck(): Promise<{ status: string; version: string; environment: string }> {
        // Health endpoint 在根路径
        const response = await axios.get('/health', {
            baseURL: import.meta.env.VITE_API_URL?.replace('/api/v1', '') || 'http://localhost:8000',
            timeout: 5000
        });
        return response.data;
    }

    // Document endpoints
    async uploadDocument(
        file: File,
        onProgress?: (progress: UploadProgress) => void
    ): Promise<Document> {
        const formData = new FormData();
        formData.append('file', file);

        const response = await this.client.post('/documents/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
            onUploadProgress: (progressEvent: AxiosProgressEvent) => {
                if (onProgress && progressEvent.total) {
                    const percentage = Math.round(
                        (progressEvent.loaded * 100) / progressEvent.total
                    );
                    onProgress({
                        loaded: progressEvent.loaded,
                        total: progressEvent.total,
                        percentage,
                    });
                }
            },
        });

        // 后端直接返回 Document 对象
        return response.data;
    }

    async getDocuments(
        page: number = 1,
        pageSize: number = 20
    ): Promise<PaginatedResponse<Document>> {
        const skip = (page - 1) * pageSize;
        const response = await this.client.get('/documents', {
            params: { skip, limit: pageSize },
        });
        // 转换后端响应格式为前端期望的格式
        const backendData = response.data;
        return {
            items: backendData.documents || [],
            total: backendData.total || 0,
            page,
            page_size: pageSize,
            total_pages: Math.ceil((backendData.total || 0) / pageSize),
        };
    }

    async getDocument(id: string): Promise<Document> {
        const response = await this.client.get(`/documents/${id}`);
        // 后端直接返回文档对象，不包装在 data 字段中
        return response.data;
    }

    async deleteDocument(id: string): Promise<{ success: boolean; message: string }> {
        const response = await this.client.delete(`/documents/${id}`);
        return response.data;
    }

    async getDocumentStatistics(): Promise<DocumentStatistics> {
        const response = await this.client.get('/documents/statistics');
        // 后端返回: { total: number, by_status: {}, total_size: number }
        return response.data;
    }

    async getDocumentChunks(
        documentId: string,
        page: number = 1,
        pageSize: number = 1000
    ): Promise<{ document_id: string; total: number; chunks: Chunk[] }> {
        const skip = (page - 1) * pageSize;
        const response = await this.client.get(`/documents/${documentId}/chunks`, {
            params: { skip, limit: pageSize },
        });
        // 后端返回: { document_id, total, chunks }
        return response.data;
    }

    // Chat endpoints
    async chat(
        documentId: string,
        request: ChatRequest
    ): Promise<ChatResponse> {
        const response = await this.client.post(
            `/documents/${documentId}/chat`,
            request
        );
        // 后端直接返回 ChatResponse 对象
        return response.data;
    }

    // Get current context based on reading position
    async getCurrentContext(
        documentId: string,
        page: number,
        x?: number,
        y?: number
    ): Promise<{
        document_id: string;
        current_page: number;
        current_position: { x: number; y: number } | null;
        relevant_chunks: Array<{
            chunk_id: string;
            chunk_index: number;
            content: string;
            chunk_type: string;
            start_page: number;
            end_page: number;
            relevance: number;
        }>;
        total_found: number;
    }> {
        const response = await this.client.post(
            `/documents/${documentId}/current-context`,
            null,
            {
                params: { page, x, y },
            }
        );
        return response.data;
    }

    // Utility methods
    getDocumentUrl(documentId: string): string {
        return `${this.client.defaults.baseURL}/documents/${documentId}/file`;
    }

    getThumbnailUrl(documentId: string, page: number = 1): string {
        return `${this.client.defaults.baseURL}/documents/${documentId}/thumbnail?page=${page}`;
    }

    // Enhanced document endpoints (注意：这些 API 后端目前返回 500，暂时回退到基础API)
    async searchDocuments(params: {
        query?: string;
        status?: string;
        sort_by?: string;
        sort_order?: string;
        limit?: number;
        offset?: number;
    }): Promise<Document[]> {
        // 暂时使用基础的 getDocuments API
        const result = await this.getDocuments(1, params.limit || 50);
        let docs = result.items;

        // 前端实现基础过滤
        if (params.status && params.status !== 'all') {
            docs = docs.filter(d => d.status === params.status);
        }
        if (params.query) {
            const query = params.query.toLowerCase();
            docs = docs.filter(d => d.filename.toLowerCase().includes(query));
        }

        return docs;
    }

    async batchDeleteDocuments(data: {
        document_ids: string[];
    }): Promise<ApiResponse<any>> {
        const response = await this.client.post('/documents-enhanced/batch/delete', data);
        return response.data;
    }

    async getDetailedStatistics(): Promise<ApiResponse<any>> {
        const response = await this.client.get('/documents-enhanced/statistics/detailed');
        return response.data;
    }

    async exportDocumentsMetadata(format: string = 'json'): Promise<ApiResponse<any>> {
        const response = await this.client.get('/documents-enhanced/export/metadata', {
            params: { format },
        });
        return response.data;
    }

    // Knowledge Graph APIs
    async getGraphData(limit: number = 50) {
        const { data } = await this.client.get(`/knowledge-graph/graph-data?limit=${limit}`);
        return data;
    }

    async getDocumentEntities(documentId: string) {
        const { data } = await this.client.get(`/knowledge-graph/entities?document_id=${documentId}`);
        return data;
    }

    async getEntityRelationships(entityId: string) {
        const { data } = await this.client.get(`/knowledge-graph/relationships?entity_id=${entityId}`);
        return data;
    }

    async analyzeDocumentGraph(documentId: string) {
        const { data } = await this.client.post(`/knowledge-graph/analyze?document_id=${documentId}`);
        return data;
    }

    // ==================== Authentication APIs ====================

    /**
     * Register a new user
     */
    async register(userData: {
        username: string;
        email: string;
        password: string;
        full_name?: string;
    }): Promise<{ access_token: string; token_type: string; user: any }> {
        const { data } = await this.client.post('/auth/register', userData);

        // Store token in localStorage
        if (data.access_token) {
            localStorage.setItem('auth_token', data.access_token);
        }

        return data;
    }

    /**
     * Login with username and password
     */
    async login(credentials: {
        username: string;
        password: string;
    }): Promise<{ access_token: string; token_type: string; user: any }> {
        const { data } = await this.client.post('/auth/login', credentials);

        // Store token in localStorage
        if (data.access_token) {
            localStorage.setItem('auth_token', data.access_token);
        }

        return data;
    }

    /**
     * Logout current user
     */
    async logout(): Promise<void> {
        try {
            await this.client.post('/auth/logout');
        } finally {
            // Always remove token from localStorage
            localStorage.removeItem('auth_token');
        }
    }

    /**
     * Get current user information
     */
    async getCurrentUser(): Promise<any> {
        const { data } = await this.client.get('/auth/me');
        return data;
    }

    /**
     * Change password
     */
    async changePassword(passwordData: {
        old_password: string;
        new_password: string;
    }): Promise<{ message: string; success: boolean }> {
        const { data } = await this.client.post('/auth/change-password', passwordData);
        return data;
    }

    // ==================== Bookmark APIs ====================

    async createBookmark(payload: any) {
        const { data } = await this.client.post('/bookmarks', payload);
        return data as any;
    }

    async generateBookmark(payload: any) {
        const { data } = await this.client.post('/bookmarks/generate', payload);
        return data as any;
    }

    async getBookmarks(params: { document_id?: string; page_number?: number; limit?: number } = {}) {
        const { data } = await this.client.get('/bookmarks', { params });
        return data as any;
    }

    async getBookmark(id: string) {
        const { data } = await this.client.get(`/bookmarks/${id}`);
        return data as any;
    }

    async updateBookmark(id: string, update: any) {
        const { data } = await this.client.put(`/bookmarks/${id}`, update);
        return data as any;
    }

    async deleteBookmark(id: string) {
        const { data } = await this.client.delete(`/bookmarks/${id}`);
        return data as any;
    }

    async searchBookmarks(payload: { query: string; document_id?: string }) {
        const { data } = await this.client.post('/bookmarks/search', payload);
        return data as any;
    }

    // ==================== Annotation APIs ====================

    async createAnnotation(payload: any) {
        const { data } = await this.client.post('/annotations', payload);
        return data as any;
    }

    async getAnnotationsForDocument(documentId: string) {
        const { data } = await this.client.get(`/annotations/documents/${documentId}`);
        return data as any;
    }

    async updateAnnotation(annotationId: string, payload: any) {
        const { data } = await this.client.patch(`/annotations/${annotationId}`, payload);
        return data as any;
    }

    async deleteAnnotation(annotationId: string) {
        const { data } = await this.client.delete(`/annotations/${annotationId}`);
        return data as any;
    }
}

export const apiService = new ApiService();
export default apiService;
