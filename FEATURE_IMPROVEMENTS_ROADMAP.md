# IntelliPDF 功能改进路线图

## 概述
本文档记录了用户提出的8大功能改进需求及实现计划。

**创建时间**: 2025年10月10日  
**总任务数**: 8个  
**已完成**: 1个  
**进行中**: 0个  
**待开始**: 7个

---

## ✅ 已完成功能

### 1. 优化渲染性能，消除刷新卡顿 ✅

**问题描述**：
- 每次点击工具或绘制完图案触发重新渲染会有明显刷新卡顿感觉
- 原因：`renderSavedAnnotations` 使用 `innerHTML = ''` 清空整个DOM，然后重建所有标注

**解决方案**：
1. **增量渲染机制**：创建 `renderSingleAnnotation` 函数处理单个标注渲染
2. **智能DOM更新**：`saveAndRefresh` 只添加新标注，不删除现有DOM
3. **requestAnimationFrame优化**：使用浏览器原生动画帧优化渲染时机
4. **避免全量重绘**：保留现有标注DOM元素，仅操作变化部分

**代码改动**：
- 文件：`frontend/src/components/PDFViewerNative.tsx`
- 新增：`renderSingleAnnotation` 函数（180行）
- 修改：`saveAndRefresh` 函数（改为增量更新）

**测试结果**：
- ✅ 绘制标注无闪烁
- ✅ 无明显卡顿感
- ✅ 性能提升明显

---

## 🚀 待实现功能（优先级排序）

### 2. 添加橡皮擦工具（Eraser） - 优先级：高

**需求**：
- 创建橡皮擦工具用于擦除标注对象
- 鼠标悬停时高亮目标标注
- 点击删除标注
- 更新 annotationStorage 并重新渲染

**技术方案**：
1. **工具栏添加橡皮擦按钮**（PDFAnnotationToolbar.tsx）
   - 新模式常量：`ERASER = 103`
   - 图标：`FiTrash2` 或 `FiDelete`
   
2. **实现橡皮擦编辑器**（PDFViewerNative.tsx）
   ```typescript
   const enableEraserMode = useCallback((container: HTMLElement) => {
       let hoveredAnnotation: HTMLElement | null = null;
       
       const handleMouseMove = (e: MouseEvent) => {
           // 检测鼠标下的标注元素
           const target = e.target as HTMLElement;
           const annotation = target.closest('.saved-annotation');
           
           if (annotation && annotation !== hoveredAnnotation) {
               hoveredAnnotation?.classList.remove('eraser-hover');
               (annotation as HTMLElement).classList.add('eraser-hover');
               hoveredAnnotation = annotation as HTMLElement;
           }
       };
       
       const handleClick = async (e: MouseEvent) => {
           if (hoveredAnnotation) {
               const id = hoveredAnnotation.dataset.annotationId;
               await deleteAnnotation(id); // 增量删除，无闪烁
           }
       };
       
       container.addEventListener('mousemove', handleMouseMove);
       container.addEventListener('click', handleClick);
   }, []);
   ```

3. **CSS高亮样式**
   ```css
   .saved-annotation.eraser-hover {
       filter: brightness(0.7) saturate(0.5);
       outline: 2px dashed red;
       cursor: not-allowed;
   }
   ```

**预计工作量**：2-3小时

---

### 3. 实现沉浸式阅读模式 - 优先级：高

**需求**：
- 一键折叠所有UI组件（顶部导航、左右侧边栏、工具栏）
- 默认进入折叠状态
- 快捷键：F11 或 Escape
- 悬停边缘显示收起的UI

**技术方案**：
1. **全局状态管理**（DocumentViewer.tsx）
   ```typescript
   const [immersiveMode, setImmersiveMode] = useState(true); // 默认开启
   
   useEffect(() => {
       const handleKeyPress = (e: KeyboardEvent) => {
           if (e.key === 'F11' || e.key === 'Escape') {
               e.preventDefault();
               setImmersiveMode(prev => !prev);
           }
       };
       window.addEventListener('keydown', handleKeyPress);
       return () => window.removeEventListener('keydown', handleKeyPress);
   }, []);
   ```

2. **UI组件条件渲染**
   ```tsx
   {/* 顶部导航 */}
   <div className={immersiveMode ? 'hidden' : 'header'}>...</div>
   
   {/* 左侧边栏 */}
   <div className={immersiveMode ? 'sidebar-collapsed' : 'sidebar'}>
       {!immersiveMode && <BookmarkPanel />}
   </div>
   
   {/* 工具栏 */}
   <PDFAnnotationToolbar 
       hidden={immersiveMode}
       onToggleImmersive={() => setImmersiveMode(!immersiveMode)}
   />
   ```

3. **悬停触发**
   ```tsx
   <div className="screen-edge-trigger left" 
        onMouseEnter={() => setShowLeftPanel(true)} />
   <div className="screen-edge-trigger top" 
        onMouseEnter={() => setShowHeader(true)} />
   ```

**预计工作量**：3-4小时

---

### 4. 添加套索选择工具（Lasso） - 优先级：中

**需求**：
- 框选多个标注对象
- 支持多选、删除、移动、缩放操作

**技术方案**：
1. **绘制选择框**（类似矩形工具）
2. **碰撞检测**：计算选择框与标注的交集
3. **多选操作**：
   - 高亮选中的标注
   - Shift+拖动 = 移动
   - Ctrl+Delete = 批量删除
   - 显示调整手柄 = 缩放

**预计工作量**：4-5小时

---

### 5. 修复高亮工具样式 - 优先级：高

**需求**：
- 类似彩笔涂抹效果
- 半透明彩色覆盖层
- 支持颜色和粗细（高度）调节

**技术方案**：
1. **PDF.js HIGHLIGHT 模式**
   ```typescript
   // 当前：AnnotationEditorType.HIGHLIGHT = 9
   // 修改编辑器初始化参数
   editorParams: {
       highlightColor: annotationColor,
       highlightOpacity: 0.4,
       highlightThickness: annotationThickness * 2 // 映射为高度
   }
   ```

2. **渲染逻辑**（renderSingleAnnotation）
   ```typescript
   if (data.annotationType === AnnotationEditorType.HIGHLIGHT) {
       const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
       const rects = data.rects || []; // PDF.js返回的文字矩形区域
       
       rects.forEach(([x, y, w, h]: number[]) => {
           const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
           rect.setAttribute('x', String(x));
           rect.setAttribute('y', String(y));
           rect.setAttribute('width', String(w));
           rect.setAttribute('height', String(h));
           rect.setAttribute('fill', data.color);
           rect.setAttribute('opacity', '0.4');
           svg.appendChild(rect);
       });
       
       annotDiv.appendChild(svg);
   }
   ```

**预计工作量**：2小时

---

### 6. 实现波浪线和删除线渲染 - 优先级：中

**需求**：
- 波浪线、删除线标注没有渲染
- 需要添加对应的渲染逻辑

**技术方案**：
1. **定义自定义类型**
   ```typescript
   const AnnotationEditorType = {
       // ...现有类型
       UNDERLINE: 104,      // 下划线
       STRIKEOUT: 105,      // 删除线
       SQUIGGLY: 106,       // 波浪线
   };
   ```

2. **波浪线SVG路径生成**
   ```typescript
   function generateWavyLine(x1: number, y: number, x2: number, amplitude: number): string {
       const wavelength = 8;
       const points: string[] = [];
       for (let x = x1; x <= x2; x += wavelength / 4) {
           const offset = amplitude * Math.sin((x - x1) / wavelength * Math.PI * 2);
           points.push(`${x},${y + offset}`);
       }
       return `M ${points.join(' L ')}`;
   }
   ```

3. **渲染实现**
   ```typescript
   if (data.annotationType === AnnotationEditorType.SQUIGGLY) {
       const svg = createSVG();
       const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
       path.setAttribute('d', generateWavyLine(x1, y, x2, 2));
       path.setAttribute('stroke', color);
       path.setAttribute('fill', 'none');
       svg.appendChild(path);
   }
   ```

**预计工作量**：2-3小时

---

### 7. 便笺工具与书签系统融合 - 优先级：中

**需求**：
- 便笺作为特殊书签类型
- 在PDF页面上添加便笺图标
- 便笺列表与书签列表合并显示

**技术方案**：
1. **后端扩展**
   - 新表：`sticky_notes`
     ```sql
     CREATE TABLE sticky_notes (
         id UUID PRIMARY KEY,
         document_id UUID REFERENCES documents(id),
         page_number INTEGER NOT NULL,
         x FLOAT,
         y FLOAT,
         content TEXT,
         color VARCHAR(20),
         created_at TIMESTAMP
     );
     ```
   
2. **前端组件**
   ```tsx
   const StickyNoteMarker: React.FC = ({ note, onClick }) => (
       <div className="sticky-marker" style={{
           position: 'absolute',
           left: note.x,
           top: note.y
       }} onClick={onClick}>
           📝
       </div>
   );
   ```

3. **书签面板整合**
   ```tsx
   <BookmarkPanel>
       <Tab label="AI书签" />
       <Tab label="我的便笺" />
       <Tab label="全部" />
   </BookmarkPanel>
   ```

**预计工作量**：6-8小时（含后端）

---

### 8. AI书签可视化标记 - 优先级：低

**需求**：
- AI生成的书签在PDF旁边显示醒目标记
- 悬停显示书签标题
- 点击展开书签内容

**技术方案**：
1. **获取书签位置**
   ```typescript
   interface AIBookmark {
       id: string;
       title: string;
       page: number;
       yPosition?: number; // 如果没有则使用页面顶部
   }
   ```

2. **侧边书签指示器**
   ```tsx
   <div className="bookmark-indicators">
       {aiBookmarks
           .filter(b => b.page === currentPage)
           .map(bookmark => (
               <div
                   key={bookmark.id}
                   className="bookmark-marker"
                   style={{ top: bookmark.yPosition || 0 }}
                   title={bookmark.title}
                   onClick={() => expandBookmark(bookmark)}
               >
                   🔖
               </div>
           ))}
   </div>
   ```

3. **样式**
   ```css
   .bookmark-indicators {
       position: absolute;
       right: -30px;
       top: 0;
       height: 100%;
   }
   
   .bookmark-marker {
       position: absolute;
       right: 0;
       cursor: pointer;
       font-size: 24px;
       animation: pulse 2s infinite;
   }
   ```

**预计工作量**：3-4小时

---

## 实施时间表

### 第1周（已完成）
- [x] 优化渲染性能

### 第2周（计划）
- [ ] 橡皮擦工具（2天）
- [ ] 沉浸式阅读模式（2天）
- [ ] 修复高亮工具（1天）

### 第3周（计划）
- [ ] 波浪线和删除线（1天）
- [ ] 套索选择工具（3天）

### 第4周（计划）
- [ ] 便笺系统（4天）
- [ ] AI书签可视化（2天）

---

## 技术债务 & 注意事项

1. **性能监控**：添加性能指标收集
2. **兼容性测试**：确保在Safari/Firefox正常工作
3. **移动端适配**：沉浸式模式需要考虑触摸手势
4. **数据迁移**：便笺系统需要数据库迁移脚本
5. **文档更新**：每个功能完成后更新用户文档

---

## 当前状态

**最新更新**：2025年10月10日  
**当前任务**：等待用户测试渲染性能优化  
**下一步**：根据用户反馈决定优先实现哪个功能

**测试地址**：http://localhost:5174  
**前端状态**：✅ 运行中  
**后端状态**：✅ 运行中
