/**
 * TypeScript type definitions for IntelliPDF
 */

// Document types
export interface Document {
    id: string;
    filename: string;
    file_path: string;
    file_size: number;
    content_hash: string;
    status: DocumentStatus;
    processing_started_at?: string;
    processing_completed_at?: string;
    processing_error?: string;
    metadata?: DocumentMetadata;
    chunk_count: number;
    created_at: string;
    updated_at: string;
}

export type DocumentStatus = 'pending' | 'processing' | 'completed' | 'failed';

export const DocumentStatus = {
    PENDING: 'pending' as const,
    PROCESSING: 'processing' as const,
    COMPLETED: 'completed' as const,
    FAILED: 'failed' as const,
};

export interface DocumentMetadata {
    title?: string;
    author?: string;
    subject?: string;
    keywords?: string;
    creator?: string;
    producer?: string;
    creation_date?: string;
    modification_date?: string;
    page_count?: number;
    language?: string;
}

// Chunk types - 匹配后端实际返回格式
export interface Chunk {
    id: string;  // 后端返回 id 而不是 chunk_id
    document_id: string;
    content: string;
    chunk_index: number;
    chunk_type: ChunkType;
    start_page: number;
    end_page: number;
    token_count: number;
    vector_id?: string;
    bounding_boxes?: BoundingBox[];  // 分块边界框信息
    chunk_metadata?: Record<string, any>;  // 后端字段名
    created_at: string;
    updated_at: string;
}

export type ChunkType = 'text' | 'code' | 'image' | 'table' | 'formula';

export const ChunkType = {
    TEXT: 'text' as const,
    CODE: 'code' as const,
    IMAGE: 'image' as const,
    TABLE: 'table' as const,
    FORMULA: 'formula' as const,
};

export interface BoundingBox {
    page: number;
    x0: number;
    y0: number;
    x1: number;
    y1: number;
}

export interface ChunkListResponse {
    document_id: string;
    total: number;
    chunks: Chunk[];
}

// Chat types
export interface ChatMessage {
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp?: string;
    sources?: ChunkSource[];
}

export interface ChunkSource {
    chunk_id: string;
    content: string;
    page_number?: number;
    similarity_score: number;
}

export interface ChatRequest {
    question: string;
    stream?: boolean;
}

export interface ChatResponse {
    answer: string;
    sources: ChunkSource[];
    processing_time?: number;
}

// API Response types
export interface ApiResponse<T> {
    success: boolean;
    data?: T;
    error?: string;
    metadata?: Record<string, any>;
}

export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
}

export interface DocumentStatistics {
    total: number;  // 后端返回的字段名
    by_status: Record<string, number>;  // 后端返回的格式
    total_size: number;
}

// Upload types
export interface UploadProgress {
    loaded: number;
    total: number;
    percentage: number;
}

// Device detection
export type DeviceType = 'mobile' | 'tablet' | 'desktop';

export interface ViewportSize {
    width: number;
    height: number;
    isMobile: boolean;
    isTablet: boolean;
    isDesktop: boolean;
}
