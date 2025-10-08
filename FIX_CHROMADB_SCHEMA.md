# 修复 ChromaDB Schema 错误

## 问题
```
ERROR: no such column: collections.topic
```

## 原因
ChromaDB 数据库的 schema 版本不匹配或数据损坏

## 解决方案

### 方案 1: 删除并重新创建数据库（推荐）

```powershell
# 1. 停止后端服务
# 按 Ctrl+C

# 2. 删除 ChromaDB 数据库
cd backend
Remove-Item -Path "data/chroma_db" -Recurse -Force

# 3. 重新启动服务（会自动创建新数据库）
.\venv\Scripts\python.exe main.py

# 4. 重新上传文档
# 因为向量数据库被清空了，需要重新上传 PDF
```

### 方案 2: 升级 ChromaDB

```powershell
cd backend
.\venv\Scripts\Activate.ps1
pip install --upgrade chromadb
```

## 注意事项

**⚠️ 删除数据库会导致**:
- 所有已上传文档的向量索引丢失
- 需要重新上传 PDF 文档
- 文档元数据（数据库中）仍然保留
- 只是需要重新生成向量嵌入

## 执行步骤

1. 停止后端
2. 备份（可选）: `cp -r data/chroma_db data/chroma_db.backup`
3. 删除: `Remove-Item -Path "data/chroma_db" -Recurse -Force`
4. 启动后端
5. 重新上传文档
