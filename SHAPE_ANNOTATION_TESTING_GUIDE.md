# 图形标注系统功能测试指南

## 🎉 Phase 6 完成！

图形标注系统已完整实现，包括绘制、保存、加载和渲染功能。

---

## ✅ 已实现功能清单

### 1. 前端组件 (860行)

- **AnnotationToolbar** (175行)
  - ✅ 浮动工具栏界面
  - ✅ 多种标注模式切换
  - ✅ 工具激活状态显示
  - ✅ 操作提示信息

- **ShapeTool** (330行)
  - ✅ 矩形绘制工具
  - ✅ 圆形绘制工具
  - ✅ 箭头绘制工具
  - ✅ 实时虚线预览
  - ✅ ESC 取消绘制
  - ✅ PDF 坐标转换

- **PDFViewerEnhanced** (245行)
  - ✅ 工具栏集成
  - ✅ ShapeTool 渲染
  - ✅ 图形完成回调
  - ✅ 数据保存到后端
  - ✅ 页面/滚动双模式

- **数据转换** (80行)
  - ✅ 后端数据转前端格式
  - ✅ 从后端加载标注
  - ✅ 标注列表更新

- **渲染引擎** (30行)
  - ✅ AnnotationCanvas 图形渲染
  - ✅ 矩形/圆形/箭头显示
  - ✅ 样式和颜色支持

### 2. 后端修复 (30行)

- ✅ 创建标注 API 端点修复
- ✅ 数据库 schema 修复（data, user_name 列）
- ✅ metadata 约束修复
- ✅ 模型实例创建逻辑

### 3. 测试工具

- ✅ test_shape_annotations.py - API 测试脚本
- ✅ test_shape_rendering.html - 交互式测试页面
- ✅ fix_database_schema.py - 数据库修复脚本
- ✅ fix_metadata_constraint.py - 约束修复脚本

---

## 🧪 完整测试流程

### 准备工作

1. **启动后端服务器**
   ```powershell
   cd backend
   .\venv\Scripts\Activate.ps1
   python main.py
   ```
   等待看到 "Uvicorn running on http://0.0.0.0:8000"

2. **启动前端服务器**
   ```powershell
   cd frontend
   npm run dev
   ```
   应该显示 "Local: http://localhost:5174"

3. **验证服务状态**
   - 后端: http://localhost:8000/health
   - 前端: http://localhost:5174

---

### 测试 1: 绘制新图形标注

#### 步骤

1. 打开浏览器访问 http://localhost:5174
2. 上传或选择一个 PDF 文档
3. 点击左侧工具栏的 **"矩形"** 按钮
4. 在 PDF 页面上点击并拖拽鼠标
5. 释放鼠标，观察结果

#### 预期结果

- ✅ 拖拽时显示虚线预览
- ✅ 释放后显示蓝色矩形（#2196F3）
- ✅ 矩形有半透明填充
- ✅ 控制台显示 "Created annotation shape-xxx"
- ✅ Network 标签显示 POST /annotations/ 返回 201

#### 测试圆形和箭头

6. 点击 **"圆形"** 按钮，重复步骤 4-5
7. 点击 **"箭头"** 按钮，重复步骤 4-5

---

### 测试 2: 刷新页面后持久化

#### 步骤

1. 按照测试 1 创建几个图形标注
2. 按 F5 刷新页面
3. 等待页面加载完成
4. 观察 PDF 页面

#### 预期结果

- ✅ 所有之前绘制的图形仍然显示
- ✅ 图形位置、大小、颜色正确
- ✅ 控制台显示 "Loaded N annotations from backend"
- ✅ Network 标签显示 GET /annotations/documents/{id} 返回 200

---

### 测试 3: 多页面支持

#### 步骤

1. 打开一个多页 PDF 文档
2. 在第 1 页绘制一个矩形
3. 翻到第 2 页
4. 在第 2 页绘制一个圆形
5. 返回第 1 页
6. 刷新页面

#### 预期结果

- ✅ 第 1 页显示矩形，不显示圆形
- ✅ 第 2 页显示圆形，不显示矩形
- ✅ 刷新后每页的标注仍然正确显示

---

### 测试 4: 页面模式 vs 滚动模式

#### 页面模式测试

1. 确保处于页面模式（顶部工具栏显示 "第 X / Y 页"）
2. 绘制图形，验证显示正常
3. 使用上一页/下一页按钮切换
4. 验证每页的标注独立显示

#### 滚动模式测试

5. 点击工具栏的 "阅读模式" 按钮切换到滚动模式
6. 滚动到不同页面
7. 在不同页面绘制图形
8. 验证所有图形正确显示

#### 预期结果

- ✅ 两种模式下绘制功能正常
- ✅ 标注显示位置准确
- ✅ 模式切换不影响已有标注

---

### 测试 5: 缩放功能

#### 步骤

1. 创建一个图形标注
2. 点击 "放大" 按钮（或按 Ctrl +）
3. 观察图形标注
4. 点击 "缩小" 按钮（或按 Ctrl -）
5. 观察图形标注

#### 预期结果

- ✅ 图形随 PDF 内容同步缩放
- ✅ 线条粗细保持视觉一致
- ✅ 图形位置相对 PDF 内容不变

---

### 测试 6: API 端点测试

使用测试脚本验证后端功能：

```powershell
python test_shape_annotations.py
```

#### 预期输出

```
============================================================
图形标注工具测试
============================================================

1. 检查后端健康状态...
   ✅ 后端正常

2. 获取文档列表...
   ✅ 找到文档: Linux教程.pdf

3. 创建矩形标注...
   ✅ 矩形标注创建成功

4. 创建圆形标注...
   ✅ 圆形标注创建成功

5. 创建箭头标注...
   ✅ 箭头标注创建成功
```

---

### 测试 7: 数据格式验证

#### 使用测试 HTML 页面

1. 打开 `test_shape_rendering.html`（双击文件或拖到浏览器）
2. 点击 "获取文档列表" 按钮
3. 点击 "获取标注列表" 按钮
4. 展开 "查看数据" 查看 JSON 格式

#### 验证数据结构

后端返回的数据应该包含：

```json
{
  "annotations": [
    {
      "id": "uuid",
      "annotation_type": "shape",
      "page_number": 1,
      "data": {
        "shapeType": "rectangle",
        "geometry": { "rect": {...} },
        "style": { "color": "#2196F3", ... }
      },
      ...
    }
  ],
  "total": 3
}
```

---

## 🐛 故障排除

### 问题 1: 图形不显示

**症状**: 绘制后图形立即消失，或刷新后不显示

**诊断步骤**:

1. 打开浏览器控制台（F12）
2. 查看 Console 标签是否有错误
3. 检查 Network 标签：
   - POST /annotations/ 是否返回 201
   - GET /annotations/documents/{id} 是否返回 200
4. 查看返回的 JSON 数据格式

**常见原因**:

- ❌ API 请求失败（检查后端是否运行）
- ❌ 数据格式不匹配（检查 `data` 字段结构）
- ❌ 坐标转换错误（检查 `geometry` 字段）

**解决方案**:

```javascript
// 在浏览器控制台运行：
// 检查 transformBackendAnnotation 函数
console.log(window.annotations);  // 查看当前标注列表

// 手动测试转换
fetch('http://localhost:8000/api/v1/annotations/documents/{DOC_ID}')
  .then(r => r.json())
  .then(data => console.log(data));
```

---

### 问题 2: 控制台错误 "annotations.map is not a function"

**原因**: 后端返回的数据结构不是数组

**解决方案**:

检查 `PDFViewerEnhanced.tsx` 第 148 行：

```typescript
const backendAnnotations = resp.annotations || [];  // 确保使用 resp.annotations
```

---

### 问题 3: 图形位置偏移

**原因**: 坐标系统不一致

**验证步骤**:

1. 在 ShapeTool 中添加调试日志：
   ```typescript
   console.log('PDF coords:', startPoint, currentPoint);
   console.log('Screen coords:', screenStart, screenCurrent);
   ```

2. 在 AnnotationCanvas 中添加调试日志：
   ```typescript
   console.log('Rendering shape:', annotation.geometry);
   console.log('Screen rect:', rect);
   ```

**解决方案**:

确保使用正确的坐标转换：
- 绘制时：`viewport.convertToPdfPoint(screenX, screenY)`
- 渲染时：`pdfCoordinateService.rectangleToScreen(pdfRect, viewport)`

---

### 问题 4: 数据库错误

**症状**: "table annotations has no column named data"

**解决方案**:

```powershell
python fix_database_schema.py
python fix_metadata_constraint.py
```

---

## 📊 性能监控

### 渲染性能

使用浏览器性能工具：

1. 打开 DevTools → Performance
2. 点击 "Record"
3. 在 PDF 上绘制几个图形
4. 停止录制
5. 查看火焰图

**预期指标**:

- 每帧渲染时间 < 16ms (60 FPS)
- Canvas 绘制时间 < 5ms
- 无明显卡顿或掉帧

### 内存使用

1. 打开 DevTools → Memory
2. 拍摄堆快照
3. 绘制 50 个图形
4. 再次拍摄快照
5. 比较差异

**预期结果**:

- 内存增长 < 10MB
- 无明显内存泄漏
- GC 回收正常

---

## 🎯 验收标准

Phase 6 完成的标志：

- ✅ 可以在 PDF 上绘制矩形、圆形、箭头
- ✅ 绘制时显示实时预览
- ✅ 释放鼠标后图形立即显示
- ✅ 图形自动保存到后端数据库
- ✅ 刷新页面后图形仍然显示
- ✅ 多页 PDF 中每页的图形独立管理
- ✅ 缩放功能正常，图形跟随 PDF 缩放
- ✅ 页面模式和滚动模式都支持
- ✅ 无控制台错误或警告
- ✅ API 测试全部通过
- ✅ 数据持久化正常

---

## 🚀 下一步开发

Phase 7 计划功能：

### 1. 标注编辑 (优先级：高)

- 点击选中图形标注
- 拖拽移动标注
- 8 个控制点调整大小
- 边界检测和约束

### 2. 删除功能 (优先级：高)

- Delete 键删除选中标注
- 右键菜单删除选项
- 确认对话框
- 后端同步删除

### 3. 样式编辑器 (优先级：中)

- 颜色选择器
- 透明度滑块
- 线宽调整
- 填充样式切换

---

## 📸 测试截图位置

建议截图保存到 `docs/screenshots/` 目录：

- `shape-toolbar.png` - 工具栏界面
- `rectangle-drawing.png` - 矩形绘制过程
- `circle-drawing.png` - 圆形绘制过程
- `arrow-drawing.png` - 箭头绘制过程
- `multi-shapes.png` - 多个图形显示
- `console-success.png` - 成功的控制台输出
- `network-api.png` - 网络请求记录

---

## 📝 测试报告模板

完成测试后，请填写以下报告：

```
测试日期: 2025-10-08
测试人: [姓名]
测试环境:
  - 浏览器: Chrome 120.0
  - 操作系统: Windows 11
  - 前端版本: v1.0
  - 后端版本: v1.0

测试结果:
  [ ] 测试 1: 绘制新图形标注 - 通过/失败
  [ ] 测试 2: 刷新页面后持久化 - 通过/失败
  [ ] 测试 3: 多页面支持 - 通过/失败
  [ ] 测试 4: 页面模式 vs 滚动模式 - 通过/失败
  [ ] 测试 5: 缩放功能 - 通过/失败
  [ ] 测试 6: API 端点测试 - 通过/失败
  [ ] 测试 7: 数据格式验证 - 通过/失败

发现的问题:
1. [描述问题]
2. [描述问题]

建议改进:
1. [改进建议]
2. [改进建议]

总体评价: 优秀/良好/合格/不合格
```

---

**Phase 6 状态**: ✅ **100% 完成**

**下一阶段**: Phase 7 - 标注编辑和删除功能

**预计时间**: 2-3 天
