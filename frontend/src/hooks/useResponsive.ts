/**
 * Custom hooks for responsive design and device detection
 */

import { useState, useEffect } from 'react';
import type { ViewportSize, DeviceType } from '../types';

// Breakpoints (matching Tailwind config)
const BREAKPOINTS = {
    mobile: 768,
    tablet: 1024,
} as const;

/**
 * Hook to detect viewport size and device type
 */
export function useViewport(): ViewportSize {
    const [viewport, setViewport] = useState<ViewportSize>(() => {
        const width = window.innerWidth;
        const height = window.innerHeight;
        return {
            width,
            height,
            isMobile: width < BREAKPOINTS.mobile,
            isTablet: width >= BREAKPOINTS.mobile && width < BREAKPOINTS.tablet,
            isDesktop: width >= BREAKPOINTS.tablet,
        };
    });

    useEffect(() => {
        const handleResize = () => {
            const width = window.innerWidth;
            const height = window.innerHeight;
            setViewport({
                width,
                height,
                isMobile: width < BREAKPOINTS.mobile,
                isTablet: width >= BREAKPOINTS.mobile && width < BREAKPOINTS.tablet,
                isDesktop: width >= BREAKPOINTS.tablet,
            });
        };

        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    return viewport;
}

/**
 * Hook to detect if user is on mobile device
 */
export function useIsMobile(): boolean {
    const { isMobile } = useViewport();
    return isMobile;
}

/**
 * Hook to detect device type
 */
export function useDeviceType(): DeviceType {
    const { isMobile, isTablet } = useViewport();
    if (isMobile) return 'mobile';
    if (isTablet) return 'tablet';
    return 'desktop';
}

/**
 * Hook to detect touch device
 */
export function useIsTouchDevice(): boolean {
    const [isTouch, setIsTouch] = useState(false);

    useEffect(() => {
        const hasTouchScreen =
            'ontouchstart' in window ||
            navigator.maxTouchPoints > 0 ||
            (navigator as any).msMaxTouchPoints > 0;
        setIsTouch(hasTouchScreen);
    }, []);

    return isTouch;
}

/**
 * Hook for media query matching
 */
export function useMediaQuery(query: string): boolean {
    const [matches, setMatches] = useState(() => {
        if (typeof window !== 'undefined') {
            return window.matchMedia(query).matches;
        }
        return false;
    });

    useEffect(() => {
        const mediaQuery = window.matchMedia(query);
        const handler = (event: MediaQueryListEvent) => setMatches(event.matches);

        mediaQuery.addEventListener('change', handler);
        return () => mediaQuery.removeEventListener('change', handler);
    }, [query]);

    return matches;
}

/**
 * Hook to detect orientation
 */
export function useOrientation(): 'portrait' | 'landscape' {
    const [orientation, setOrientation] = useState<'portrait' | 'landscape'>(
        () => (window.innerHeight > window.innerWidth ? 'portrait' : 'landscape')
    );

    useEffect(() => {
        const handleOrientationChange = () => {
            setOrientation(
                window.innerHeight > window.innerWidth ? 'portrait' : 'landscape'
            );
        };

        window.addEventListener('resize', handleOrientationChange);
        return () => window.removeEventListener('resize', handleOrientationChange);
    }, []);

    return orientation;
}

/**
 * Hook to detect safe area insets (for iOS notch, etc.)
 */
export function useSafeArea() {
    const [safeArea, setSafeArea] = useState({
        top: 0,
        right: 0,
        bottom: 0,
        left: 0,
    });

    useEffect(() => {
        const updateSafeArea = () => {
            const style = getComputedStyle(document.documentElement);
            setSafeArea({
                top: parseInt(style.getPropertyValue('--safe-area-inset-top') || '0'),
                right: parseInt(style.getPropertyValue('--safe-area-inset-right') || '0'),
                bottom: parseInt(style.getPropertyValue('--safe-area-inset-bottom') || '0'),
                left: parseInt(style.getPropertyValue('--safe-area-inset-left') || '0'),
            });
        };

        updateSafeArea();
        window.addEventListener('resize', updateSafeArea);
        return () => window.removeEventListener('resize', updateSafeArea);
    }, []);

    return safeArea;
}
