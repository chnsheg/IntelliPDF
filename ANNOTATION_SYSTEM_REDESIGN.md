# PDF 标注系统重新设计方案

## 📅 创建时间
2025-10-08 19:00

---

## ❌ 当前方案的问题

### 1. 依赖屏幕坐标
```typescript
// 当前错误方案
const rect = selection.getRangeAt(0).getBoundingClientRect();
const position = { x: rect.left, y: rect.top };  // ❌ 屏幕坐标
```

**问题**：
- 缩放时位置错误
- 滚动后无法定位
- 重新打开文档失效
- 无法跨设备同步

### 2. 缺少文本锚点
**问题**：
- PDF 内容变化后无法重新定位
- 无法处理 PDF 版本更新
- 搜索功能无法关联标注

### 3. 不符合 PDF 标准
**问题**：
- 无法导出为标准 PDF 标注
- 无法与其他 PDF 软件互操作
- 缺少行业标准支持

---

## ✅ 行业标准解决方案

### 核心原理：**文本锚点 + PDF 原生坐标 + 四边形数组**

参考标准：
- **PDF 规范**：ISO 32000-2 (PDF 2.0) Annotation 标准
- **Adobe PDF Annotations**：TextMarkup Annotations
- **PDF.js Annotation API**：内置标注系统
- **W3C Web Annotations**：文本选择和锚点

---

## 🏗️ 新架构设计

### 1. 数据模型（三层定位）

```typescript
interface AnnotationData {
    // ==== 第一层：唯一标识 ====
    id: string;
    documentId: string;
    
    // ==== 第二层：文本锚点（TextAnchor）====
    textAnchor: {
        // 选中的文本内容
        selectedText: string;
        
        // 前后文片段（用于重新定位）
        prefix: string;    // 前 50 个字符
        suffix: string;    // 后 50 个字符
        
        // 页面内偏移量
        pageNumber: number;
        startOffset: number;  // 在页面文本中的起始字符位置
        endOffset: number;    // 结束字符位置
        
        // 文本指纹（用于验证）
        textHash: string;     // SHA-256 hash of page text
    };
    
    // ==== 第三层：PDF 原生坐标（QuadPoints）====
    pdfCoordinates: {
        pageNumber: number;
        
        // PDF 坐标系（origin: bottom-left, unit: points, 1pt = 1/72 inch）
        // 支持跨行选择的四边形数组
        quadPoints: Array<{
            // 四个顶点：左下、右下、左上、右上
            x1: number, y1: number,  // 左下
            x2: number, y2: number,  // 右下
            x3: number, y3: number,  // 左上
            x4: number, y4: number   // 右上
        }>;
        
        // 旋转角度（0, 90, 180, 270）
        rotation: number;
        
        // 页面尺寸（用于验证）
        pageWidth: number;
        pageHeight: number;
    };
    
    // ==== 第四层：样式和元数据 ====
    style: {
        type: 'highlight' | 'underline' | 'strikethrough' | 'text' | 'ink' | 'shape';
        color: string;        // RGB hex
        opacity: number;      // 0-1
        strokeWidth?: number; // for ink/shape
    };
    
    // ==== 第五层：批注内容（可选）====
    comment?: {
        text: string;
        author: string;
        createdAt: string;
        updatedAt: string;
    };
    
    metadata: {
        createdAt: string;
        updatedAt: string;
        userId: string;
    };
}
```

### 2. 文本锚点算法（TextAnchor）

#### 2.1 创建文本锚点
```typescript
async function createTextAnchor(
    selection: Selection,
    pageNumber: number,
    pdfPage: PDFPageProxy
): Promise<TextAnchor> {
    // 1. 获取页面完整文本
    const textContent = await pdfPage.getTextContent();
    const pageText = textContent.items.map(item => item.str).join('');
    
    // 2. 获取选中文本
    const selectedText = selection.toString();
    
    // 3. 计算选中文本在页面中的位置
    const startOffset = pageText.indexOf(selectedText);
    const endOffset = startOffset + selectedText.length;
    
    // 4. 提取前后文（用于重新定位）
    const prefix = pageText.substring(
        Math.max(0, startOffset - 50),
        startOffset
    );
    const suffix = pageText.substring(
        endOffset,
        Math.min(pageText.length, endOffset + 50)
    );
    
    // 5. 计算文本指纹
    const textHash = await sha256(pageText);
    
    return {
        selectedText,
        prefix,
        suffix,
        pageNumber,
        startOffset,
        endOffset,
        textHash
    };
}
```

#### 2.2 重新定位算法（Relocate）
```typescript
async function relocateAnnotation(
    anchor: TextAnchor,
    pdfPage: PDFPageProxy
): Promise<{ startOffset: number; endOffset: number } | null> {
    // 1. 获取当前页面文本
    const textContent = await pdfPage.getTextContent();
    const pageText = textContent.items.map(item => item.str).join('');
    
    // 2. 策略1：精确匹配（最快）
    const exactIndex = pageText.indexOf(anchor.selectedText);
    if (exactIndex !== -1) {
        return {
            startOffset: exactIndex,
            endOffset: exactIndex + anchor.selectedText.length
        };
    }
    
    // 3. 策略2：前后文匹配（中等）
    const contextPattern = `${anchor.prefix}(${escapeRegex(anchor.selectedText)})${anchor.suffix}`;
    const contextMatch = pageText.match(new RegExp(contextPattern));
    if (contextMatch && contextMatch.index !== undefined) {
        const startOffset = contextMatch.index + anchor.prefix.length;
        return {
            startOffset,
            endOffset: startOffset + anchor.selectedText.length
        };
    }
    
    // 4. 策略3：模糊匹配（最慢，最宽容）
    const fuzzyMatch = findFuzzyMatch(pageText, anchor.selectedText, 0.85);
    if (fuzzyMatch) {
        return fuzzyMatch;
    }
    
    // 5. 失败：返回 null
    console.warn('Failed to relocate annotation', anchor);
    return null;
}
```

### 3. PDF 原生坐标系统

#### 3.1 获取 QuadPoints（四边形数组）
```typescript
async function getQuadPoints(
    selection: Selection,
    pageNumber: number,
    pdfPage: PDFPageProxy
): Promise<QuadPoint[]> {
    const quadPoints: QuadPoint[] = [];
    const range = selection.getRangeAt(0);
    
    // 1. 获取选区的所有 ClientRect（支持跨行）
    const clientRects = range.getClientRects();
    
    // 2. 获取 PDF 视口
    const viewport = pdfPage.getViewport({ scale: 1.0 });
    
    // 3. 获取页面容器位置
    const pageElement = document.querySelector(`[data-page-number="${pageNumber}"]`);
    if (!pageElement) return quadPoints;
    const pageRect = pageElement.getBoundingClientRect();
    
    // 4. 转换每个 ClientRect 为 QuadPoint
    for (const rect of clientRects) {
        // 计算相对于页面的坐标
        const relX1 = rect.left - pageRect.left;
        const relY1 = rect.top - pageRect.top;
        const relX2 = rect.right - pageRect.left;
        const relY2 = rect.bottom - pageRect.top;
        
        // 转换为 PDF 坐标（原点在左下角）
        const [pdfX1, pdfY1] = viewport.convertToPdfPoint(relX1, relY1);
        const [pdfX2, pdfY2] = viewport.convertToPdfPoint(relX2, relY2);
        const [pdfX3, pdfY3] = viewport.convertToPdfPoint(relX1, relY2);
        const [pdfX4, pdfY4] = viewport.convertToPdfPoint(relX2, relY1);
        
        quadPoints.push({
            x1: pdfX1, y1: pdfY1,  // 左下
            x2: pdfX2, y2: pdfY2,  // 右下
            x3: pdfX3, y3: pdfY3,  // 左上
            x4: pdfX4, y4: pdfY4   // 右上
        });
    }
    
    return quadPoints;
}
```

#### 3.2 渲染 QuadPoints
```typescript
function renderQuadPoints(
    quadPoints: QuadPoint[],
    pdfPage: PDFPageProxy,
    scale: number,
    style: AnnotationStyle
): void {
    const viewport = pdfPage.getViewport({ scale });
    const canvas = getAnnotationCanvas(pdfPage.pageNumber);
    const ctx = canvas.getContext('2d');
    
    if (!ctx) return;
    
    quadPoints.forEach(quad => {
        // 转换为屏幕坐标
        const [x1, y1] = viewport.convertToViewportPoint(quad.x1, quad.y1);
        const [x2, y2] = viewport.convertToViewportPoint(quad.x2, quad.y2);
        const [x3, y3] = viewport.convertToViewportPoint(quad.x3, quad.y3);
        const [x4, y4] = viewport.convertToViewportPoint(quad.x4, quad.y4);
        
        // 绘制四边形
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.lineTo(x4, y4);
        ctx.lineTo(x3, y3);
        ctx.closePath();
        
        // 应用样式
        if (style.type === 'highlight') {
            ctx.fillStyle = hexToRgba(style.color, style.opacity);
            ctx.fill();
        } else if (style.type === 'underline') {
            ctx.strokeStyle = hexToRgba(style.color, style.opacity);
            ctx.lineWidth = style.strokeWidth || 2;
            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
            ctx.stroke();
        } else if (style.type === 'strikethrough') {
            ctx.strokeStyle = hexToRgba(style.color, style.opacity);
            ctx.lineWidth = style.strokeWidth || 2;
            const midY = (y1 + y3) / 2;
            ctx.beginPath();
            ctx.moveTo(x1, midY);
            ctx.lineTo(x2, midY);
            ctx.stroke();
        }
    });
}
```

### 4. 渲染架构（Canvas 覆盖层）

#### 4.1 三层渲染架构
```
┌─────────────────────────────────┐
│   PDF 内容层 (react-pdf)        │  ← PDF.js 渲染
├─────────────────────────────────┤
│   标注层 (Canvas)                │  ← 我们的标注渲染
├─────────────────────────────────┤
│   交互层 (React Components)     │  ← 工具栏、编辑器
└─────────────────────────────────┘
```

#### 4.2 Canvas 渲染组件
```typescript
const AnnotationCanvas: React.FC<{
    pageNumber: number;
    annotations: AnnotationData[];
    scale: number;
    pdfPage: PDFPageProxy;
}> = ({ pageNumber, annotations, scale, pdfPage }) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    
    useEffect(() => {
        if (!canvasRef.current) return;
        
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;
        
        // 清空画布
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // 设置画布尺寸（匹配 PDF 页面）
        const viewport = pdfPage.getViewport({ scale });
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        
        // 渲染所有标注
        annotations
            .filter(a => a.pdfCoordinates.pageNumber === pageNumber)
            .forEach(annotation => {
                renderQuadPoints(
                    annotation.pdfCoordinates.quadPoints,
                    pdfPage,
                    scale,
                    annotation.style
                );
            });
    }, [pageNumber, annotations, scale, pdfPage]);
    
    return (
        <canvas
            ref={canvasRef}
            className="absolute top-0 left-0 pointer-events-none"
            style={{ zIndex: 10 }}
        />
    );
};
```

---

## 🔧 实现路线图

### Phase 1：基础架构（2-3天）

#### 任务 1.1：数据模型和类型定义
```typescript
// frontend/src/types/annotation.ts
export interface TextAnchor { ... }
export interface QuadPoint { ... }
export interface AnnotationData { ... }
```

#### 任务 1.2：文本锚点服务
```typescript
// frontend/src/services/textAnchor.ts
export class TextAnchorService {
    async create(selection, pageNumber, pdfPage): Promise<TextAnchor>
    async relocate(anchor, pdfPage): Promise<{start, end} | null>
}
```

#### 任务 1.3：PDF 坐标服务
```typescript
// frontend/src/services/pdfCoordinates.ts
export class PDFCoordinateService {
    async getQuadPoints(selection, pageNumber, pdfPage): Promise<QuadPoint[]>
    renderQuadPoints(quadPoints, pdfPage, scale, style): void
}
```

#### 任务 1.4：Canvas 渲染组件
```typescript
// frontend/src/components/AnnotationCanvas.tsx
export const AnnotationCanvas: React.FC<Props>
```

### Phase 2：标注功能（2-3天）

#### 任务 2.1：创建标注
```typescript
// 点击"高亮"按钮时
async function createHighlight() {
    // 1. 创建文本锚点
    const textAnchor = await textAnchorService.create(selection, pageNum, pdfPage);
    
    // 2. 获取 PDF 坐标
    const quadPoints = await pdfCoordService.getQuadPoints(selection, pageNum, pdfPage);
    
    // 3. 构建完整数据
    const annotation: AnnotationData = {
        id: uuidv4(),
        documentId,
        textAnchor,
        pdfCoordinates: { pageNumber, quadPoints, rotation: 0, pageWidth, pageHeight },
        style: { type: 'highlight', color: '#FAEB96', opacity: 0.45 },
        metadata: { createdAt: new Date().toISOString(), userId }
    };
    
    // 4. 保存到后端
    await api.createAnnotation(annotation);
    
    // 5. 本地更新状态
    setAnnotations(prev => [...prev, annotation]);
}
```

#### 任务 2.2：加载和渲染标注
```typescript
// 页面加载时
async function loadAnnotations() {
    // 1. 从后端加载标注数据
    const annotations = await api.getAnnotations(documentId);
    
    // 2. 尝试重新定位（验证文本锚点）
    for (const annotation of annotations) {
        const pdfPage = await pdfDoc.getPage(annotation.pdfCoordinates.pageNumber);
        const relocated = await textAnchorService.relocate(annotation.textAnchor, pdfPage);
        
        if (!relocated) {
            console.warn('Annotation position changed', annotation.id);
            // 可以标记为"位置已变化"或尝试自动修复
        }
    }
    
    // 3. 渲染到 Canvas
    setAnnotations(annotations);
}
```

#### 任务 2.3：编辑和删除标注
```typescript
// 删除标注
async function deleteAnnotation(annotationId: string) {
    await api.deleteAnnotation(annotationId);
    setAnnotations(prev => prev.filter(a => a.id !== annotationId));
}

// 移动标注（更新 QuadPoints）
async function moveAnnotation(annotationId: string, newPosition: QuadPoint[]) {
    const updated = await api.updateAnnotation(annotationId, {
        pdfCoordinates: { ...annotation.pdfCoordinates, quadPoints: newPosition }
    });
    setAnnotations(prev => prev.map(a => a.id === annotationId ? updated : a));
}
```

### Phase 3：批注功能（2-3天）

#### 任务 3.1：文字批注（Popup Annotation）
```typescript
// 数据模型扩展
interface TextAnnotation extends AnnotationData {
    style: { type: 'text' };
    comment: {
        text: string;
        author: string;
        createdAt: string;
    };
    // 锚点位置（单个点）
    pdfCoordinates: {
        pageNumber: number;
        point: { x: number; y: number };
    };
}

// UI 组件
const TextAnnotationPopup: React.FC<{ annotation: TextAnnotation }> = ({ annotation }) => {
    return (
        <div className="absolute bg-yellow-100 p-2 rounded shadow">
            <p>{annotation.comment.text}</p>
            <small>{annotation.comment.author} - {annotation.comment.createdAt}</small>
        </div>
    );
};
```

#### 任务 3.2：图形批注（Circle/Square Annotation）
```typescript
interface ShapeAnnotation extends AnnotationData {
    style: {
        type: 'circle' | 'square' | 'arrow';
        strokeColor: string;
        fillColor: string;
        strokeWidth: number;
    };
    pdfCoordinates: {
        pageNumber: number;
        rect: { x: number; y: number; width: number; height: number };
    };
}

// Canvas 渲染
function renderShape(shape: ShapeAnnotation, ctx: CanvasRenderingContext2D, viewport: PageViewport) {
    const [x, y] = viewport.convertToViewportPoint(shape.pdfCoordinates.rect.x, shape.pdfCoordinates.rect.y);
    const [x2, y2] = viewport.convertToViewportPoint(
        shape.pdfCoordinates.rect.x + shape.pdfCoordinates.rect.width,
        shape.pdfCoordinates.rect.y + shape.pdfCoordinates.rect.height
    );
    
    if (shape.style.type === 'circle') {
        const centerX = (x + x2) / 2;
        const centerY = (y + y2) / 2;
        const radius = Math.abs(x2 - x) / 2;
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
        ctx.strokeStyle = shape.style.strokeColor;
        ctx.lineWidth = shape.style.strokeWidth;
        ctx.stroke();
    } else if (shape.style.type === 'square') {
        ctx.strokeRect(x, y, x2 - x, y2 - y);
    }
}
```

#### 任务 3.3：自由绘制（Ink Annotation）
```typescript
interface InkAnnotation extends AnnotationData {
    style: {
        type: 'ink';
        strokeColor: string;
        strokeWidth: number;
    };
    pdfCoordinates: {
        pageNumber: number;
        // 路径数组（支持多条路径）
        paths: Array<Array<{ x: number; y: number }>>;
    };
}

// 绘制工具实现
const InkTool: React.FC = () => {
    const [isDrawing, setIsDrawing] = useState(false);
    const [currentPath, setCurrentPath] = useState<{x: number; y: number}[]>([]);
    
    const handleMouseDown = (e: React.MouseEvent) => {
        setIsDrawing(true);
        const point = getMousePosition(e);
        setCurrentPath([point]);
    };
    
    const handleMouseMove = (e: React.MouseEvent) => {
        if (!isDrawing) return;
        const point = getMousePosition(e);
        setCurrentPath(prev => [...prev, point]);
    };
    
    const handleMouseUp = async () => {
        setIsDrawing(false);
        
        // 转换为 PDF 坐标
        const pdfPath = await convertPathToPdfCoords(currentPath, pdfPage);
        
        // 创建标注
        const annotation: InkAnnotation = {
            id: uuidv4(),
            documentId,
            style: { type: 'ink', strokeColor: '#FF0000', strokeWidth: 2 },
            pdfCoordinates: { pageNumber, paths: [pdfPath] }
        };
        
        await api.createAnnotation(annotation);
        setCurrentPath([]);
    };
    
    return (
        <canvas
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
        />
    );
};
```

### Phase 4：后端集成（1-2天）

#### 任务 4.1：数据库模型
```python
# backend/app/models/db/models_simple.py
class AnnotationModel(Base):
    __tablename__ = "annotations"
    
    id = Column(String(36), primary_key=True)
    document_id = Column(String(36), ForeignKey("documents.id"))
    
    # 文本锚点
    selected_text = Column(Text)
    prefix = Column(String(100))
    suffix = Column(String(100))
    page_number = Column(Integer)
    start_offset = Column(Integer)
    end_offset = Column(Integer)
    text_hash = Column(String(64))
    
    # PDF 坐标（JSON 存储）
    quad_points = Column(JSON)  # Array of QuadPoint
    rotation = Column(Integer, default=0)
    page_width = Column(Float)
    page_height = Column(Float)
    
    # 样式
    style_type = Column(String(20))  # highlight, underline, etc.
    style_color = Column(String(7))
    style_opacity = Column(Float, default=0.45)
    style_stroke_width = Column(Float, nullable=True)
    
    # 批注内容（可选）
    comment_text = Column(Text, nullable=True)
    comment_author = Column(String(100), nullable=True)
    
    # 元数据
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    user_id = Column(String(36))
```

#### 任务 4.2：API 端点
```python
# backend/app/api/v1/endpoints/annotations.py
@router.post("/documents/{document_id}/annotations")
async def create_annotation(
    document_id: str,
    annotation: AnnotationCreate,
    db: AsyncSession = Depends(get_db)
):
    # 创建标注
    ...

@router.get("/documents/{document_id}/annotations")
async def get_annotations(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    # 获取文档的所有标注
    ...

@router.patch("/annotations/{annotation_id}")
async def update_annotation(
    annotation_id: str,
    update: AnnotationUpdate,
    db: AsyncSession = Depends(get_db)
):
    # 更新标注
    ...

@router.delete("/annotations/{annotation_id}")
async def delete_annotation(
    annotation_id: str,
    db: AsyncSession = Depends(get_db)
):
    # 删除标注
    ...
```

#### 任务 4.3：导出为标准 PDF 标注（FDF/XFDF）
```python
# backend/app/services/pdf/annotation_export.py
def export_annotations_to_xfdf(document_id: str) -> str:
    """导出标注为 XFDF 格式（XML FDF）"""
    annotations = get_annotations(document_id)
    
    xfdf = f"""<?xml version="1.0" encoding="UTF-8"?>
    <xfdf xmlns="http://ns.adobe.com/xfdf/" xml:space="preserve">
        <annots>
    """
    
    for ann in annotations:
        if ann.style_type == 'highlight':
            xfdf += f"""
            <highlight page="{ann.page_number}" 
                       color="{ann.style_color}" 
                       opacity="{ann.style_opacity}"
                       coords="{format_quad_points(ann.quad_points)}">
                <contents>{ann.selected_text}</contents>
            </highlight>
            """
    
    xfdf += """
        </annots>
    </xfdf>
    """
    
    return xfdf
```

### Phase 5：性能优化（持续）

#### 优化 5.1：虚拟化渲染
```typescript
// 只渲染可见页面的标注
const visibleAnnotations = useMemo(() => {
    return annotations.filter(a => 
        a.pdfCoordinates.pageNumber >= firstVisiblePage &&
        a.pdfCoordinates.pageNumber <= lastVisiblePage
    );
}, [annotations, firstVisiblePage, lastVisiblePage]);
```

#### 优化 5.2：Canvas 离屏渲染
```typescript
// 使用 OffscreenCanvas 在 Worker 中渲染
const worker = new Worker('annotationRenderer.worker.js');
worker.postMessage({
    type: 'render',
    annotations: visibleAnnotations,
    viewport: { width, height, scale }
});
```

#### 优化 5.3：WebWorker 文本提取
```typescript
// 在 Worker 中处理文本提取和锚点创建
const textWorker = new Worker('textAnchor.worker.js');
textWorker.postMessage({
    type: 'createAnchor',
    selection: { startOffset, endOffset },
    pageText: pageTextContent
});
```

---

## 📊 对比：旧方案 vs 新方案

| 特性 | 旧方案 | 新方案 |
|------|--------|--------|
| **坐标系统** | ❌ 屏幕坐标 | ✅ PDF 原生坐标 |
| **缩放适应** | ❌ 失效 | ✅ 自动适应 |
| **跨设备同步** | ❌ 不支持 | ✅ 完美同步 |
| **文本锚定** | ❌ 无 | ✅ 三层定位 |
| **PDF 标准** | ❌ 不兼容 | ✅ 符合 ISO 32000 |
| **跨行选择** | ❌ 单矩形 | ✅ QuadPoints 数组 |
| **批注功能** | ❌ 无 | ✅ 文字/图形/画笔 |
| **导出兼容** | ❌ 不支持 | ✅ XFDF 格式 |
| **性能** | ⚠️ DOM 渲染 | ✅ Canvas 硬件加速 |

---

## 🎯 最终效果

### 用户体验
1. ✅ **位置精确**：缩放、滚动、旋转都不影响标注位置
2. ✅ **跨设备同步**：在手机/平板/电脑上位置一致
3. ✅ **文档更新容错**：PDF 轻微变化时仍能定位
4. ✅ **流畅交互**：拖拽、编辑、删除都很流畅
5. ✅ **标准兼容**：可导出为标准 PDF 标注

### 开发者体验
1. ✅ **架构清晰**：文本锚点、PDF 坐标、渲染分离
2. ✅ **易于扩展**：添加新标注类型简单
3. ✅ **可测试**：每个服务可独立测试
4. ✅ **高性能**：Canvas + Worker 充分利用硬件

---

## 📚 参考资料

1. **PDF 规范**
   - [ISO 32000-2:2020 (PDF 2.0)](https://www.iso.org/standard/75839.html)
   - [Adobe PDF Reference 1.7](https://opensource.adobe.com/dc-acrobat-sdk-docs/pdfstandards/PDF32000_2008.pdf)

2. **PDF.js 文档**
   - [PDF.js Annotation API](https://mozilla.github.io/pdf.js/api/draft/)
   - [Text Layer Implementation](https://github.com/mozilla/pdf.js/wiki/Frequently-Asked-Questions#text-layer)

3. **W3C 标准**
   - [Web Annotations Data Model](https://www.w3.org/TR/annotation-model/)
   - [Selection API](https://w3c.github.io/selection-api/)

4. **开源项目参考**
   - [PDF Annotator](https://github.com/agentcooper/react-pdf-annotator)
   - [Hypothesis (Web Annotation)](https://github.com/hypothesis/h)
   - [Apache PDFBox Annotations](https://pdfbox.apache.org/)

---

## ✅ 下一步行动

1. **立即开始**：Phase 1 基础架构实现
2. **并行进行**：前端和后端同时开发
3. **持续测试**：每个 Phase 完成后进行测试
4. **迭代优化**：根据测试反馈优化性能

---

**文档创建时间**：2025-10-08 19:00  
**预计完成时间**：7-10 天  
**核心优势**：行业标准 + 高性能 + 易扩展
