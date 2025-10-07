/**
 * Modern Sidebar with Animations and Gradients
 */

import { Link, useLocation } from 'react-router-dom';
import { 
  FiHome, FiUpload, FiFileText, FiSettings, FiX, 
  FiTrendingUp, FiBookOpen, FiLayers
} from 'react-icons/fi';
import { useUIStore } from '../stores';
import { useIsMobile } from '../hooks/useResponsive';
import clsx from 'clsx';

const navigation = [
  { 
    name: '首页', 
    href: '/', 
    icon: FiHome,
    description: '查看统计和最近文档',
    gradient: 'from-blue-500 to-cyan-500'
  },
  { 
    name: '上传文档', 
    href: '/upload', 
    icon: FiUpload,
    description: '上传新的 PDF 文档',
    gradient: 'from-purple-500 to-pink-500'
  },
  { 
    name: '我的文档', 
    href: '/documents', 
    icon: FiFileText,
    description: '浏览所有文档',
    gradient: 'from-green-500 to-emerald-500'
  },
  { 
    name: '知识图谱', 
    href: '/knowledge-graph', 
    icon: FiLayers,
    description: '可视化知识结构',
    gradient: 'from-orange-500 to-yellow-500'
  },
];

const secondaryNav = [
  { name: '统计分析', href: '/analytics', icon: FiTrendingUp },
  { name: '学习中心', href: '/learn', icon: FiBookOpen },
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
    <>
      {/* Overlay for mobile */}
      {isMobile && sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-30 animate-fade-in"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={clsx(
          'bg-white border-r border-gray-200/50 transition-all duration-300 flex flex-col',
          isMobile
            ? // Mobile: Drawer style
              clsx(
                'fixed inset-y-0 left-0 z-40 w-72 shadow-2xl',
                sidebarOpen ? 'translate-x-0' : '-translate-x-full'
              )
            : // Desktop: Fixed sidebar
              clsx(
                'relative',
                sidebarOpen ? 'w-72' : 'w-0 overflow-hidden'
              )
        )}
      >
        {/* Header */}
        {isMobile && (
          <div className="flex items-center justify-between p-4 border-b border-gray-200">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-primary-600 to-accent-600 rounded-lg flex items-center justify-center shadow-lg">
                <span className="text-white font-bold">I</span>
              </div>
              <span className="font-bold text-gray-900">导航菜单</span>
            </div>
            <button
              onClick={() => setSidebarOpen(false)}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <FiX className="w-5 h-5 text-gray-600" />
            </button>
          </div>
        )}

        {/* Main Navigation */}
        <nav className="flex-1 px-3 py-6 space-y-2 overflow-y-auto scrollbar-thin">
          <div className="mb-6">
            <h3 className="px-3 mb-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">
              主要功能
            </h3>
            <div className="space-y-1">
              {navigation.map((item, index) => {
                const isActive = location.pathname === item.href;
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    onClick={handleLinkClick}
                    className={clsx(
                      'group relative flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-300',
                      'hover:scale-[1.02] active:scale-[0.98]',
                      isActive
                        ? 'bg-gradient-to-r shadow-soft' + ` ${item.gradient}`
                        : 'hover:bg-gray-50'
                    )}
                    style={{
                      animationDelay: `${index * 50}ms`
                    }}
                  >
                    {/* Icon */}
                    <div className={clsx(
                      'relative flex items-center justify-center w-10 h-10 rounded-lg transition-all duration-300',
                      isActive
                        ? 'bg-white/20 shadow-soft'
                        : 'bg-gray-100 group-hover:bg-white'
                    )}>
                      <item.icon className={clsx(
                        'w-5 h-5 transition-all duration-300',
                        isActive 
                          ? 'text-white' 
                          : 'text-gray-600 group-hover:text-primary-600 group-hover:scale-110'
                      )} />
                    </div>

                    {/* Text */}
                    <div className="flex-1 min-w-0">
                      <p className={clsx(
                        'text-sm font-medium transition-colors',
                        isActive ? 'text-white' : 'text-gray-900'
                      )}>
                        {item.name}
                      </p>
                      <p className={clsx(
                        'text-xs transition-colors truncate',
                        isActive ? 'text-white/80' : 'text-gray-500'
                      )}>
                        {item.description}
                      </p>
                    </div>

                    {/* Active indicator */}
                    {isActive && (
                      <div className="absolute right-2 w-1.5 h-8 bg-white rounded-full shadow-soft animate-scale-in" />
                    )}

                    {/* Hover gradient overlay */}
                    {!isActive && (
                      <div className={clsx(
                        'absolute inset-0 rounded-xl bg-gradient-to-r opacity-0 group-hover:opacity-5 transition-opacity',
                        item.gradient
                      )} />
                    )}
                  </Link>
                );
              })}
            </div>
          </div>

          {/* Secondary Navigation */}
          <div>
            <h3 className="px-3 mb-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">
              其他
            </h3>
            <div className="space-y-1">
              {secondaryNav.map((item) => {
                const isActive = location.pathname === item.href;
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    onClick={handleLinkClick}
                    className={clsx(
                      'group flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-300',
                      'hover:bg-gray-50',
                      isActive
                        ? 'bg-gray-100 text-primary-700 font-medium'
                        : 'text-gray-600 hover:text-gray-900'
                    )}
                  >
                    <item.icon className={clsx(
                      'w-4 h-4 transition-all duration-300',
                      isActive 
                        ? 'text-primary-600' 
                        : 'group-hover:text-primary-600 group-hover:scale-110'
                    )} />
                    <span className="text-sm">{item.name}</span>
                  </Link>
                );
              })}
            </div>
          </div>
        </nav>

        {/* Footer Stats */}
        <div className="p-4 border-t border-gray-200 space-y-3">
          {/* Storage */}
          <div className="px-3">
            <div className="flex items-center justify-between text-xs text-gray-600 mb-2">
              <span>存储空间</span>
              <span className="font-medium">2.4 / 10 GB</span>
            </div>
            <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-primary-500 to-accent-500 rounded-full transition-all duration-1000"
                style={{ width: '24%' }}
              >
                <div className="h-full w-full bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer" />
              </div>
            </div>
          </div>

          {/* Version */}
          <div className="px-3 text-xs text-gray-500 flex items-center justify-between">
            <span>IntelliPDF</span>
            <span className="px-2 py-0.5 bg-gray-100 rounded-full font-medium">v0.1.0</span>
          </div>
        </div>
      </aside>
    </>
  );
}
