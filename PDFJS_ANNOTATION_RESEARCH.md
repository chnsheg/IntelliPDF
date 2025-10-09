# PDF.js 标注 API 调研报告

## 目标
将当前的自定义 Canvas 标注系统迁移到 PDF.js 原生标注 API，以获得更好的兼容性和标准化支持。

## PDF.js 标注系统架构

### 1. 核心层级（从下到上）

```
┌──────────────────────────────────────┐
│ Canvas Layer (z=0)                   │  PDF 页面渲染
├──────────────────────────────────────┤
│ Text Layer (z=1)                     │  文本选择层
├──────────────────────────────────────┤
│ Annotation Layer (z=2)               │  显示已有标注（只读）
├──────────────────────────────────────┤
│ Annotation Editor Layer (z=3)        │  编辑/创建标注
└──────────────────────────────────────┘
```

### 2. 关键 API 组件

#### A. AnnotationLayer（显示层）
- **用途**: 渲染 PDF 中已存在的标注（从 PDF 文件读取）
- **特点**: 只读，显示高亮、链接、注释等
- **API**: `pdfjsLib.AnnotationLayer.render()`
- **限制**: 不能创建新标注，只能显示

#### B. AnnotationEditorLayer（编辑层）✅ **重点**
- **用途**: 创建和编辑标注
- **支持类型**:
  - `FreeText`: 文本框标注
  - `Ink`: 手绘/画笔标注
  - `Stamp`: 图章标注
  - `Highlight`: 文本高亮（PDF.js 3.0+）
- **API**: `pdfjsLib.AnnotationEditorLayer`
- **事件**: 
  - `annotationeditorlayerrendered`: 层渲染完成
  - `annotationeditorstateschanged`: 标注状态改变

#### C. AnnotationStorage（数据存储）
- **用途**: 存储标注数据（内存中）
- **API**: 
  - `pdfDocument.annotationStorage`
  - `.setValue(key, value)`: 设置标注数据
  - `.getAll()`: 获取所有标注
  - `.serializable`: 可序列化的标注数据
- **导出**: 可导出为 PDF 标注格式

### 3. React-PDF 集成

react-pdf 默认会渲染 `annotationLayer`，但 **不会自动启用编辑功能**。

#### 现有配置
```tsx
<Page
  pageNumber={pageNum}
  scale={scale}
  renderTextLayer={true}           // ✅ 已启用
  renderAnnotationLayer={true}     // ✅ 已启用（只读显示）
  // ⚠️ 缺少编辑层配置
/>
```

#### 需要添加的配置
```tsx
<Page
  pageNumber={pageNum}
  scale={scale}
  renderTextLayer={true}
  renderAnnotationLayer={true}
  // 🆕 启用编辑模式
  onGetAnnotationsSuccess={(annotations) => {
    // 处理加载的标注
  }}
/>
```

## 标注类型对应关系

### 当前系统 → PDF.js 映射

| 当前功能 | 当前实现    | PDF.js 对应          | 迁移难度 |
| -------- | ----------- | -------------------- | -------- |
| 高亮文本 | Canvas 绘制 | Highlight Annotation | ⭐⭐ 中等  |
| 下划线   | Canvas 绘制 | Underline Annotation | ⭐⭐ 中等  |
| 删除线   | Canvas 绘制 | StrikeOut Annotation | ⭐⭐ 中等  |
| 矩形     | Canvas 绘制 | Ink (FreeHand)       | ⭐⭐⭐ 较难 |
| 圆形     | Canvas 绘制 | Ink (FreeHand)       | ⭐⭐⭐ 较难 |
| 箭头     | Canvas 绘制 | Ink (FreeHand)       | ⭐⭐⭐ 较难 |
| 便笺     | 自定义组件  | FreeText Annotation  | ⭐⭐ 中等  |
| 画笔     | Canvas 路径 | Ink Annotation       | ⭐ 简单   |

### 问题分析

#### ⚠️ 限制 1: 矩形/圆形不是标准 PDF 标注类型
PDF.js 的 `AnnotationEditorLayer` **不直接支持**矩形、圆形、多边形等几何图形标注。

**解决方案选项**:
1. **使用 Ink 标注模拟** ⭐ 推荐
   - 用 Ink 路径绘制矩形/圆形轮廓
   - 优点: PDF.js 原生支持
   - 缺点: 失去几何属性（无法精确调整）

2. **使用 Stamp 标注**
   - 上传矩形/圆形图片作为图章
   - 优点: 可拖拽、调整大小
   - 缺点: 需要预生成图片

3. **扩展 PDF.js**（不推荐）
   - 修改 PDF.js 源码添加几何图形支持
   - 优点: 完全控制
   - 缺点: 维护成本高、升级困难

#### ⚠️ 限制 2: 高亮标注需要文本坐标
PDF.js 的高亮标注需要精确的 PDF 文本坐标（QuadPoints）。

**当前系统**: 已实现 `textAnchor` 和 `quadPoints` 提取 ✅

#### ⚠️ 限制 3: 数据持久化
PDF.js 的 `AnnotationStorage` 是**内存数据结构**，不会自动保存到后端。

**解决方案**:
- 监听 `annotationeditorstateschanged` 事件
- 提取 `.serializable` 数据
- 手动发送到后端 API

## 推荐的重构方案

### 方案 A: 完全迁移到 PDF.js（激进）❌ 不推荐

**优点**:
- 标准化、兼容性好
- 减少自定义代码

**缺点**:
- 矩形/圆形/箭头无原生支持
- 需要大量 Ink 路径计算
- 失去精确几何属性
- UI 定制受限

### 方案 B: 混合架构（保守）✅ **推荐**

**文本标注**: 使用 PDF.js Highlight/Underline/StrikeOut
**图形标注**: 保留当前 Canvas 实现
**便笺**: 使用 PDF.js FreeText
**画笔**: 使用 PDF.js Ink

**优点**:
- 保留图形标注的精确性
- 文本标注获得标准化支持
- 渐进式迁移，降低风险

**缺点**:
- 维护两套系统
- 代码复杂度略增

### 方案 C: 增强当前系统（实用）⭐⭐⭐ **最推荐**

**核心思路**: 保留自定义 Canvas 渲染，但兼容 PDF.js 数据格式

1. **数据层**: 使用 PDF 标准标注格式（XFA/FDF）
2. **渲染层**: 保留 Canvas（性能更好、定制性强）
3. **导出层**: 支持导出为标准 PDF 标注

**实现步骤**:
1. 修改后端数据模型，支持 PDF 标注格式
2. 前端增加 PDF.js AnnotationStorage 适配器
3. 添加标注导出功能（保存到 PDF）

**优点**:
- ✅ 保留所有现有功能
- ✅ 支持标准 PDF 标注导出
- ✅ 性能最优（Canvas 渲染）
- ✅ 完全定制化 UI

**缺点**:
- 需要维护格式转换逻辑

## 详细实现方案（方案 C）

### 阶段 1: 数据格式兼容

#### 后端改造
```python
# backend/app/schemas/annotation.py
class PDFAnnotationData(BaseModel):
    """PDF 标准标注数据格式"""
    annotationType: str  # Highlight, FreeText, Ink, Square, Circle
    rect: List[float]    # [x1, y1, x2, y2] PDF 坐标
    quadPoints: Optional[List[List[float]]]  # 文本标注
    inkList: Optional[List[List[Point]]]     # 画笔标注
    contents: Optional[str]  # 注释内容
    color: List[float]  # RGB [r, g, b]
    opacity: float
    # ... 其他 PDF 标注属性
```

#### 前端适配器
```typescript
// frontend/src/utils/pdfAnnotationAdapter.ts
export class PDFAnnotationAdapter {
    // 将自定义格式转换为 PDF 标注格式
    static toXFDF(annotation: Annotation): XFDFAnnotation {}
    
    // 从 PDF 标注格式转换为自定义格式
    static fromXFDF(xfdf: XFDFAnnotation): Annotation {}
    
    // 导出为 PDF.js AnnotationStorage 格式
    static toAnnotationStorage(annotations: Annotation[]): Map {}
}
```

### 阶段 2: 渲染层保持不变

**保留现有代码**:
- `AnnotationCanvas.tsx` ✅
- `DraggableAnnotation.tsx` ✅
- `ShapeTool.tsx` ✅

**优势**:
- 无需重写 1000+ 行代码
- 保留所有功能和 UI
- 性能最优

### 阶段 3: 增加导出功能

```typescript
// 新增：导出标注到 PDF
async function exportAnnotationsToPDF(documentId: string) {
    const annotations = await apiService.getAnnotationsForDocument(documentId);
    
    // 转换为 PDF.js 格式
    const storageData = PDFAnnotationAdapter.toAnnotationStorage(annotations);
    
    // 使用 PDF.js 写入标注
    const pdfDoc = await pdfjsLib.getDocument(pdfUrl).promise;
    pdfDoc.annotationStorage.setAll(storageData);
    
    // 保存 PDF（需要后端支持）
    await apiService.savePDFWithAnnotations(documentId, pdfDoc);
}
```

## 工作量评估

### 方案 A: 完全迁移到 PDF.js
- **时间**: 2-3 周
- **风险**: 高（功能缺失）
- **收益**: 中（标准化）

### 方案 B: 混合架构
- **时间**: 1-2 周
- **风险**: 中（系统复杂）
- **收益**: 中（部分标准化）

### 方案 C: 增强当前系统 ⭐
- **时间**: 3-5 天
- **风险**: 低（增量改进）
- **收益**: 高（兼容性+保留功能）

## 最终建议

**推荐方案 C**，原因：

1. ✅ **保留所有现有功能**（矩形、圆形、拖拽、调整大小）
2. ✅ **最小化重构成本**（只需添加适配层）
3. ✅ **向后兼容**（支持 PDF 标准格式导出）
4. ✅ **性能最优**（Canvas 渲染比 DOM 标注快）
5. ✅ **可扩展**（未来可选择性迁移部分功能到 PDF.js）

## 下一步行动

1. **确认方案**：需要用户确认选择哪个方案
2. **数据模型设计**：设计 PDF 标注数据结构
3. **实现适配器**：编写格式转换逻辑
4. **后端 API**：添加标注导出端点
5. **前端集成**：添加导出功能按钮
6. **测试验证**：确保兼容性

---

## 参考资料

- PDF.js API 文档: https://mozilla.github.io/pdf.js/api/
- PDF 标注规范: ISO 32000-2 (PDF 2.0)
- react-pdf 文档: https://github.com/wojtekmaj/react-pdf
