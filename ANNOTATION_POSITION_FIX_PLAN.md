# 标注位置修复计划

## 问题分析

### 当前问题
用户反馈："所有在pdf编辑的内容，例如高亮、下划线这些绘制的位置都不对"

### 根本原因
**坐标系统不匹配**

当前代码中，`handleSelection` 函数计算坐标的方式：
```typescript
const rect = range.getBoundingClientRect();  // 浏览器视口坐标
const containerRect = containerRef.current?.getBoundingClientRect();  // 容器坐标
const position = {
    x: rect.left - containerRect.left,  // ❌ 相对于容器的坐标
    y: rect.top - containerRect.top,    // ❌ 相对于容器的坐标
    width: rect.width,
    height: rect.height,
};
```

**问题**：
1. 这些坐标是相对于**浏览器容器**的，不是相对于 **PDF 页面**的
2. 没有考虑 PDF 页面的缩放（scale）
3. 没有考虑滚动偏移
4. 没有考虑页面旋转
5. PDF.js 内部使用的是 PDF 页面坐标系统（原点在左下角，Y轴向上）

### PDF 坐标系统 vs 浏览器坐标系统

**PDF 坐标系统**（PDF.js 内部）：
- 原点：页面**左下角**
- X轴：向右为正
- Y轴：**向上为正**
- 单位：PDF points (1/72 inch)
- 不受浏览器缩放影响

**浏览器坐标系统**：
- 原点：页面**左上角**
- X轴：向右为正
- Y轴：**向下为正**
- 单位：CSS pixels
- 受浏览器缩放、滚动影响

## 解决方案

### 方案一：使用 PDF.js 的 TextLayer（推荐）

**优点**：
- PDF.js 已经提供了文本层和坐标转换
- 更准确，因为使用的是 PDF 原生坐标
- 自动处理缩放和旋转

**实现步骤**：
1. 监听文本选择事件
2. 使用 PDF.js 的 `getTextContent()` 获取文本项
3. 从文本项中提取 PDF 坐标
4. 将 PDF 坐标转换为渲染坐标

**核心代码**：
```typescript
// 获取页面的 PDF 页面对象
const pdfPage = await pdfDocument.getPage(pageNumber);

// 获取文本内容
const textContent = await pdfPage.getTextContent();

// 获取视口（包含缩放和旋转）
const viewport = pdfPage.getViewport({ scale });

// 将选区映射到 PDF 文本项
const selectedItems = findTextItemsInRange(textContent.items, selectedText);

// 获取边界框（PDF 坐标）
const pdfBounds = calculateBoundingBox(selectedItems);

// 转换为渲染坐标
const [x, y, width, height] = viewport.convertToViewportRectangle([
    pdfBounds.x0, pdfBounds.y0, pdfBounds.x1, pdfBounds.y1
]);
```

### 方案二：手动坐标转换

**适用场景**：无法访问 PDF.js 内部 API 时

**转换公式**：
```typescript
function convertScreenToPDF(
    screenX: number,
    screenY: number,
    pageElement: HTMLElement,
    scale: number,
    pageHeight: number  // PDF 页面高度（points）
) {
    const pageRect = pageElement.getBoundingClientRect();
    
    // 1. 相对于页面元素的坐标
    const relativeX = screenX - pageRect.left;
    const relativeY = screenY - pageRect.top;
    
    // 2. 考虑缩放，转换为 PDF points
    const pdfX = relativeX / scale;
    const pdfY = relativeY / scale;
    
    // 3. Y轴翻转（浏览器向下，PDF向上）
    const pdfYFlipped = pageHeight - pdfY;
    
    return { x: pdfX, y: pdfYFlipped };
}

function convertPDFToScreen(
    pdfX: number,
    pdfY: number,
    pageElement: HTMLElement,
    scale: number,
    pageHeight: number
) {
    const pageRect = pageElement.getBoundingClientRect();
    
    // 1. Y轴翻转
    const browserY = pageHeight - pdfY;
    
    // 2. 应用缩放
    const scaledX = pdfX * scale;
    const scaledY = browserY * scale;
    
    // 3. 加上页面偏移
    const screenX = scaledX + pageRect.left;
    const screenY = scaledY + pageRect.top;
    
    return { x: screenX, y: screenY };
}
```

### 方案三：使用 react-pdf 的内置功能

`react-pdf` 提供了 `onGetTextSuccess` 回调，可以访问文本层信息。

```typescript
<Page
    pageNumber={pageNumber}
    scale={scale}
    onGetTextSuccess={(textContent) => {
        // textContent 包含所有文本项及其坐标
        console.log(textContent);
    }}
/>
```

## 推荐实现方案

**混合方案**：使用 PDF.js API + 手动转换

### 实现步骤

#### 1. 获取 PDF 页面信息
```typescript
const [pdfDocument, setPdfDocument] = useState<PDFDocumentProxy | null>(null);
const [pdfPages, setPdfPages] = useState<Map<number, PDFPageProxy>>(new Map());

// 在 onLoadSuccess 中保存文档引用
const onDocumentLoadSuccess = useCallback(({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
    // 保存文档引用以供后续使用
    // 注意：react-pdf 不直接暴露 PDFDocumentProxy，需要通过其他方式获取
}, []);
```

#### 2. 改进 handleSelection 函数
```typescript
const handleSelection = async () => {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed) return;

    const selectedText = selection.toString().trim();
    if (selectedText.length < 3) return;

    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();

    // 获取页面元素
    const pageElement = pageRefs.current.get(pageNumber);
    if (!pageElement) return;

    // 获取 PDF 页面信息
    const pdfPage = pdfPages.get(pageNumber);
    if (!pdfPage) {
        console.warn('PDF page not loaded');
        // 降级方案：使用相对坐标
        useRelativeCoordinates(rect, pageElement);
        return;
    }

    // 转换为 PDF 坐标
    const pdfCoords = await convertScreenToPDFCoords(
        rect,
        pageElement,
        pdfPage,
        scale
    );

    setSelectionInfo({
        visible: true,
        pageNumber: pageNumber,
        ...pdfCoords,
        text: selectedText,
    });
};
```

#### 3. 实现坐标转换函数
```typescript
async function convertScreenToPDFCoords(
    rect: DOMRect,
    pageElement: HTMLElement,
    pdfPage: PDFPageProxy,
    scale: number
) {
    const pageRect = pageElement.getBoundingClientRect();
    const viewport = pdfPage.getViewport({ scale });
    
    // 相对于页面的坐标
    const relX = rect.left - pageRect.left;
    const relY = rect.top - pageRect.top;
    
    // 转换为 PDF 坐标（使用 viewport 的逆变换）
    const pdfPoint = viewport.convertToPdfPoint(relX, relY);
    const pdfPoint2 = viewport.convertToPdfPoint(
        relX + rect.width,
        relY + rect.height
    );
    
    return {
        x: Math.min(pdfPoint[0], pdfPoint2[0]),
        y: Math.min(pdfPoint[1], pdfPoint2[1]),
        width: Math.abs(pdfPoint2[0] - pdfPoint[0]),
        height: Math.abs(pdfPoint2[1] - pdfPoint[1]),
    };
}
```

#### 4. 渲染标注时转换回屏幕坐标
```typescript
function renderAnnotation(anno) {
    const pdfPage = pdfPages.get(anno.page);
    if (!pdfPage) return null;
    
    const viewport = pdfPage.getViewport({ scale });
    
    // PDF 坐标转换为视口坐标
    const [x1, y1] = viewport.convertToViewportPoint(anno.x, anno.y);
    const [x2, y2] = viewport.convertToViewportPoint(
        anno.x + anno.width,
        anno.y + anno.height
    );
    
    return {
        left: Math.min(x1, x2),
        top: Math.min(y1, y2),
        width: Math.abs(x2 - x1),
        height: Math.abs(y2 - y1),
    };
}
```

## 测试计划

### 测试场景
1. **缩放测试**
   - 50% 缩放
   - 100% 缩放（默认）
   - 150% 缩放
   - 200% 缩放

2. **滚动测试**
   - 页面顶部
   - 页面中部
   - 页面底部
   - 跨页选择

3. **旋转测试**（如果支持）
   - 0° (默认)
   - 90°
   - 180°
   - 270°

4. **多页测试**
   - 第一页
   - 中间页
   - 最后一页

5. **边界情况**
   - 非常短的选择（1-2个字符）
   - 长文本选择（跨多行）
   - 页面边缘的选择

### 预期结果
- ✅ 标注位置准确覆盖选中文本
- ✅ 缩放后位置保持正确
- ✅ 滚动后重新渲染位置正确
- ✅ 刷新页面后从后端加载的标注位置正确

## 实现优先级

### Phase 1：基础坐标转换（本次迭代）
- [ ] 实现 convertScreenToPDFCoords 函数
- [ ] 实现 convertPDFToScreenCoords 函数
- [ ] 修改 handleSelection 使用新坐标
- [ ] 修改标注渲染使用转换后的坐标

### Phase 2：PDF.js 集成
- [ ] 获取 PDFDocumentProxy 引用
- [ ] 缓存 PDFPageProxy 对象
- [ ] 使用 viewport.convertToPdfPoint
- [ ] 使用 viewport.convertToViewportPoint

### Phase 3：完善和优化
- [ ] 处理页面旋转
- [ ] 处理跨页选择
- [ ] 性能优化（坐标转换缓存）
- [ ] 错误处理和降级方案

### Phase 4：测试和验证
- [ ] 编写单元测试
- [ ] 手动测试所有场景
- [ ] 修复发现的问题
- [ ] 用户验收测试

## 技术难点

### 1. 访问 PDF.js 内部对象
`react-pdf` 封装了 PDF.js，不直接暴露 `PDFDocumentProxy`。

**解决方案**：
- 使用 `react-pdf` 的 ref 功能
- 或者使用原生 PDF.js API（绕过 react-pdf）

### 2. 坐标系统理解
PDF 坐标系统与浏览器坐标系统的差异。

**解决方案**：
- 详细阅读 PDF.js 文档
- 参考现有开源项目（如 PDF.js viewer）
- 逐步测试验证

### 3. 性能考虑
频繁的坐标转换可能影响性能。

**解决方案**：
- 使用 useMemo 缓存计算结果
- 按需加载 PDF 页面对象
- 虚拟化渲染（只渲染可见标注）

## 参考资源

### 官方文档
- [PDF.js Documentation](https://mozilla.github.io/pdf.js/)
- [react-pdf Documentation](https://github.com/wojtekmaj/react-pdf)

### 相关项目
- [PDF.js Viewer Source](https://github.com/mozilla/pdf.js/tree/master/web)
- [Hypothesis (PDF 标注工具)](https://github.com/hypothesis/client)
- [PDF Annotator](https://github.com/agentcooper/react-pdf-highlighter)

### 关键 API
- `PDFPageProxy.getViewport()`
- `PageViewport.convertToPdfPoint(x, y)`
- `PageViewport.convertToViewportPoint(x, y)`
- `PageViewport.convertToViewportRectangle([x1, y1, x2, y2])`

## 预期完成时间

- Phase 1：2-3 小时
- Phase 2：3-4 小时  
- Phase 3：2-3 小时
- Phase 4：2-3 小时

**总计**：9-13 小时

## 下一步行动

1. ✅ 创建本计划文档
2. ⏳ 研究 react-pdf 如何访问 PDF.js 内部对象
3. ⏳ 实现基础坐标转换函数（Phase 1）
4. ⏳ 测试验证修复效果
5. ⏳ 继续 Phase 2-4
