/**
 * Responsive Sidebar/Drawer component
 */

import { Link, useLocation } from 'react-router-dom';
import { FiHome, FiUpload, FiFileText, FiSettings } from 'react-icons/fi';
import { useUIStore } from '../stores';
import { useIsMobile } from '../hooks/useResponsive';
import clsx from 'clsx';

const navigation = [
    { name: '首页', href: '/', icon: FiHome },
    { name: '上传文档', href: '/upload', icon: FiUpload },
    { name: '我的文档', href: '/documents', icon: FiFileText },
    { name: '设置', href: '/settings', icon: FiSettings },
];

export default function Sidebar() {
    const { sidebarOpen, setSidebarOpen } = useUIStore();
    const isMobile = useIsMobile();
    const location = useLocation();

    const handleLinkClick = () => {
        if (isMobile) {
            setSidebarOpen(false);
        }
    };

    return (
        <aside
            className={clsx(
                'bg-white border-r border-gray-200 transition-all duration-300',
                isMobile
                    ? // Mobile: Drawer style
                    clsx(
                        'fixed inset-y-0 left-0 z-40 w-64',
                        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
                    )
                    : // Desktop: Fixed sidebar
                    clsx('relative', sidebarOpen ? 'w-64' : 'w-0 overflow-hidden')
            )}
        >
            <div className="h-full flex flex-col py-4">
                {/* Navigation */}
                <nav className="flex-1 px-2 space-y-1">
                    {navigation.map((item) => {
                        const isActive = location.pathname === item.href;
                        return (
                            <Link
                                key={item.name}
                                to={item.href}
                                onClick={handleLinkClick}
                                className={clsx(
                                    'flex items-center gap-3 px-4 py-3 rounded-lg transition-colors',
                                    'hover:bg-gray-100',
                                    isActive
                                        ? 'bg-primary-50 text-primary-700 font-medium'
                                        : 'text-gray-700'
                                )}
                            >
                                <item.icon className="w-5 h-5" />
                                <span>{item.name}</span>
                            </Link>
                        );
                    })}
                </nav>

                {/* Footer */}
                <div className="px-4 py-2 text-xs text-gray-500 border-t border-gray-200">
                    <p>IntelliPDF v0.1.0</p>
                    <p className="mt-1">智能PDF知识管理</p>
                </div>
            </div>
        </aside>
    );
}
