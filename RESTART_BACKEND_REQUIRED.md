# Phase 7 删除功能修复

## 修复内容

修复了后端 DELETE 端点的问题:

### 问题
`repo.delete()` 方法接受 UUID 参数,但 endpoint 传入了 model 实例

### 修复
```python
# OLD (错误):
await repo.delete(model)

# NEW (正确):
deleted = await repo.delete(id_uuid)
```

## 测试步骤

1. **重启后端服务器** (重要!)
   ```powershell
   # 停止当前运行的服务器 (Ctrl+C)
   # 然后重新启动:
   cd backend
   .\start.bat
   ```

2. **运行测试脚本**
   ```powershell
   python test_annotation_selection.py
   ```

## 预期结果

```
✅ 创建rectangle标注成功
✅ 创建circle标注成功
✅ 创建arrow标注成功
✅ 删除标注成功
✅ 验证成功: 标注已被删除
✅ 清理完成
```

## 文件修改

- `backend/app/api/v1/endpoints/annotations.py` - 修复 delete_annotation 端点
- `frontend/src/services/api.ts` - 添加 deleteAnnotation 和 updateAnnotation 方法
- `frontend/src/components/PDFViewerEnhanced.tsx` - 添加键盘 Delete 键处理
- `test_annotation_selection.py` - 新测试脚本
