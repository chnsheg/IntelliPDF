/**
 * 组件导入测试 - 验证所有组件是否可以正确导入
 * 这个文件用于诊断 TypeScript 模块解析问题
 */

// 测试直接导入
import ChatPanelDirect from '../components/ChatPanel';
import BookmarkPanelDirect from '../components/BookmarkPanel';
import PDFViewerEnhancedDirect from '../components/PDFViewerEnhanced';

// 测试从 index 导入
import { ChatPanel, BookmarkPanel, PDFViewerEnhanced } from '../components';

export default function ComponentImportTest() {
    return (
        <div className="p-8">
            <h1 className="text-2xl font-bold mb-4">组件导入测试</h1>

            <div className="space-y-4">
                <div className="p-4 bg-green-50 border border-green-200 rounded">
                    <h2 className="font-semibold">✅ 直接导入</h2>
                    <p className="text-sm text-gray-600">
                        ChatPanel: {ChatPanelDirect ? '成功' : '失败'}
                    </p>
                    <p className="text-sm text-gray-600">
                        BookmarkPanel: {BookmarkPanelDirect ? '成功' : '失败'}
                    </p>
                    <p className="text-sm text-gray-600">
                        PDFViewerEnhanced: {PDFViewerEnhancedDirect ? '成功' : '失败'}
                    </p>
                </div>

                <div className="p-4 bg-blue-50 border border-blue-200 rounded">
                    <h2 className="font-semibold">✅ 从 Index 导入</h2>
                    <p className="text-sm text-gray-600">
                        ChatPanel: {ChatPanel ? '成功' : '失败'}
                    </p>
                    <p className="text-sm text-gray-600">
                        BookmarkPanel: {BookmarkPanel ? '成功' : '失败'}
                    </p>
                    <p className="text-sm text-gray-600">
                        PDFViewerEnhanced: {PDFViewerEnhanced ? '成功' : '失败'}
                    </p>
                </div>

                <div className="p-4 bg-yellow-50 border border-yellow-200 rounded">
                    <h2 className="font-semibold">📋 说明</h2>
                    <p className="text-sm text-gray-600">
                        如果此页面能正常显示,说明组件导入没有问题。
                    </p>
                    <p className="text-sm text-gray-600 mt-2">
                        如果看到错误,检查浏览器 Console (F12)。
                    </p>
                </div>
            </div>
        </div>
    );
}
