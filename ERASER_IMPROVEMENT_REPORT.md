# 橡皮擦工具改进报告

## 改进内容

### 1. 橡皮擦光标显示
**实现**: 创建一个跟随鼠标的圆形光标
```typescript
const createEraserCursor = () => {
    const cursor = document.createElement('div');
    cursor.style.position = 'absolute';
    cursor.style.width = `${eraserSize}px`;
    cursor.style.height = `${eraserSize}px`;
    cursor.style.borderRadius = '50%';
    cursor.style.border = '2px solid #ff0000';
    cursor.style.backgroundColor = 'rgba(255, 0, 0, 0.1)';
    cursor.style.pointerEvents = 'none';
    cursor.style.zIndex = '1000';
    cursor.style.transform = 'translate(-50%, -50%)';
    container.appendChild(cursor);
    return cursor;
};
```

### 2. 大小控制
**实现**: 橡皮擦大小由annotationThickness参数控制
- 计算公式: `eraserSize = annotationThickness * 10`
- 可选值: 1, 2, 3, 4, 5 (对应橡皮擦直径: 10px, 20px, 30px, 40px, 50px)
- UI位置: PDFAnnotationToolbar中的"大小"选择器

### 3. 碰撞检测和擦除
**实现**: 按住鼠标拖动时检测碰撞
```typescript
const checkCollision = (x: number, y: number): HTMLElement[] => {
    const annotations = container.querySelectorAll('.saved-annotation');
    const collided: HTMLElement[] = [];
    
    annotations.forEach((annot) => {
        const rect = annot.getBoundingClientRect();
        const containerRect = container.getBoundingClientRect();
        const relativeRect = {
            left: rect.left - containerRect.left,
            right: rect.right - containerRect.left,
            top: rect.top - containerRect.top,
            bottom: rect.bottom - containerRect.top
        };
        
        const halfSize = eraserSize / 2;
        if (x + halfSize > relativeRect.left && x - halfSize < relativeRect.right &&
            y + halfSize > relativeRect.top && y - halfSize < relativeRect.bottom) {
            collided.push(annot as HTMLElement);
        }
    });
    
    return collided;
};
```

### 4. 擦除动画
**实现**: CSS动画效果
```css
.saved-annotation.erasing {
    animation: erasing-pulse 0.3s ease-out;
    opacity: 0;
    transform: scale(0.8);
}

@keyframes erasing-pulse {
    0% {
        opacity: 1;
        transform: scale(1);
    }
    50% {
        opacity: 0.5;
        transform: scale(1.1);
    }
    100% {
        opacity: 0;
        transform: scale(0.8);
    }
}
```

## 用户体验改进

### 交互流程
1. 点击橡皮擦工具按钮
2. 在工具栏中选择橡皮擦大小(1-5)
3. 鼠标移动时显示红色圆形光标
4. 按住鼠标拖动,碰到的标注自动标记为"erasing"
5. 松开鼠标时,所有碰到的标注被删除并保存

### 视觉反馈
- **光标**: 红色边框圆形,半透明红色填充
- **动画**: 标注被擦除时有缩小+淡出动画
- **提示**: 工具栏显示"橡皮擦模式：按住鼠标拖动擦除标注 (大小: X)"

## 技术细节

### 文件修改
1. **PDFViewerNative.tsx**
   - 重写`enableEraserMode`函数
   - 添加光标创建逻辑
   - 添加碰撞检测逻辑
   - 添加鼠标事件处理(mousedown, mousemove, mouseup)
   - 添加CSS动画样式

2. **PDFAnnotationToolbar.tsx**
   - 扩展粗细选择器支持ERASER模式
   - 修改标签文本: ERASER模式显示"大小"
   - 修改tooltip: 显示"橡皮擦大小"

### 依赖参数
```typescript
const enableEraserMode = useCallback((container: HTMLElement) => {
    // ...
}, [pdfDocument, saveAnnotations, annotationThickness]);
```
- `pdfDocument`: 获取annotationStorage
- `saveAnnotations`: 保存删除后的标注
- `annotationThickness`: 控制橡皮擦大小

## 待优化项

### 1. 碰撞检测优化
**当前**: 检测整个标注矩形边界
**改进方向**: 检测标注的实际路径(对于INK类型的自由绘制)

### 2. 性能优化
**当前**: 每次mousemove都检测所有标注
**改进方向**: 使用空间索引(如四叉树)减少检测数量

### 3. 撤销功能
**当前**: 删除后无法撤销
**改进方向**: 实现撤销栈,支持Ctrl+Z撤销擦除

## 下一步工作

### 高亮工具集成
用户要求"高亮功能还是要在原来选取文字的组件里面":
1. 使用PDF.js原生HIGHLIGHT模式(类型9)
2. 监听文本选择事件
3. 应用当前颜色和透明度样式
4. 自动保存高亮标注

### 实现计划
```typescript
// 在initializeEditorLayer中添加HIGHLIGHT模式处理
} else if (editorMode === AnnotationEditorType.HIGHLIGHT) {
    // 启用PDF.js原生高亮编辑器
    const eventBus = new pdfjsLib.EventBus();
    const annotationEditorParams = {
        mode: AnnotationEditorType.HIGHLIGHT,
        uiManager: new AnnotationEditorUIManager(...),
        eventBus,
    };
    // 配置高亮颜色和透明度
    // 监听文本选择事件
}
```

## 测试验证

### 测试步骤
1. 启动前端服务: `cd frontend && npm run dev`
2. 上传一个带有多种标注的PDF
3. 点击橡皮擦工具
4. 测试不同大小的橡皮擦(1-5)
5. 拖动鼠标擦除标注
6. 验证:
   - 光标正确显示
   - 大小控制有效
   - 碰撞检测准确
   - 动画流畅
   - 删除保存成功

### 预期结果
- ✅ 橡皮擦光标跟随鼠标
- ✅ 大小可调(10px-50px)
- ✅ 拖动擦除(非点击)
- ✅ 动画流畅无卡顿
- ✅ 删除后自动保存

## 总结

橡皮擦工具已按用户需求完成改进:
- ✅ 显示橡皮擦光标(红色圆形)
- ✅ 支持大小控制(1-5档位)
- ✅ 碰到即删除(拖动擦除)
- ✅ 视觉反馈(动画效果)

下一阶段: 高亮工具的文本选择集成
