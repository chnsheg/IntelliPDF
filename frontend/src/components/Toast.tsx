/**
 * Toast Notification System
 */

import { useState, useEffect, createContext, useContext } from 'react';
import type { ReactNode } from 'react';
import { FiCheckCircle, FiAlertCircle, FiInfo, FiX, FiAlertTriangle } from 'react-icons/fi';

type ToastType = 'success' | 'error' | 'warning' | 'info';

interface Toast {
    id: string;
    type: ToastType;
    message: string;
    duration?: number;
}

interface ToastContextType {
    showToast: (type: ToastType, message: string, duration?: number) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function useToast() {
    const context = useContext(ToastContext);
    if (!context) {
        throw new Error('useToast must be used within ToastProvider');
    }
    return context;
}

export function ToastProvider({ children }: { children: ReactNode }) {
    const [toasts, setToasts] = useState<Toast[]>([]);

    const showToast = (type: ToastType, message: string, duration = 3000) => {
        const id = `toast-${Date.now()}-${Math.random()}`;
        setToasts((prev) => [...prev, { id, type, message, duration }]);
    };

    const removeToast = (id: string) => {
        setToasts((prev) => prev.filter((toast) => toast.id !== id));
    };

    return (
        <ToastContext.Provider value={{ showToast }}>
            {children}
            <ToastContainer toasts={toasts} onRemove={removeToast} />
        </ToastContext.Provider>
    );
}

function ToastContainer({
    toasts,
    onRemove
}: {
    toasts: Toast[];
    onRemove: (id: string) => void;
}) {
    return (
        <div className="fixed top-4 right-4 z-50 space-y-2 max-w-sm w-full pointer-events-none">
            {toasts.map((toast) => (
                <ToastItem key={toast.id} toast={toast} onRemove={onRemove} />
            ))}
        </div>
    );
}

function ToastItem({ toast, onRemove }: { toast: Toast; onRemove: (id: string) => void }) {
    const [isExiting, setIsExiting] = useState(false);

    useEffect(() => {
        if (toast.duration) {
            const timer = setTimeout(() => {
                handleRemove();
            }, toast.duration);

            return () => clearTimeout(timer);
        }
    }, [toast.duration]);

    const handleRemove = () => {
        setIsExiting(true);
        setTimeout(() => {
            onRemove(toast.id);
        }, 300);
    };

    const icons = {
        success: <FiCheckCircle className="w-5 h-5 text-success-600" />,
        error: <FiAlertCircle className="w-5 h-5 text-error-600" />,
        warning: <FiAlertTriangle className="w-5 h-5 text-warning-600" />,
        info: <FiInfo className="w-5 h-5 text-primary-600" />,
    };

    const bgColors = {
        success: 'bg-success-50 border-success-200',
        error: 'bg-error-50 border-error-200',
        warning: 'bg-warning-50 border-warning-200',
        info: 'bg-primary-50 border-primary-200',
    };

    return (
        <div
            className={`
        ${isExiting ? 'animate-slide-out-right opacity-0' : 'animate-slide-in-right'}
        ${bgColors[toast.type]}
        pointer-events-auto
        flex items-start gap-3 p-4 rounded-lg border shadow-lg
        backdrop-blur-sm transition-all duration-300
      `}
        >
            <div className="flex-shrink-0 mt-0.5">{icons[toast.type]}</div>
            <p className="flex-1 text-sm font-medium text-gray-900">{toast.message}</p>
            <button
                onClick={handleRemove}
                className="flex-shrink-0 text-gray-400 hover:text-gray-600 transition-colors"
            >
                <FiX className="w-4 h-4" />
            </button>
        </div>
    );
}

// Helper functions - use with useToast() hook in components
