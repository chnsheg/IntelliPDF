/**
 * Header component with responsive navigation
 */

import { Link } from 'react-router-dom';
import { FiMenu, FiUpload } from 'react-icons/fi';
import { useUIStore } from '../stores';
import { useIsMobile } from '../hooks/useResponsive';

export default function Header() {
    const { toggleSidebar } = useUIStore();
    const isMobile = useIsMobile();

    return (
        <header className="bg-white border-b border-gray-200 h-16 flex items-center px-4 z-20">
            <div className="flex items-center justify-between w-full">
                {/* Left: Logo + Menu */}
                <div className="flex items-center gap-3">
                    <button
                        onClick={toggleSidebar}
                        className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                        aria-label="Toggle menu"
                    >
                        <FiMenu className="w-6 h-6 text-gray-700" />
                    </button>

                    <Link to="/" className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                            <span className="text-white font-bold text-lg">I</span>
                        </div>
                        {!isMobile && (
                            <h1 className="text-xl font-bold text-gray-900">IntelliPDF</h1>
                        )}
                    </Link>
                </div>

                {/* Right: Actions */}
                <div className="flex items-center gap-2">
                    <Link
                        to="/upload"
                        className="btn btn-primary flex items-center gap-2"
                    >
                        <FiUpload className="w-4 h-4" />
                        {!isMobile && <span>上传文档</span>}
                    </Link>
                </div>
            </div>
        </header>
    );
}
