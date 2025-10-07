/**
 * Main App component with routing              <Route path="/upload" element={<UploadPage />} />
              <Route path="/documents" element={<DocumentsPage />} />
              <Route path="/knowledge-graph" element={<KnowledgeGraphPage />} />
            </Routes>nd lazy loading
 */

import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ToastProvider } from './components/Toast';
import { PageLoader } from './components/Loading';
import './index.css';

// Lazy load components for code splitting
const Layout = lazy(() => import('./components/Layout'));
const HomePage = lazy(() => import('./pages/HomePage'));
const DocumentViewerPage = lazy(() => import('./pages/DocumentViewerPage'));
const UploadPage = lazy(() => import('./pages/UploadPage'));
const DocumentsPage = lazy(() => import('./pages/DocumentsPage'));
const KnowledgeGraphPage = lazy(() => import('./pages/KnowledgeGraphPage'));

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <BrowserRouter>
          <Suspense fallback={<PageLoader message="加载中..." />}>
            <Routes>
              <Route path="/" element={<Layout />}>
                <Route index element={<HomePage />} />
                <Route path="upload" element={<UploadPage />} />
                <Route path="documents" element={<DocumentsPage />} />
                <Route path="knowledge-graph" element={<KnowledgeGraphPage />} />
                <Route path="document/:id" element={<DocumentViewerPage />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Route>
            </Routes>
          </Suspense>
        </BrowserRouter>
      </ToastProvider>
    </QueryClientProvider>
  );
}

export default App;
