"""
前端标注功能测试脚本

在浏览器控制台中运行这些命令来测试标注功能
"""

# 测试 1: 检查 PDFViewerNative 组件是否加载
print("""
// 1. 检查组件是否加载
document.querySelector('canvas')?.width > 0 ? '✅ PDF 已渲染' : '❌ PDF 未渲染'
""")

# 测试 2: 检查工具栏
print("""
// 2. 检查工具栏按钮
const toolbar = document.querySelectorAll('button');
console.log('工具栏按钮数量:', toolbar.length);
toolbar.length > 5 ? '✅ 工具栏正常' : '❌ 工具栏缺失'
""")

# 测试 3: 模拟点击画笔工具
print("""
// 3. 激活画笔工具
const inkButton = Array.from(document.querySelectorAll('button')).find(b => b.textContent?.includes('画笔'));
if (inkButton) {
    inkButton.click();
    console.log('✅ 画笔工具已激活');
} else {
    console.log('❌ 找不到画笔按钮');
}
""")

# 测试 4: 检查标注层
print("""
// 4. 检查标注相关的 DOM 元素
const canvas = document.querySelector('canvas');
const textLayer = document.querySelector('.textLayer');
const annotationLayer = document.querySelector('.annotationLayer');
const editorLayer = document.querySelector('.annotationEditorLayer');

console.log('Canvas:', canvas ? '✅' : '❌');
console.log('TextLayer:', textLayer ? '✅' : '❌');
console.log('AnnotationLayer:', annotationLayer ? '✅' : '❌');
console.log('EditorLayer:', editorLayer ? '✅' : '❌');
""")

# 测试 5: 模拟创建画笔标注
print("""
// 5. 模拟画笔标注（在 PDF 上绘制）
// 打开浏览器控制台，激活画笔工具后：
// - 在 PDF 上按住鼠标拖拽
// - 释放鼠标完成绘制
// - 查看控制台是否有 '[InkEditor] Created annotation' 日志
// - 查看右下角是否有 '保存中...' 提示
""")

# 测试 6: 检查标注数据
print("""
// 6. 检查本地存储的标注数据（开发者工具 -> Application -> IndexedDB）
// 或者直接在控制台运行：
window.localStorage.getItem('pdfjs.history');
""")

# 测试 7: 测试选择和删除
print("""
// 7. 测试选择和删除标注
// - 点击 '选择' 按钮
// - 点击已保存的标注（应该有蓝色边框）
// - 按 Delete 或 Backspace 键删除
// - 查看控制台是否有 '[SelectMode] Deleted annotation' 日志
""")

# 测试 8: 测试文本标注
print("""
// 8. 测试文本标注
const textButton = Array.from(document.querySelectorAll('button')).find(b => b.textContent?.includes('文本'));
if (textButton) {
    textButton.click();
    console.log('✅ 文本工具已激活，点击 PDF 任意位置添加文本');
}
""")

# 测试 9: 测试图章标注
print("""
// 9. 测试图章标注
const stampButton = Array.from(document.querySelectorAll('button')).find(b => b.textContent?.includes('图章'));
if (stampButton) {
    stampButton.click();
    console.log('✅ 图章工具已激活，点击 PDF 任意位置上传图片');
}
""")

# 测试 10: 刷新页面验证持久化
print("""
// 10. 测试标注持久化
// - 创建几个标注
// - 等待 '保存中...' 消失
// - 刷新页面 (F5)
// - 检查标注是否还在
location.reload();
""")

print("\n=== 手动测试步骤 ===\n")
print("1. 打开浏览器访问: http://localhost:5174/annotation-test")
print("2. 打开开发者工具 (F12) -> Console 标签")
print("3. 选择一个 PDF 文档")
print("4. 依次测试上面的功能")
print("5. 观察控制台日志和网络请求")
print("\n=== 预期结果 ===\n")
print("✅ PDF 正常渲染")
print("✅ 工具栏按钮可点击")
print("✅ 画笔可以绘制")
print("✅ 文本框可以输入")
print("✅ 图章可以上传图片")
print("✅ 标注可以选中和删除")
print("✅ 标注保存后刷新页面仍显示")
print("\n=== 网络请求检查 ===\n")
print("开发者工具 -> Network 标签，应该看到：")
print("- POST /api/v1/annotations/batch (保存标注)")
print("- GET /api/v1/annotations/documents/{id} (加载标注)")
print("- DELETE /api/v1/annotations/documents/{id} (删除标注)")
