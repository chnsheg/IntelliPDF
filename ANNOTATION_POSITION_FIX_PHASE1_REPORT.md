# 标注位置修复 - Phase 1 完成报告

## 完成时间
2025-10-08 18:00

## 完成的工作

### 1. 添加 PDF 文档和页面引用
✅ 添加 `pdfDocumentRef` 用于保存 PDFDocumentProxy
✅ 添加 `pdfPagesCache` 用于缓存 PDFPageProxy 对象
✅ 修改 `onDocumentLoadSuccess` 保存文档引用

### 2. 实现坐标转换函数

#### getPDFPage 函数
```typescript
const getPDFPage = useCallback(async (pageNum: number) => {
    // 检查缓存
    if (pdfPagesCache.current.has(pageNum)) {
        return pdfPagesCache.current.get(pageNum);
    }
    
    // 加载页面
    if (pdfDocumentRef.current) {
        const page = await pdfDocumentRef.current.getPage(pageNum);
        pdfPagesCache.current.set(pageNum, page);
        return page;
    }
    return null;
}, []);
```

#### convertScreenToPDF 函数
```typescript
const convertScreenToPDF = useCallback(async (
    rect: DOMRect,
    pageElement: HTMLElement,
    pageNum: number
): Promise<{ x: number; y: number; width: number; height: number } | null> => {
    const pdfPage = await getPDFPage(pageNum);
    if (!pdfPage) return null;

    const viewport = pdfPage.getViewport({ scale });
    const pageRect = pageElement.getBoundingClientRect();

    // 计算相对于页面元素的坐标
    const relX = rect.left - pageRect.left;
    const relY = rect.top - pageRect.top;
    const relX2 = rect.right - pageRect.left;
    const relY2 = rect.bottom - pageRect.top;

    // 使用 viewport 转换为 PDF 坐标
    const [pdfX, pdfY] = viewport.convertToPdfPoint(relX, relY);
    const [pdfX2, pdfY2] = viewport.convertToPdfPoint(relX2, relY2);

    return {
        x: Math.min(pdfX, pdfX2),
        y: Math.min(pdfY, pdfY2),
        width: Math.abs(pdfX2 - pdfX),
        height: Math.abs(pdfY2 - pdfY),
    };
}, [scale, getPDFPage]);
```

#### convertPDFToScreen 函数
```typescript
const convertPDFToScreen = useCallback(async (
    pdfCoords: { x: number; y: number; width: number; height: number },
    pageNum: number
): Promise<{ left: number; top: number; width: number; height: number } | null> => {
    const pdfPage = await getPDFPage(pageNum);
    if (!pdfPage) return null;

    const viewport = pdfPage.getViewport({ scale });

    // 转换 PDF 坐标为视口坐标
    const [x1, y1] = viewport.convertToViewportPoint(pdfCoords.x, pdfCoords.y);
    const [x2, y2] = viewport.convertToViewportPoint(
        pdfCoords.x + pdfCoords.width,
        pdfCoords.y + pdfCoords.height
    );

    return {
        left: Math.min(x1, x2),
        top: Math.min(y1, y2),
        width: Math.abs(x2 - x1),
        height: Math.abs(y2 - y1),
    };
}, [scale, getPDFPage]);
```

### 3. 修改文本选择处理

✅ 修改 `handleSelection` 为异步函数
✅ 使用 `convertScreenToPDF` 转换选区坐标
✅ 添加降级方案（PDF 转换失败时使用相对坐标）
✅ 分离工具栏定位坐标和标注坐标：
   - 标注使用 PDF 坐标（x, y, width, height）
   - 工具栏使用屏幕坐标（toolbarX, toolbarY）

### 4. 更新类型定义

✅ 扩展 `selectionInfo` 类型，添加：
   - `toolbarX?: number` - 工具栏屏幕 X 坐标
   - `toolbarY?: number` - 工具栏屏幕 Y 坐标

## 技术实现细节

### 坐标系统理解

**PDF 坐标系统**：
- 原点：页面左下角
- X 轴：向右为正
- Y 轴：向上为正
- 单位：PDF points (1/72 inch)

**浏览器坐标系统**：
- 原点：页面左上角  
- X 轴：向右为正
- Y 轴：向下为正
- 单位：CSS pixels

**关键转换**：
```
PDF.js 的 viewport 对象提供了两个关键方法：
1. convertToPdfPoint(x, y) - 浏览器坐标 → PDF 坐标
2. convertToViewportPoint(x, y) - PDF 坐标 → 浏览器坐标
```

### 缩放处理

`viewport.getViewport({ scale })` 自动处理缩放：
- scale = 1.0 表示100%
- scale = 1.5 表示150%
- viewport 的转换方法自动应用缩放因子

### Y 轴翻转

PDF.js 的 `convertToPdfPoint` 和 `convertToViewportPoint` 自动处理 Y 轴翻转，无需手动计算。

## 待完成工作

### Phase 1 剩余任务
- [ ] 修改标注渲染使用 `convertPDFToScreen`
- [ ] 测试基础坐标转换功能
- [ ] 验证不同缩放级别下的准确性

### Phase 2 任务
- [ ] 处理页面加载顺序问题
- [ ] 优化坐标转换性能
- [ ] 添加错误处理和日志

### Phase 3 任务
- [ ] 支持页面旋转
- [ ] 支持跨页选择
- [ ] 持久化标注时的坐标格式

## 已知问题

### 1. 工具栏定位
当前工具栏仍使用屏幕坐标定位，这是正确的。但标注渲染需要从 PDF 坐标转换回屏幕坐标。

### 2. 现有标注
代码中标注直接使用 `a.x, a.y` 定位：
```tsx
<div style={{ left: a.x, top: a.y, width: a.width, height: a.height }} />
```

这需要修改为：
```tsx
<AnnotationOverlay annotation={a} scale={scale} pageNum={pageNum} />
```

### 3. 异步转换
坐标转换是异步的（需要加载 PDF 页面），渲染逻辑需要适应异步模式。

## 下一步行动

### 立即（今晚）
1. 创建 Git 提交保存当前进度
2. 实现标注渲染组件使用 `convertPDFToScreen`
3. 进行基础测试

### 明天
1. 完成 Phase 1 所有任务
2. 开始 Phase 2
3. 编写详细测试用例

## 测试计划（Phase 1）

### 手动测试
1. **100% 缩放**
   - 选中文本
   - 创建高亮标注
   - 验证位置准确

2. **150% 缩放**
   - 重复上述测试
   - 验证标注位置随缩放正确调整

3. **50% 缩放**
   - 重复上述测试

4. **切换页面**
   - 在不同页面创建标注
   - 验证每个标注在正确的页面显示

### 自动化测试（后续）
```typescript
describe('Coordinate Conversion', () => {
    it('should convert screen to PDF coordinates correctly', async () => {
        const screenRect = new DOMRect(100, 100, 200, 50);
        const pdfCoords = await convertScreenToPDF(screenRect, pageElement, 1);
        expect(pdfCoords).toBeDefined();
        expect(pdfCoords.x).toBeGreaterThan(0);
        expect(pdfCoords.y).toBeGreaterThan(0);
    });
    
    it('should convert PDF to screen coordinates correctly', async () => {
        const pdfCoords = { x: 100, y: 200, width: 200, height: 50 };
        const screenCoords = await convertPDFToScreen(pdfCoords, 1);
        expect(screenCoords).toBeDefined();
        expect(screenCoords.left).toBeGreaterThan(0);
        expect(screenCoords.top).toBeGreaterThan(0);
    });
});
```

## 性能考虑

### 缓存策略
✅ 已实现 `pdfPagesCache` 缓存 PDF 页面对象
- 避免重复加载同一页面
- 提升坐标转换速度

### 优化机会
- [ ] 预加载常见页面（当前页 ±2）
- [ ] 使用 Web Worker 进行坐标转换（如果成为瓶颈）
- [ ] 标注批量转换（避免逐个转换）

## 总结

### ✅ 完成
- 核心坐标转换函数实现
- PDF 页面引用管理
- 文本选择坐标转换

### ⏳ 进行中
- 标注渲染坐标转换

### 📝 待办
- 完整测试验证
- 性能优化
- 错误处理

**预计完成时间**：Phase 1 - 明天中午前

---

**报告生成时间**：2025-10-08 18:00  
**状态**：Phase 1 部分完成，代码已实现但未完全集成  
**下一步**：实现标注渲染组件并测试
