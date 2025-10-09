# PDF.js 原生标注系统 - 测试指南

## 当前实现状态

### ✅ 已完成功能

1. **后端 API**
   - ✅ 批量创建标注: `POST /api/v1/annotations/batch`
   - ✅ 删除文档所有标注: `DELETE /api/v1/annotations/documents/{document_id}`

2. **前端组件**
   - ✅ PDFViewerNative: 纯 PDF.js 实现的查看器
   - ✅ PDFAnnotationToolbar: 简化的标注工具栏
   - ✅ usePDFAnnotations: 标注数据管理 Hook
   - ✅ PDFAnnotationTestPage: 测试页面

3. **标注功能**
   - ✅ 画笔 (Ink): 鼠标拖拽绘制
   - ✅ 文本框 (FreeText): 点击添加文本
   - ✅ 文本选择层 (TextLayer): 透明文本用于选择

### 🚧 待实现功能

1. **标注类型**
   - ⏳ 图章 (Stamp): 添加图片标注
   - ⏳ 高亮 (Highlight): 文本高亮 (PDF.js experimental)

2. **交互功能**
   - ⏳ 标注编辑: 选中标注后修改
   - ⏳ 标注删除: 右键菜单或工具栏
   - ⏳ 标注样式: 颜色、粗细、字体大小
   - ⏳ 撤销/重做

3. **数据持久化**
   - ✅ 保存标注到后端 (基础实现)
   - ⏳ 加载标注并渲染到 PDF
   - ⏳ 标注与 PDF.js AnnotationStorage 的完整集成

4. **UI/UX**
   - ⏳ 标注列表侧边栏
   - ⏳ 标注搜索和过滤
   - ⏳ 多页面标注同步

## 测试步骤

### 1. 启动服务

**后端** (如未启动):
```powershell
cd backend
.\start.bat
```

**前端** (如未启动):
```powershell
cd frontend
npm run dev
```

### 2. 访问测试页面

打开浏览器访问: **http://localhost:5173/annotation-test**

### 3. 功能测试

#### 画笔测试
1. 点击工具栏 "画笔" 按钮
2. 在 PDF 页面上按住鼠标拖拽绘制
3. 释放鼠标完成绘制
4. 打开浏览器控制台查看 `[InkEditor] Created annotation` 日志
5. 检查右下角是否显示 "保存中..." 提示

#### 文本框测试
1. 点击工具栏 "文本框" 按钮
2. 在 PDF 页面上点击任意位置
3. 输入文本，按 Enter 或点击外部完成
4. 查看控制台 `[FreeTextEditor] Created annotation` 日志
5. 检查保存状态提示

#### 文本选择测试
1. 点击工具栏 "选择" 按钮
2. 在 PDF 页面上用鼠标选择文本
3. 验证文本是否可以正常选择（透明文本层）

### 4. 验证数据持久化

#### 方法1: 检查后端数据库
```powershell
cd backend
python
>>> from sqlalchemy import create_engine, inspect
>>> engine = create_engine('sqlite:///data/intellipdf.db')
>>> inspector = inspect(engine)
>>> tables = inspector.get_table_names()
>>> print(tables)  # 应该包含 'annotations' 表
```

#### 方法2: API 调用测试
```powershell
# 获取某个文档的所有标注
curl http://localhost:8000/api/v1/annotations/documents/{document_id}
```

#### 方法3: 刷新页面
1. 创建标注后刷新页面
2. 观察标注是否被重新加载（当前版本可能不显示，因为渲染逻辑未完成）

## 已知问题

### 问题 1: 标注不显示
**现象**: 创建标注后，刷新页面标注不显示  
**原因**: 渲染逻辑未完成，需要实现 AnnotationLayerBuilder  
**状态**: 待修复

### 问题 2: 画笔路径不平滑
**现象**: 鼠标拖拽过快时路径断裂  
**原因**: 简化实现，未使用贝塞尔曲线平滑  
**状态**: 待优化

### 问题 3: 文本框位置不准确
**现象**: 文本框位置与点击位置有偏差  
**原因**: 未考虑 PDF 坐标系转换  
**状态**: 待修复

### 问题 4: 无法编辑或删除标注
**现象**: 创建后无法选中或删除标注  
**原因**: 交互功能未实现  
**状态**: 待实现

## 下一步开发计划

### Phase 1: 完善标注渲染 (优先级: 高)
- [ ] 实现 AnnotationLayerBuilder
- [ ] 从后端加载标注数据
- [ ] 将标注数据转换为 PDF.js 格式
- [ ] 渲染已保存的标注到页面

### Phase 2: 完善编辑功能 (优先级: 高)
- [ ] 标注选择: 点击标注进入编辑状态
- [ ] 标注删除: Del 键或工具栏按钮
- [ ] 标注移动: 拖拽改变位置
- [ ] 标注调整: 改变大小和形状

### Phase 3: 增强标注类型 (优先级: 中)
- [ ] 图章标注: 上传图片或使用预设图标
- [ ] 高亮标注: 文本选择后高亮
- [ ] 样式选择器: 颜色、粗细、字体

### Phase 4: 数据集成 (优先级: 中)
- [ ] 完整的 AnnotationStorage 集成
- [ ] 标准 PDF 标注格式导出
- [ ] 标注历史记录
- [ ] 多用户标注同步

### Phase 5: 删除旧代码 (优先级: 低)
- [ ] 删除 AnnotationCanvas.tsx (~300 行)
- [ ] 删除 DraggableAnnotation.tsx (~400 行)
- [ ] 删除 ShapeTool.tsx (~280 行)
- [ ] 删除 NoteTool.tsx (~280 行)
- [ ] 删除 HistoryManager.ts (~320 行)
- [ ] 更新路由和导入

## 技术细节

### PDF.js AnnotationEditorType 映射

```javascript
const AnnotationEditorType = {
    DISABLE: -1,  // 禁用编辑器
    NONE: 0,      // 选择模式
    FREETEXT: 3,  // 文本框
    HIGHLIGHT: 9, // 高亮 (experimental)
    STAMP: 13,    // 图章
    INK: 15,      // 画笔/手绘
};
```

### 标注数据格式 (后端)

```json
{
    "document_id": "uuid",
    "user_id": "uuid",
    "annotation_type": "pdfjs",
    "page_number": 1,
    "data": {
        "pdfjs_data": {
            "annotationType": 15,
            "pageIndex": 0,
            "paths": [
                [{ "x": 100, "y": 200 }, { "x": 150, "y": 250 }]
            ],
            "color": [1, 0, 0],
            "thickness": 2
        }
    }
}
```

### PDF.js AnnotationStorage 序列化格式

```javascript
// PDF.js 内部格式
const serializable = pdfDocument.annotationStorage.serializable;
// 示例输出:
{
    "ink_1234567890_0.123": {
        "annotationType": 15,
        "pageIndex": 0,
        // ... 其他属性
    }
}
```

## 性能优化建议

1. **延迟保存**: 使用 debounce 避免频繁 API 调用
2. **批量操作**: 一次性保存多个标注
3. **增量渲染**: 只渲染可见页面的标注
4. **Canvas 缓存**: 缓存已渲染的页面

## 调试技巧

### 控制台日志关键字
- `[PDFViewerNative]`: 组件生命周期
- `[InkEditor]`: 画笔编辑器事件
- `[FreeTextEditor]`: 文本框编辑器事件
- `[usePDFAnnotations]`: Hook 操作日志

### Chrome DevTools 断点
- `PDFViewerNative.tsx:250`: 画笔 mousedown 事件
- `PDFViewerNative.tsx:280`: 画笔保存逻辑
- `PDFViewerNative.tsx:310`: 文本框创建

### Network 监控
- 监控 `/api/v1/annotations/batch` 请求
- 检查请求体和响应状态
- 验证 JWT token 是否有效

## 相关文件清单

### 前端文件
- `frontend/src/components/PDFViewerNative.tsx` (312 行) - 主组件
- `frontend/src/components/PDFAnnotationToolbar.tsx` (120 行) - 工具栏
- `frontend/src/hooks/usePDFAnnotations.ts` (110 行) - 数据管理
- `frontend/src/pages/PDFAnnotationTestPage.tsx` (105 行) - 测试页面
- `frontend/src/services/api.ts` (+18 行) - API 方法
- `frontend/src/index.css` (+50 行) - 样式

### 后端文件
- `backend/app/api/v1/endpoints/annotations.py` (+105 行) - 批量 API

### 文档文件
- `PDFJS_ANNOTATION_RESEARCH.md` (470 行) - 技术研究
- `PDFJS_NATIVE_IMPLEMENTATION_PLAN.md` (226 行) - 实现计划
- `PDFJS_IMPLEMENTATION_PROGRESS.md` (226 行) - 进度追踪

## Git 提交历史

```bash
git log --oneline --graph -10
```

最新提交:
- `b682c30` feat: 添加 PDF.js 原生标注测试页面
- `cced576` feat: 实现 PDF.js 原生标注系统（画笔+文本框）
- `0f4b252` feat: 添加批量创建和删除标注的后端 API

## 联系与支持

如有问题请查看:
- 项目文档: `PROJECT_TODO.md`
- 架构文档: `ARCHITECTURE.md`
- Copilot 指令: `.github/copilot-instructions.md`
