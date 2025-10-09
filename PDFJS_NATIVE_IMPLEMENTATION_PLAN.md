# PDF.js 原生标注系统实施方案

## 目标
完全移除自定义标注代码，100% 使用 PDF.js 原生 API 实现标注功能。

## 功能对比

### 原有功能 → PDF.js 映射

| 原有功能 | 实现方式 | PDF.js 对应 | 保留 |
|---------|---------|-------------|------|
| 矩形标注 | Canvas | ❌ 不支持 | **放弃** |
| 圆形标注 | Canvas | ❌ 不支持 | **放弃** |
| 箭头标注 | Canvas | ❌ 不支持 | **放弃** |
| 手绘/画笔 | Canvas | ✅ Ink Annotation | **保留** |
| 高亮文本 | Canvas | ✅ Highlight (实验性) | **保留** |
| 下划线 | Canvas | ✅ Underline | **保留** |
| 删除线 | Canvas | ✅ StrikeOut | **保留** |
| 便笺 | 自定义 | ✅ FreeText | **保留** |
| 拖拽移动 | 自定义 | ✅ 内置支持 | **保留** |
| 调整大小 | 自定义 | ✅ 内置支持 | **保留** |
| 撤销/重做 | HistoryManager | ✅ 内置支持 | **保留** |

## 架构设计

### 1. 核心组件架构

```
┌────────────────────────────────────────┐
│ PDFViewerSimplified.tsx               │  简化的 PDF 查看器
│  ├─ PDF.js Page Component             │
│  ├─ TextLayer (文本选择)              │
│  ├─ AnnotationLayer (显示已有标注)    │
│  └─ AnnotationEditorLayer (编辑标注) │  ⭐ 核心
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│ AnnotationToolbar.tsx (简化版)        │  工具栏
│  ├─ Ink Tool (画笔)                   │
│  ├─ FreeText Tool (文本框)            │
│  ├─ Highlight Tool (高亮)             │
│  └─ Eraser Tool (删除)                │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│ Backend API (简化版)                  │
│  └─ AnnotationStorage 格式存储         │  直接存储 PDF.js 数据
└────────────────────────────────────────┘
```

### 2. 数据流

```
用户操作
    ↓
PDF.js AnnotationEditorLayer (创建/编辑标注)
    ↓
annotationeditorstateschanged 事件
    ↓
提取 pdfDocument.annotationStorage.serializable
    ↓
发送到后端 API
    ↓
保存到数据库（JSON 格式）
    ↓
下次加载时恢复到 AnnotationStorage
```

## 详细实施步骤

### Phase 1: 启用 PDF.js 编辑模式

#### 1.1 修改 react-pdf 配置

```tsx
// PDFViewerSimplified.tsx
import { Document, Page } from 'react-pdf';
import * as pdfjsLib from 'pdfjs-dist';

const [annotationEditorMode, setAnnotationEditorMode] = useState(0);
// 0 = None, 3 = Ink, 13 = FreeText, 15 = Stamp

<Document
    file={pdfUrl}
    onLoadSuccess={onDocumentLoadSuccess}
    options={{
        // 启用标注编辑
        enableAnnotationEditorLayer: true,
    }}
>
    <Page
        pageNumber={pageNumber}
        scale={scale}
        renderTextLayer={true}
        renderAnnotationLayer={true}
        // ⭐ 关键：设置编辑模式
        annotationEditorMode={annotationEditorMode}
    />
</Document>
```

#### 1.2 监听标注变化事件

```tsx
useEffect(() => {
    if (!pdfDocument) return;

    const handleAnnotationChange = (event: any) => {
        console.log('Annotation changed:', event);
        
        // 获取所有标注数据
        const storage = pdfDocument.annotationStorage;
        const annotations = storage.serializable;
        
        // 保存到后端
        saveAnnotations(annotations);
    };

    // 监听事件
    pdfDocument.addEventListener(
        'annotationeditorstateschanged',
        handleAnnotationChange
    );

    return () => {
        pdfDocument.removeEventListener(
            'annotationeditorstateschanged',
            handleAnnotationChange
        );
    };
}, [pdfDocument]);
```

### Phase 2: 工具栏实现

```tsx
// components/PDFAnnotationToolbar.tsx
export const PDFAnnotationToolbar = ({ 
    onModeChange 
}: { 
    onModeChange: (mode: number) => void 
}) => {
    return (
        <div className="fixed left-4 top-24 z-50 bg-white rounded-lg shadow-xl p-2">
            {/* 选择工具 */}
            <button onClick={() => onModeChange(0)}>
                <FiMousePointer /> 选择
            </button>

            {/* 画笔工具 */}
            <button onClick={() => onModeChange(3)}>
                <FiEdit3 /> 画笔
            </button>

            {/* 文本框工具 */}
            <button onClick={() => onModeChange(13)}>
                <FiType /> 文本
            </button>

            {/* 高亮工具 */}
            <button onClick={() => onModeChange(9)}>
                <FiHighlight /> 高亮
            </button>
        </div>
    );
};
```

### Phase 3: 文本高亮实现

PDF.js 3.0+ 支持文本高亮，但需要特殊处理：

```tsx
// 监听文本选择
useEffect(() => {
    const handleTextSelection = () => {
        const selection = window.getSelection();
        if (!selection || selection.isCollapsed) return;

        const range = selection.getRangeAt(0);
        
        // 使用 PDF.js 的 TextLayer API
        const textLayer = document.querySelector('.textLayer');
        if (!textLayer) return;

        // 创建高亮标注
        // PDF.js 会自动处理坐标转换
        createHighlight(range);
    };

    document.addEventListener('mouseup', handleTextSelection);
    return () => document.removeEventListener('mouseup', handleTextSelection);
}, []);
```

### Phase 4: 后端 API 适配

#### 4.1 修改数据模型

```python
# backend/app/models/db/models_simple.py
class AnnotationModel(Base):
    __tablename__ = "annotations"
    
    id = Column(String(36), primary_key=True)
    document_id = Column(String(36), ForeignKey("documents.id"))
    page_number = Column(Integer)
    
    # ⭐ 直接存储 PDF.js serializable 数据（JSON）
    pdfjs_data = Column(JSON, nullable=False)
    
    # 元数据
    annotation_type = Column(String(50))  # ink, freetext, highlight
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
```

#### 4.2 API 端点

```python
# backend/app/api/v1/endpoints/annotations.py
@router.post("/annotations/batch")
async def save_annotations_batch(
    annotations: List[Dict[str, Any]],
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """批量保存 PDF.js 标注数据"""
    for ann_data in annotations:
        annotation = AnnotationModel(
            id=str(uuid.uuid4()),
            document_id=document_id,
            page_number=ann_data.get('pageIndex', 0) + 1,
            pdfjs_data=ann_data,  # 直接存储
            annotation_type=ann_data.get('annotationType', 'unknown')
        )
        db.add(annotation)
    
    await db.commit()
    return {"status": "success"}

@router.get("/annotations/{document_id}")
async def get_annotations(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取文档的所有标注"""
    result = await db.execute(
        select(AnnotationModel)
        .where(AnnotationModel.document_id == document_id)
    )
    annotations = result.scalars().all()
    
    # 返回 PDF.js 格式
    return {
        "annotations": [ann.pdfjs_data for ann in annotations]
    }
```

### Phase 5: 恢复标注到 PDF

```tsx
// 加载文档时恢复标注
const loadAnnotations = async (documentId: string) => {
    const response = await apiService.getAnnotations(documentId);
    const annotations = response.annotations;

    if (!pdfDocument) return;

    // 恢复到 AnnotationStorage
    const storage = pdfDocument.annotationStorage;
    
    annotations.forEach((ann: any) => {
        // PDF.js 会根据数据自动渲染
        storage.setValue(ann.id, ann);
    });

    // 触发重新渲染
    // PDF.js 会自动显示标注
};
```

## 要删除的文件（约 1500 行）

```
frontend/src/components/annotation/
├── AnnotationCanvas.tsx          ❌ 删除 (300+ 行)
├── DraggableAnnotation.tsx       ❌ 删除 (400+ 行)
├── ShapeTool.tsx                 ❌ 删除 (280+ 行)
├── NoteTool.tsx                  ❌ 删除 (280+ 行)
└── AnnotationToolbar.tsx         🔄 简化 (保留 50 行)

frontend/src/utils/
├── annotation.ts                 🔄 简化 (只保留格式转换)
└── pdfCoordinateService.ts      ❌ 删除 (PDF.js 内置)

frontend/src/services/
└── HistoryManager.ts             ❌ 删除 (PDF.js 内置撤销/重做)
```

## 要创建的新文件

```
frontend/src/components/
├── PDFViewerSimplified.tsx       🆕 简化版 PDF 查看器 (200 行)
├── PDFAnnotationToolbar.tsx      🆕 简化版工具栏 (100 行)
└── PDFAnnotationManager.tsx      🆕 标注管理器 (150 行)

frontend/src/hooks/
└── usePDFAnnotations.ts          🆕 标注 Hook (100 行)
```

## 预期代码量变化

- **删除**: ~1500 行自定义代码
- **新增**: ~550 行 PDF.js 集成代码
- **净减少**: ~950 行代码 ✅

## 工作量评估

### 时间线（7 天）

**Day 1-2**: 研究 PDF.js API + 删除旧代码
- 阅读 PDF.js 文档
- 删除自定义标注组件
- 创建新的简化版查看器

**Day 3-4**: 实现核心功能
- 配置 AnnotationEditorLayer
- 实现工具栏切换
- 实现数据保存/加载

**Day 5**: 文本高亮
- 研究 TextLayer API
- 实现高亮选择逻辑

**Day 6**: 后端适配
- 修改数据模型
- 更新 API 端点
- 数据迁移脚本

**Day 7**: 测试和文档
- 端到端测试
- 编写使用文档

## 优势总结

✅ **代码量减少 60%** - 从 2500 行降到 1000 行  
✅ **标准化** - 符合 PDF 规范  
✅ **维护成本低** - 依赖成熟库  
✅ **内置功能** - 撤销/重做、拖拽、调整大小  
✅ **兼容性好** - 可被其他 PDF 阅读器识别  

## 劣势和权衡

❌ **失去几何图形** - 矩形、圆形、箭头  
❌ **UI 定制受限** - 使用 PDF.js 默认样式  
❌ **功能简化** - 只保留标准 PDF 标注  

---

## 下一步行动

立即开始实施：

1. ✅ 创建 `PDFViewerSimplified.tsx`
2. ✅ 配置 AnnotationEditorLayer
3. ✅ 实现基础工具栏
4. ✅ 删除旧代码
5. ✅ 测试验证

**预计完成时间**: 7 天

准备开始了吗？🚀
