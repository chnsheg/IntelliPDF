/**
 * Global state management using Zustand
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Document, ChatMessage } from '../types';

// UI State Store
interface UIState {
    sidebarOpen: boolean;
    theme: 'light' | 'dark';
    toggleSidebar: () => void;
    setSidebarOpen: (open: boolean) => void;
    setTheme: (theme: 'light' | 'dark') => void;
}

export const useUIStore = create<UIState>()(
    persist(
        (set) => ({
            sidebarOpen: true,
            theme: 'light',
            toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
            setSidebarOpen: (open) => set({ sidebarOpen: open }),
            setTheme: (theme) => set({ theme }),
        }),
        {
            name: 'ui-storage',
        }
    )
);

// Document Store
interface DocumentState {
    currentDocument: Document | null;
    documents: Document[];
    setCurrentDocument: (doc: Document | null) => void;
    setDocuments: (docs: Document[]) => void;
    addDocument: (doc: Document) => void;
    removeDocument: (id: string) => void;
}

export const useDocumentStore = create<DocumentState>((set) => ({
    currentDocument: null,
    documents: [],
    setCurrentDocument: (doc) => set({ currentDocument: doc }),
    setDocuments: (docs) => set({ documents: docs }),
    addDocument: (doc) =>
        set((state) => ({ documents: [...state.documents, doc] })),
    removeDocument: (id) =>
        set((state) => ({
            documents: state.documents.filter((d) => d.id !== id),
            currentDocument:
                state.currentDocument?.id === id ? null : state.currentDocument,
        })),
}));

// Chat Store
interface ChatState {
    messages: ChatMessage[];
    isLoading: boolean;
    addMessage: (message: ChatMessage) => void;
    setMessages: (messages: ChatMessage[]) => void;
    clearMessages: () => void;
    setLoading: (loading: boolean) => void;
}

export const useChatStore = create<ChatState>((set) => ({
    messages: [],
    isLoading: false,
    addMessage: (message) =>
        set((state) => ({ messages: [...state.messages, message] })),
    setMessages: (messages) => set({ messages }),
    clearMessages: () => set({ messages: [] }),
    setLoading: (loading) => set({ isLoading: loading }),
}));

// Upload Store
interface UploadState {
    uploadProgress: number;
    isUploading: boolean;
    uploadError: string | null;
    setUploadProgress: (progress: number) => void;
    setUploading: (uploading: boolean) => void;
    setUploadError: (error: string | null) => void;
    resetUpload: () => void;
}

export const useUploadStore = create<UploadState>((set) => ({
    uploadProgress: 0,
    isUploading: false,
    uploadError: null,
    setUploadProgress: (progress) => set({ uploadProgress: progress }),
    setUploading: (uploading) => set({ isUploading: uploading }),
    setUploadError: (error) => set({ uploadError: error }),
    resetUpload: () =>
        set({ uploadProgress: 0, isUploading: false, uploadError: null }),
}));
