# 功能测试指南

## 已修复功能测试

### 1. 书签跳转功能 ✅

**测试步骤**:
1. 启动前端: `cd frontend && npm run dev`
2. 打开已有文档(例如Linux教程.pdf)
3. 点击左侧书签面板中的书签条目
4. 点击右上角的书签图标(跳转按钮)

**预期结果**:
- PDF应该滚动到书签所在的页面
- 当前页码显示应该更新

**测试命令**:
```powershell
# 启动前端测试
cd frontend
npm run dev
# 访问 http://localhost:5173
```

### 2. AI提问流程优化 ✅

**测试步骤**:
1. 在PDF中选中一段文字
2. 点击"AI提问"按钮(或自动打开聊天面板)
3. 查看输入框上方是否显示蓝色背景的"选中文本"区域
4. 输入框placeholder应显示"针对选中文本提问..."
5. 输入问题并发送

**预期结果**:
- 选中文本显示在输入框上方,包含页码信息
- 输入框有针对性的提示
- AI回答应该基于选中文本和上下文

## 待实现功能

### 3. 标注位置修复 (紧急)

**问题**: 高亮、下划线等标注的位置不正确

**解决方案**: 需要修复PDF坐标转换
```typescript
// 在PDFViewerEnhanced.tsx中添加坐标转换函数
function convertScreenToPDF(screenCoords, pageInfo) {
  const { pageHeight, scale } = pageInfo;
  return {
    x: screenCoords.x / scale,
    y: pageHeight - (screenCoords.y / scale), // Y轴翻转
    width: screenCoords.width / scale,
    height: screenCoords.height / scale
  };
}
```

### 4. 标签生成流程优化

**需求**: 点击"生成标签"时跳转到标签栏

**实现方案**:
1. 在DocumentViewerPage中添加标签面板
2. 点击"生成标签"按钮时:
   - 打开标签面板
   - 根据选中文字智能推荐标签名称
   - 允许用户自定义

### 5. 文本批注功能

**需求**: 可以在PDF上添加文字批注

**实现方案**:
1. 双击PDF空白处创建批注
2. 批注可拖动、调整大小
3. 批注保存到数据库
4. 支持编辑和删除

## 快速验证脚本

### 测试书签跳转
```javascript
// 在浏览器控制台执行
// 触发跳转到第100页
window.dispatchEvent(new CustomEvent('jumpToPage', { 
  detail: { page_number: 100 } 
}));
```

### 测试AI提问流程
```javascript
// 在浏览器控制台执行
// 模拟选中文本
const mockSelection = {
  text: "测试选中的文本",
  pageNumber: 10,
  position: { x: 100, y: 200, width: 150, height: 20 }
};
// 触发文本选择事件
window.dispatchEvent(new CustomEvent('textSelected', { 
  detail: mockSelection 
}));
```

## 开发环境启动

### 后端
```powershell
cd D:\IntelliPDF\backend
.\venv\Scripts\Activate.ps1
python main.py
# 访问 http://localhost:8000
```

### 前端
```powershell
cd D:\IntelliPDF\frontend
npm run dev
# 访问 http://localhost:5173
```

## 问题排查

### 书签跳转不工作
1. 检查浏览器控制台是否有错误
2. 确认PDFViewerEnhanced是否正确监听jumpToPage事件
3. 检查BookmarkPanel的handleJump函数是否被调用

### AI提问没有显示选中文本
1. 检查selectedText和currentPage props是否正确传递
2. 确认ChatPanel是否接收到props
3. 查看输入框上方的蓝色区域是否渲染

### 标注位置不正确
1. 检查getSelection()返回的坐标
2. 确认page.getViewport()的scale参数
3. 验证坐标转换函数是否正确

## 下一步开发任务

按优先级排序:
1. **修复标注坐标系统** - 2小时
2. **实现TextSelectionToolbar** - 3小时
3. **完善后端标注API** - 2小时
4. **实现标注渲染层** - 3小时
5. **实现文本批注功能** - 4小时
6. **实现标签管理面板** - 2小时

预计总时间: 16小时

需要开始哪个任务?
