/**
 * Main Layout component with responsive sidebar
 */

import { Outlet } from 'react-router-dom';
import { useEffect } from 'react';
import Header from './Header';
import Sidebar from './Sidebar';
import { useUIStore } from '../stores';
import { useIsMobile } from '../hooks/useResponsive';

export default function Layout() {
    const { sidebarOpen, setSidebarOpen } = useUIStore();
    const isMobile = useIsMobile();

    // Close sidebar on mobile by default
    useEffect(() => {
        if (isMobile) {
            setSidebarOpen(false);
        }
    }, [isMobile, setSidebarOpen]);

    return (
        <div className="h-screen flex flex-col overflow-hidden">
            {/* Header */}
            <Header />

            <div className="flex-1 flex overflow-hidden">
                {/* Sidebar */}
                <Sidebar />

                {/* Mobile overlay */}
                {isMobile && sidebarOpen && (
                    <div
                        className="fixed inset-0 bg-black bg-opacity-50 z-30"
                        onClick={() => setSidebarOpen(false)}
                    />
                )}

                {/* Main content */}
                <main className="flex-1 overflow-auto bg-gray-50">
                    <Outlet />
                </main>
            </div>
        </div>
    );
}
