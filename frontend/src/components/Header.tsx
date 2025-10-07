/**
 * Modern Header Component with Glass Effect
 */

import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  FiMenu, FiUpload, FiSearch, FiBell, FiUser, FiSettings,
  FiLogOut, FiSun, FiMoon, FiCommand
} from 'react-icons/fi';
import { useUIStore } from '../stores';
import { useIsMobile } from '../hooks/useResponsive';

export default function Header() {
  const { toggleSidebar, theme, setTheme } = useUIStore();
  const isMobile = useIsMobile();
  const navigate = useNavigate();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light');
  };

  return (
    <header className="sticky top-0 z-30 glass border-b border-gray-200/50 backdrop-blur-xl">
      <div className="h-16 px-4 flex items-center justify-between">
        
        {/* Left: Menu + Logo + Search */}
        <div className="flex items-center gap-3 flex-1">
          {/* Menu Button */}
          <button
            onClick={toggleSidebar}
            className="group p-2 hover:bg-gray-100 rounded-xl transition-all duration-300 hover:scale-105 active:scale-95"
            aria-label="Toggle menu"
          >
            <FiMenu className="w-5 h-5 text-gray-700 group-hover:text-primary-600 transition-colors" />
          </button>

          {/* Logo */}
          <Link 
            to="/" 
            className="flex items-center gap-2 group"
          >
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-br from-primary-500 to-accent-500 rounded-xl blur-md opacity-50 group-hover:opacity-75 transition-opacity" />
              <div className="relative w-9 h-9 bg-gradient-to-br from-primary-600 to-accent-600 rounded-xl flex items-center justify-center shadow-lg group-hover:shadow-xl transition-shadow">
                <span className="text-white font-bold text-lg">I</span>
              </div>
            </div>
            {!isMobile && (
              <div className="flex flex-col">
                <h1 className="text-lg font-bold bg-gradient-to-r from-primary-600 to-accent-600 bg-clip-text text-transparent">
                  IntelliPDF
                </h1>
                <span className="text-xs text-gray-500 -mt-1">智能文档助手</span>
              </div>
            )}
          </Link>

          {/* Search Bar (Desktop) */}
          {!isMobile && (
            <div className="relative flex-1 max-w-xl ml-8">
              <div className="relative group">
                <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 group-focus-within:text-primary-600 transition-colors" />
                <input
                  type="text"
                  placeholder="搜索文档... (Ctrl+K)"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-xl text-sm
                           focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
                           transition-all duration-300 hover:bg-gray-100"
                />
                <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1 text-xs text-gray-400">
                  <FiCommand className="w-3 h-3" />
                  <span>K</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-2">
          
          {/* Search Icon (Mobile) */}
          {isMobile && (
            <button
              className="p-2 hover:bg-gray-100 rounded-xl transition-all duration-300 hover:scale-105"
              aria-label="Search"
            >
              <FiSearch className="w-5 h-5 text-gray-700" />
            </button>
          )}

          {/* Upload Button */}
          <button
            onClick={() => navigate('/upload')}
            className="group relative overflow-hidden bg-gradient-to-r from-primary-600 to-primary-700 text-white px-4 py-2 rounded-xl font-medium shadow-soft hover:shadow-lg transition-all duration-300 hover:scale-105 active:scale-95"
          >
            <div className="relative flex items-center gap-2 z-10">
              <FiUpload className="w-4 h-4 group-hover:animate-bounce-soft" />
              {!isMobile && <span>上传</span>}
            </div>
            {/* Shine effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />
          </button>

          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="relative p-2 hover:bg-gray-100 rounded-xl transition-all duration-300 hover:scale-105 group"
            aria-label="Toggle theme"
          >
            <div className="relative w-5 h-5">
              <FiSun className={`absolute inset-0 text-yellow-500 transition-all duration-300 ${
                theme === 'light' ? 'opacity-100 rotate-0' : 'opacity-0 rotate-180'
              }`} />
              <FiMoon className={`absolute inset-0 text-purple-600 transition-all duration-300 ${
                theme === 'dark' ? 'opacity-100 rotate-0' : 'opacity-0 -rotate-180'
              }`} />
            </div>
          </button>

          {/* Notifications */}
          <div className="relative">
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className="relative p-2 hover:bg-gray-100 rounded-xl transition-all duration-300 hover:scale-105"
              aria-label="Notifications"
            >
              <FiBell className="w-5 h-5 text-gray-700" />
              {/* Badge */}
              <span className="absolute top-1 right-1 w-2 h-2 bg-error-500 rounded-full animate-pulse" />
            </button>

            {/* Notifications Dropdown */}
            {showNotifications && (
              <>
                <div 
                  className="fixed inset-0 z-20" 
                  onClick={() => setShowNotifications(false)}
                />
                <div className="absolute right-0 mt-2 w-80 bg-white rounded-2xl shadow-soft-lg border border-gray-100 overflow-hidden z-30 animate-fade-in-down">
                  <div className="p-4 border-b border-gray-100">
                    <h3 className="font-semibold text-gray-900">通知</h3>
                  </div>
                  <div className="max-h-96 overflow-y-auto scrollbar-thin">
                    {/* Empty state */}
                    <div className="p-8 text-center">
                      <FiBell className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                      <p className="text-sm text-gray-500">暂无新通知</p>
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>

          {/* User Menu */}
          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="group relative p-1 hover:bg-gray-100 rounded-xl transition-all duration-300 hover:scale-105"
              aria-label="User menu"
            >
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-br from-primary-500 to-accent-500 rounded-lg blur-sm opacity-0 group-hover:opacity-75 transition-opacity" />
                <div className="relative w-8 h-8 bg-gradient-to-br from-primary-600 to-accent-600 rounded-lg flex items-center justify-center text-white font-medium shadow-soft">
                  <FiUser className="w-4 h-4" />
                </div>
              </div>
            </button>

            {/* User Dropdown */}
            {showUserMenu && (
              <>
                <div 
                  className="fixed inset-0 z-20" 
                  onClick={() => setShowUserMenu(false)}
                />
                <div className="absolute right-0 mt-2 w-56 bg-white rounded-2xl shadow-soft-lg border border-gray-100 overflow-hidden z-30 animate-fade-in-down">
                  <div className="p-4 border-b border-gray-100">
                    <p className="font-semibold text-gray-900">用户中心</p>
                    <p className="text-xs text-gray-500 mt-0.5">user@example.com</p>
                  </div>
                  <div className="py-2">
                    <button className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 transition-colors flex items-center gap-3 group">
                      <FiUser className="w-4 h-4 text-gray-400 group-hover:text-primary-600 transition-colors" />
                      <span>个人资料</span>
                    </button>
                    <button className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 transition-colors flex items-center gap-3 group">
                      <FiSettings className="w-4 h-4 text-gray-400 group-hover:text-primary-600 transition-colors" />
                      <span>设置</span>
                    </button>
                  </div>
                  <div className="p-2 border-t border-gray-100">
                    <button className="w-full px-4 py-2 text-left text-sm text-error-600 hover:bg-error-50 rounded-lg transition-colors flex items-center gap-3 group">
                      <FiLogOut className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                      <span>退出登录</span>
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
