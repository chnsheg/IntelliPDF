# PDF 标注系统实现计划

## 📅 时间规划
**总工期**：7-10 天  
**开始时间**：2025-10-08  
**预计完成**：2025-10-18

---

## 🗓️ 详细时间表

### Day 1-2：Phase 1 基础架构

#### Day 1 上午：类型定义和数据模型
**文件**：`frontend/src/types/annotation.ts`

```typescript
// 创建完整的类型定义系统
export interface TextAnchor {
    selectedText: string;
    prefix: string;
    suffix: string;
    pageNumber: number;
    startOffset: number;
    endOffset: number;
    textHash: string;
}

export interface QuadPoint {
    x1: number; y1: number;  // 左下
    x2: number; y2: number;  // 右下
    x3: number; y3: number;  // 左上
    x4: number; y4: number;  // 右上
}

export interface PDFCoordinates {
    pageNumber: number;
    quadPoints: QuadPoint[];
    rotation: number;
    pageWidth: number;
    pageHeight: number;
}

export interface AnnotationStyle {
    type: 'highlight' | 'underline' | 'strikethrough' | 'text' | 'ink' | 'shape';
    color: string;
    opacity: number;
    strokeWidth?: number;
}

export interface AnnotationComment {
    text: string;
    author: string;
    createdAt: string;
    updatedAt: string;
}

export interface AnnotationData {
    id: string;
    documentId: string;
    textAnchor: TextAnchor;
    pdfCoordinates: PDFCoordinates;
    style: AnnotationStyle;
    comment?: AnnotationComment;
    metadata: {
        createdAt: string;
        updatedAt: string;
        userId: string;
    };
}
```

**验收标准**：
- ✅ 所有类型定义编译通过
- ✅ 符合 PDF 规范和 PDF.js API
- ✅ 支持所有标注类型

---

#### Day 1 下午：文本锚点服务
**文件**：`frontend/src/services/annotation/textAnchor.ts`

```typescript
import { sha256 } from 'crypto-hash';
import { PDFPageProxy } from 'pdfjs-dist';
import { TextAnchor } from '../../types/annotation';

export class TextAnchorService {
    /**
     * 创建文本锚点
     */
    async createTextAnchor(
        selection: Selection,
        pageNumber: number,
        pdfPage: PDFPageProxy
    ): Promise<TextAnchor> {
        // 1. 获取页面完整文本
        const textContent = await pdfPage.getTextContent();
        const pageText = textContent.items
            .map((item: any) => item.str)
            .join('');
        
        // 2. 获取选中文本
        const selectedText = selection.toString().trim();
        if (!selectedText) {
            throw new Error('No text selected');
        }
        
        // 3. 计算偏移量
        const startOffset = pageText.indexOf(selectedText);
        if (startOffset === -1) {
            throw new Error('Selected text not found in page');
        }
        const endOffset = startOffset + selectedText.length;
        
        // 4. 提取前后文
        const prefixStart = Math.max(0, startOffset - 50);
        const prefix = pageText.substring(prefixStart, startOffset);
        
        const suffixEnd = Math.min(pageText.length, endOffset + 50);
        const suffix = pageText.substring(endOffset, suffixEnd);
        
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
    
    /**
     * 重新定位标注（三种策略）
     */
    async relocateAnnotation(
        anchor: TextAnchor,
        pdfPage: PDFPageProxy
    ): Promise<{ startOffset: number; endOffset: number } | null> {
        // 获取当前页面文本
        const textContent = await pdfPage.getTextContent();
        const pageText = textContent.items
            .map((item: any) => item.str)
            .join('');
        
        // 策略1：精确匹配
        const exactIndex = pageText.indexOf(anchor.selectedText);
        if (exactIndex !== -1) {
            return {
                startOffset: exactIndex,
                endOffset: exactIndex + anchor.selectedText.length
            };
        }
        
        // 策略2：前后文匹配
        const contextPattern = this.escapeRegex(anchor.prefix) + 
                               '(.+?)' + 
                               this.escapeRegex(anchor.suffix);
        const contextMatch = pageText.match(new RegExp(contextPattern, 's'));
        if (contextMatch && contextMatch.index !== undefined) {
            const startOffset = contextMatch.index + anchor.prefix.length;
            return {
                startOffset,
                endOffset: startOffset + contextMatch[1].length
            };
        }
        
        // 策略3：模糊匹配（使用 Levenshtein 距离）
        const fuzzyMatch = this.findFuzzyMatch(
            pageText,
            anchor.selectedText,
            0.85  // 85% 相似度
        );
        if (fuzzyMatch) {
            return fuzzyMatch;
        }
        
        // 失败
        console.warn('Failed to relocate annotation:', {
            id: anchor.selectedText.substring(0, 20) + '...',
            pageNumber: anchor.pageNumber
        });
        return null;
    }
    
    /**
     * 模糊匹配算法
     */
    private findFuzzyMatch(
        haystack: string,
        needle: string,
        threshold: number
    ): { startOffset: number; endOffset: number } | null {
        const needleLen = needle.length;
        const windowSize = Math.floor(needleLen * 1.5);  // 允许 50% 长度差异
        
        let bestMatch = { score: 0, start: -1, end: -1 };
        
        for (let i = 0; i <= haystack.length - needleLen; i++) {
            const window = haystack.substring(i, i + windowSize);
            const similarity = this.calculateSimilarity(window, needle);
            
            if (similarity > bestMatch.score) {
                bestMatch = { score: similarity, start: i, end: i + needleLen };
            }
        }
        
        if (bestMatch.score >= threshold) {
            return {
                startOffset: bestMatch.start,
                endOffset: bestMatch.end
            };
        }
        
        return null;
    }
    
    /**
     * 计算相似度（Dice 系数）
     */
    private calculateSimilarity(str1: string, str2: string): number {
        const bigrams1 = this.getBigrams(str1);
        const bigrams2 = this.getBigrams(str2);
        
        const intersection = bigrams1.filter(b => bigrams2.includes(b)).length;
        const union = bigrams1.length + bigrams2.length;
        
        return (2 * intersection) / union;
    }
    
    private getBigrams(str: string): string[] {
        const bigrams: string[] = [];
        for (let i = 0; i < str.length - 1; i++) {
            bigrams.push(str.substring(i, i + 2));
        }
        return bigrams;
    }
    
    private escapeRegex(str: string): string {
        return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }
}

// 单例导出
export const textAnchorService = new TextAnchorService();
```

**验收标准**：
- ✅ 创建文本锚点功能完整
- ✅ 三种重定位策略都能工作
- ✅ 模糊匹配算法测试通过
- ✅ 单元测试覆盖率 > 80%

---

#### Day 2 上午：PDF 坐标服务
**文件**：`frontend/src/services/annotation/pdfCoordinates.ts`

```typescript
import { PDFPageProxy, PageViewport } from 'pdfjs-dist';
import { QuadPoint, PDFCoordinates } from '../../types/annotation';

export class PDFCoordinateService {
    /**
     * 获取 QuadPoints（支持跨行选择）
     */
    async getQuadPoints(
        selection: Selection,
        pageNumber: number,
        pdfPage: PDFPageProxy
    ): Promise<QuadPoint[]> {
        const range = selection.getRangeAt(0);
        const clientRects = Array.from(range.getClientRects());
        
        if (clientRects.length === 0) {
            throw new Error('No client rects found for selection');
        }
        
        // 获取页面元素和位置
        const pageElement = document.querySelector(
            `[data-page-number="${pageNumber}"]`
        );
        if (!pageElement) {
            throw new Error(`Page element not found: ${pageNumber}`);
        }
        
        const pageRect = pageElement.getBoundingClientRect();
        
        // 获取 PDF 视口（使用 scale=1.0 获取原始坐标）
        const viewport = pdfPage.getViewport({ scale: 1.0 });
        
        // 转换每个 ClientRect
        const quadPoints: QuadPoint[] = [];
        
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
    
    /**
     * 创建完整的 PDF 坐标数据
     */
    async createPDFCoordinates(
        selection: Selection,
        pageNumber: number,
        pdfPage: PDFPageProxy
    ): Promise<PDFCoordinates> {
        const quadPoints = await this.getQuadPoints(selection, pageNumber, pdfPage);
        const viewport = pdfPage.getViewport({ scale: 1.0 });
        
        return {
            pageNumber,
            quadPoints,
            rotation: pdfPage.rotate || 0,
            pageWidth: viewport.width,
            pageHeight: viewport.height
        };
    }
    
    /**
     * 将 QuadPoint 转换为屏幕坐标（用于渲染）
     */
    convertQuadPointToScreen(
        quad: QuadPoint,
        viewport: PageViewport
    ): {
        x: number;
        y: number;
        width: number;
        height: number;
        points: number[][];
    } {
        // 转换四个顶点
        const [x1, y1] = viewport.convertToViewportPoint(quad.x1, quad.y1);
        const [x2, y2] = viewport.convertToViewportPoint(quad.x2, quad.y2);
        const [x3, y3] = viewport.convertToViewportPoint(quad.x3, quad.y3);
        const [x4, y4] = viewport.convertToViewportPoint(quad.x4, quad.y4);
        
        return {
            x: Math.min(x1, x2, x3, x4),
            y: Math.min(y1, y2, y3, y4),
            width: Math.max(x1, x2, x3, x4) - Math.min(x1, x2, x3, x4),
            height: Math.max(y1, y2, y3, y4) - Math.min(y1, y2, y3, y4),
            points: [[x1, y1], [x2, y2], [x4, y4], [x3, y3]]  // 绘制顺序
        };
    }
}

// 单例导出
export const pdfCoordinateService = new PDFCoordinateService();
```

**验收标准**：
- ✅ QuadPoints 计算正确
- ✅ 支持跨行选择
- ✅ 坐标转换精确
- ✅ 处理页面旋转

---

#### Day 2 下午：Canvas 渲染组件
**文件**：`frontend/src/components/AnnotationCanvas.tsx`

```typescript
import React, { useEffect, useRef } from 'react';
import { PDFPageProxy } from 'pdfjs-dist';
import { AnnotationData } from '../types/annotation';
import { pdfCoordinateService } from '../services/annotation/pdfCoordinates';

interface AnnotationCanvasProps {
    pageNumber: number;
    annotations: AnnotationData[];
    scale: number;
    pdfPage: PDFPageProxy | null;
    onAnnotationClick?: (annotationId: string) => void;
}

export const AnnotationCanvas: React.FC<AnnotationCanvasProps> = ({
    pageNumber,
    annotations,
    scale,
    pdfPage,
    onAnnotationClick
}) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    
    useEffect(() => {
        if (!canvasRef.current || !pdfPage) return;
        
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;
        
        // 获取视口
        const viewport = pdfPage.getViewport({ scale });
        
        // 设置画布尺寸
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        
        // 清空画布
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // 筛选当前页面的标注
        const pageAnnotations = annotations.filter(
            a => a.pdfCoordinates.pageNumber === pageNumber
        );
        
        // 渲染每个标注
        pageAnnotations.forEach(annotation => {
            renderAnnotation(ctx, annotation, viewport);
        });
    }, [pageNumber, annotations, scale, pdfPage]);
    
    const renderAnnotation = (
        ctx: CanvasRenderingContext2D,
        annotation: AnnotationData,
        viewport: any
    ) => {
        const { quadPoints } = annotation.pdfCoordinates;
        const { style } = annotation;
        
        // 转换每个 QuadPoint 并渲染
        quadPoints.forEach(quad => {
            const screenCoords = pdfCoordinateService.convertQuadPointToScreen(
                quad,
                viewport
            );
            
            // 绘制路径
            ctx.beginPath();
            screenCoords.points.forEach((point, index) => {
                if (index === 0) {
                    ctx.moveTo(point[0], point[1]);
                } else {
                    ctx.lineTo(point[0], point[1]);
                }
            });
            ctx.closePath();
            
            // 应用样式
            applyStyle(ctx, style);
        });
    };
    
    const applyStyle = (
        ctx: CanvasRenderingContext2D,
        style: AnnotationData['style']
    ) => {
        const rgbaColor = hexToRgba(style.color, style.opacity);
        
        switch (style.type) {
            case 'highlight':
                ctx.fillStyle = rgbaColor;
                ctx.fill();
                break;
            
            case 'underline':
                ctx.strokeStyle = rgbaColor;
                ctx.lineWidth = style.strokeWidth || 2;
                ctx.stroke();
                break;
            
            case 'strikethrough':
                ctx.strokeStyle = rgbaColor;
                ctx.lineWidth = style.strokeWidth || 2;
                // 计算中线位置并绘制
                ctx.stroke();
                break;
        }
    };
    
    return (
        <canvas
            ref={canvasRef}
            className="absolute top-0 left-0 pointer-events-none"
            style={{ zIndex: 10 }}
        />
    );
};

function hexToRgba(hex: string, opacity: number): string {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${opacity})`;
}
```

**验收标准**：
- ✅ Canvas 渲染正确
- ✅ 支持高亮、下划线、删除线
- ✅ 缩放时自动更新
- ✅ 性能良好（60fps）

---

### Day 3-4：Phase 2 标注功能

#### Day 3 上午：集成到 PDFViewerEnhanced
**文件**：`frontend/src/components/PDFViewerEnhanced.tsx`

**主要修改**：
1. 引入新的服务和组件
2. 修改 `handleSelection` 使用新系统
3. 添加 AnnotationCanvas 到渲染树
4. 实现标注创建功能

```typescript
// 添加导入
import { textAnchorService } from '../services/annotation/textAnchor';
import { pdfCoordinateService } from '../services/annotation/pdfCoordinates';
import { AnnotationCanvas } from './AnnotationCanvas';
import { AnnotationData } from '../types/annotation';

// 修改 handleSelection
const handleSelection = async () => {
    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0) return;
    
    const selectedText = selection.toString().trim();
    if (!selectedText) return;
    
    // 获取页面信息
    const range = selection.getRangeAt(0);
    const pageElement = range.commonAncestorContainer.parentElement?.closest('[data-page-number]');
    if (!pageElement) return;
    
    const pageNumber = parseInt(pageElement.getAttribute('data-page-number') || '1');
    const pdfPage = await getPDFPage(pageNumber);
    if (!pdfPage) return;
    
    // 创建文本锚点
    const textAnchor = await textAnchorService.createTextAnchor(
        selection,
        pageNumber,
        pdfPage
    );
    
    // 创建 PDF 坐标
    const pdfCoordinates = await pdfCoordinateService.createPDFCoordinates(
        selection,
        pageNumber,
        pdfPage
    );
    
    // 计算工具栏位置（屏幕坐标）
    const rect = range.getBoundingClientRect();
    const containerRect = containerRef.current?.getBoundingClientRect();
    
    setSelectionInfo({
        selected_text: selectedText,
        page_number: pageNumber,
        textAnchor,
        pdfCoordinates,
        toolbarX: rect.left - (containerRect?.left || 0),
        toolbarY: rect.top - (containerRect?.top || 0) - 44
    });
};

// 添加创建标注的函数
const createAnnotation = async (type: 'highlight' | 'underline' | 'strikethrough') => {
    if (!selectionInfo) return;
    
    const annotation: AnnotationData = {
        id: uuidv4(),
        documentId: document_id,
        textAnchor: selectionInfo.textAnchor,
        pdfCoordinates: selectionInfo.pdfCoordinates,
        style: {
            type,
            color: type === 'highlight' ? '#FAEB96' : '#FF0000',
            opacity: type === 'highlight' ? 0.45 : 0.8,
            strokeWidth: 2
        },
        metadata: {
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
            userId: 'current-user'
        }
    };
    
    // 保存到后端
    await api.createAnnotation(annotation);
    
    // 更新本地状态
    setAnnotations(prev => [...prev, annotation]);
    
    // 清空选择
    setSelectionInfo(null);
    window.getSelection()?.removeAllRanges();
};

// 在渲染中添加 AnnotationCanvas
{pdfPagesCache.current.has(pageNumber) && (
    <AnnotationCanvas
        pageNumber={pageNumber}
        annotations={annotations}
        scale={scale}
        pdfPage={pdfPagesCache.current.get(pageNumber)}
    />
)}
```

**验收标准**：
- ✅ 选择文本创建标注
- ✅ 标注正确渲染
- ✅ 缩放时位置正确
- ✅ 切换页面正常

---

#### Day 3 下午 & Day 4：后端 API
**文件**：
- `backend/app/models/db/models_simple.py`
- `backend/app/schemas/annotation.py`
- `backend/app/repositories/annotation_repository.py`
- `backend/app/api/v1/endpoints/annotations.py`

（详细代码见设计文档）

**验收标准**：
- ✅ 数据库模型完整
- ✅ CRUD API 完整
- ✅ 与前端集成成功
- ✅ API 测试通过

---

### Day 5-6：Phase 3 批注功能

#### 文字批注、图形批注、自由绘制
（详细实现见设计文档）

---

### Day 7-8：Phase 4 交互和优化

#### 拖拽、删除、编辑
#### 性能优化
#### 虚拟化渲染

---

### Day 9-10：测试和文档

#### 完整测试
#### 用户文档
#### 开发文档

---

## 🎯 验收标准

### 功能完整性
- ✅ 支持高亮、下划线、删除线
- ✅ 支持文字批注
- ✅ 支持图形批注
- ✅ 支持自由绘制
- ✅ 支持拖拽移动
- ✅ 支持删除编辑

### 技术质量
- ✅ 位置精确（误差 < 2px）
- ✅ 缩放适应（50%-400%）
- ✅ 跨设备同步
- ✅ 性能良好（60fps）
- ✅ 代码覆盖率 > 80%

### 用户体验
- ✅ 操作流畅
- ✅ 响应及时（< 100ms）
- ✅ 错误提示友好
- ✅ 支持撤销重做

---

**文档创建时间**：2025-10-08 19:30  
**预计开始时间**：2025-10-08  
**预计完成时间**：2025-10-18
