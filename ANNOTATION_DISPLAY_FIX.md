# 标注显示问题诊断报告

## 问题描述
用户报告：前端绘制的标注虽然创建成功（控制台显示成功），但在页面上不可见，也无法拖拽和缩放。

## 根本原因分析

### 1. 主要问题：创建后未刷新状态
**位置**: `PDFViewerEnhanced.tsx::handleShapeComplete`

**问题**: 图形标注保存到后端后，没有重新加载标注列表，导致本地 `annotations` 状态未更新。

```typescript
// ❌ 问题代码
await apiService.createAnnotation(annotationPayload);
// 缺少重新加载标注的逻辑

// ✅ 修复后
await apiService.createAnnotation(annotationPayload);
const resp = await apiService.getAnnotationsForDocument(documentId);
const backendAnnotations = resp.annotations || [];
const transformedAnnotations = backendAnnotations.map(transformBackendAnnotation);
setAnnotations(transformedAnnotations);
```

### 2. 便笺双重状态问题
**位置**: `PDFViewerEnhanced.tsx`

**问题**: 便笺使用了两个独立的状态：
- `noteAnnotations`: 临时存储未保存的便笺
- `annotations`: 存储已保存的标注（包括便笺）

这导致：
1. NoteTool 显示 `noteAnnotations`（临时）
2. AnnotationCanvas 显示 `annotations`（已保存）
3. 便笺保存后只更新了 `annotations`，但 NoteTool 看不到

### 3. 便笺工作流混乱
**当前流程**:
```
用户点击 → handleNoteComplete(添加到 noteAnnotations) 
→ 用户编辑内容 → handleNoteUpdate(保存到后端 + 更新 annotations)
→ NoteTool 仍显示 noteAnnotations（旧状态）
```

## 修复方案

### 修复1: handleShapeComplete 添加重新加载
✅ 已修复

### 修复2: 统一便笺状态管理
需要修改 NoteTool，让它直接使用 `annotations` 而不是 `noteAnnotations`。

### 修复3: 简化便笺创建流程
移除 `noteAnnotations` 临时状态，直接操作 `annotations`。

## 影响范围
- ShapeTool: 图形标注创建
- NoteTool: 便笺创建和显示
- AnnotationCanvas: 所有标注渲染
- DraggableAnnotation: 标注拖拽和调整

## 测试计划
1. 创建矩形标注 → 验证立即显示
2. 创建便笺 → 验证立即显示
3. 拖拽标注 → 验证实时预览和保存
4. 调整标注大小 → 验证实时预览和保存
5. 撤销/重做 → 验证状态同步
