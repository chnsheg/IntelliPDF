/**
 * Loading Components - Modern loading animations
 */

import { FiLoader } from 'react-icons/fi';

// Spinner Loader
export function Spinner({ size = 'md', className = '' }: { size?: 'sm' | 'md' | 'lg'; className?: string }) {
    const sizeClasses = {
        sm: 'w-4 h-4',
        md: 'w-6 h-6',
        lg: 'w-8 h-8',
    };

    return (
        <FiLoader className={`${sizeClasses[size]} animate-spin text-primary-600 ${className}`} />
    );
}

// Dots Loader
export function DotsLoader({ className = '' }: { className?: string }) {
    return (
        <div className={`flex items-center gap-1 ${className}`}>
            <div className="w-2 h-2 bg-primary-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
            <div className="w-2 h-2 bg-primary-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
            <div className="w-2 h-2 bg-primary-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
    );
}

// Pulse Loader
export function PulseLoader({ className = '' }: { className?: string }) {
    return (
        <div className={`flex items-center justify-center ${className}`}>
            <div className="relative w-12 h-12">
                <div className="absolute inset-0 bg-primary-500 rounded-full animate-ping opacity-75" />
                <div className="absolute inset-2 bg-primary-600 rounded-full" />
            </div>
        </div>
    );
}

// Skeleton Loader
export function Skeleton({ className = '', variant = 'text' }: { className?: string; variant?: 'text' | 'circular' | 'rectangular' }) {
    const baseClass = 'bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 bg-[length:200%_100%] animate-skeleton';

    const variantClasses = {
        text: 'h-4 w-full rounded',
        circular: 'rounded-full',
        rectangular: 'rounded-lg',
    };

    return <div className={`${baseClass} ${variantClasses[variant]} ${className}`} />;
}

// Progress Bar
export function ProgressBar({
    progress,
    className = '',
    showPercentage = false,
    variant = 'primary'
}: {
    progress: number;
    className?: string;
    showPercentage?: boolean;
    variant?: 'primary' | 'success' | 'warning' | 'error';
}) {
    const variantColors = {
        primary: 'bg-primary-600',
        success: 'bg-success-500',
        warning: 'bg-warning-500',
        error: 'bg-error-500',
    };

    return (
        <div className={`relative ${className}`}>
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                    className={`h-full ${variantColors[variant]} transition-all duration-500 ease-out rounded-full`}
                    style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
                >
                    <div className="h-full w-full bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer" />
                </div>
            </div>
            {showPercentage && (
                <span className="absolute right-0 -top-6 text-xs font-medium text-gray-600">
                    {Math.round(progress)}%
                </span>
            )}
        </div>
    );
}

// Full Page Loading
export function PageLoader({ message = 'Loading...' }: { message?: string }) {
    return (
        <div className="fixed inset-0 bg-white/80 backdrop-blur-sm z-50 flex items-center justify-center animate-fade-in">
            <div className="text-center space-y-4">
                <div className="relative w-16 h-16 mx-auto">
                    <div className="absolute inset-0 border-4 border-primary-200 rounded-full animate-ping" />
                    <div className="absolute inset-0 border-4 border-primary-600 rounded-full border-t-transparent animate-spin" />
                </div>
                <p className="text-sm font-medium text-gray-700">{message}</p>
            </div>
        </div>
    );
}

// Card Skeleton
export function CardSkeleton({ count = 1 }: { count?: number }) {
    return (
        <>
            {Array.from({ length: count }).map((_, i) => (
                <div key={i} className="card space-y-4 animate-pulse">
                    <Skeleton variant="rectangular" className="h-48 w-full" />
                    <div className="space-y-2">
                        <Skeleton className="w-3/4" />
                        <Skeleton className="w-1/2" />
                    </div>
                </div>
            ))}
        </>
    );
}

// Ripple Effect (for button clicks)
export function Ripple({ x, y }: { x: number; y: number }) {
    return (
        <span
            className="absolute bg-white/50 rounded-full animate-ping"
            style={{
                left: x,
                top: y,
                width: 20,
                height: 20,
                transform: 'translate(-50%, -50%)',
            }}
        />
    );
}
