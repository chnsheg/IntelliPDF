# PDF 详情页面空白问题诊断指南

**问题**: 打开 PDF 详情页面没有显示内容  
**日期**: 2025-10-08

---

## 🔍 快速诊断步骤

### 步骤 1: 打开浏览器开发者工具
1. 按 **F12** 打开开发者工具
2. 切换到 **Console** (控制台) 标签
3. 查看是否有**红色错误消息**

#### 可能的错误及解决方案:

**错误 A: "找不到模块 ChatPanel"**
```
Module not found: Error: Can't resolve '../components/ChatPanel'
```
**原因**: TypeScript 编译缓存问题  
**解决**: 
```powershell
# 方法 1: 运行清理脚本
.\RESTART_FRONTEND.bat

# 方法 2: 手动清理
cd frontend
rm -r node_modules\.vite
npm run dev
```

**错误 B: "document is undefined"**
```
TypeError: Cannot read properties of undefined (reading 'filename')
```
**原因**: 文档数据加载失败  
**解决**: 检查后端 API 是否正常 (见步骤 2)

**错误 C: "Failed to fetch"**
```
TypeError: Failed to fetch
```
**原因**: 后端服务器未运行或端口错误  
**解决**: 
```powershell
# 确认后端运行
cd backend
.\venv\Scripts\Activate.ps1
python main.py
```

---

### 步骤 2: 检查 Network (网络) 请求

1. 切换到 **Network** 标签
2. 刷新页面 (F5)
3. 查找以下关键请求:

#### 必须成功的请求:

| 请求 | URL                                      | 状态码 | 说明          |
| ---- | ---------------------------------------- | ------ | ------------- |
| 1    | `GET /api/v1/documents/{id}`             | 200    | 获取文档信息  |
| 2    | `GET /api/v1/documents/{id}/chunks`      | 200    | 获取分块数据  |
| 3    | `GET /api/v1/bookmarks?document_id={id}` | 200    | 获取书签列表  |
| 4    | `GET /api/v1/documents/{id}/file`        | 200    | 获取 PDF 文件 |

#### 如果某个请求失败:

**状态码 404** - 文档不存在
- 检查 URL 中的文档 ID 是否正确
- 尝试重新上传文档

**状态码 500** - 后端错误
- 查看后端终端的错误日志
- 检查 `backend/logs/errors_*.log`

**状态码 0 / Failed** - 后端未运行
- 确认后端在 http://localhost:8000 运行
- 测试: 访问 http://localhost:8000/health

---

### 步骤 3: 检查 React 组件状态

1. 安装 **React DevTools** 浏览器扩展 (如果未安装)
2. 打开扩展,切换到 **Components** 标签
3. 找到 `DocumentViewerPage` 组件
4. 查看右侧面板的 **props** 和 **state**

#### 检查点:

- ✅ `document` 有值 (不是 null/undefined)
- ✅ `fileUrl` 是有效的 URL
- ✅ `chunksData` 有值 (可能为空数组)
- ✅ `isLoading` 为 false
- ✅ `error` 为 null

---

## 🐛 常见问题及解决方案

### 问题 1: 页面一直显示"加载中"

**症状**: 旋转的加载动画一直显示  
**原因**: `isLoading` 状态未变为 false

**检查**:
```typescript
// 在 DocumentViewerPage.tsx 中
const { data: document, isLoading, error } = useQuery({...});
```

**解决**:
1. 检查 Network 面板,`GET /api/v1/documents/{id}` 是否完成
2. 如果请求卡住,检查后端是否响应
3. 如果请求返回错误,检查后端日志

---

### 问题 2: 显示"文档加载失败"

**症状**: 页面显示红色错误提示  
**原因**: `error` 不为 null 或 `document` 为空

**检查**:
1. 打开 Console,查看错误详情
2. 检查 Network 面板,找到失败的请求
3. 查看响应内容 (Response 标签)

**常见原因**:
- 文档 ID 错误 (404)
- 文档处理失败 (500)
- 数据库连接问题

---

### 问题 3: PDF 区域空白

**症状**: 页面布局正常,但 PDF 显示区域是空白的  
**原因**: PDFViewerEnhanced 组件加载失败

**检查**:
1. Console 是否有 "pdf.js" 相关错误
2. Network 面板,PDF 文件请求 (`/documents/{id}/file`) 是否成功
3. 检查 `fileUrl` 是否正确

**解决**:
```typescript
// 检查 fileUrl 格式
const fileUrl = apiService.getDocumentUrl(document.id);
// 应该类似: http://localhost:8000/api/v1/documents/{id}/file
```

---

### 问题 4: 书签/聊天面板不显示

**症状**: 点击书签/聊天按钮无反应  
**原因**: 组件导入或状态管理问题

**检查**:
1. Console 是否有组件导入错误
2. React DevTools 中检查 `chatOpen` / `bookmarkOpen` 状态
3. 确认组件文件存在:
   - `frontend/src/components/ChatPanel.tsx`
   - `frontend/src/components/BookmarkPanel.tsx`

**解决**:
```powershell
# 清除缓存并重启
.\RESTART_FRONTEND.bat
```

---

## 🔧 强制刷新前端

如果上述方法都不行,尝试完全重启前端:

```powershell
# 停止所有 Node 进程
taskkill /F /IM node.exe

# 进入前端目录
cd frontend

# 清除所有缓存
rm -r node_modules\.vite
rm -r dist
rm .tsbuildinfo

# 重新启动
npm run dev
```

---

## 🧪 测试后端 API 可用性

**不要运行测试脚本** (会中断服务器),而是手动测试:

### 方法 1: 浏览器访问
```
http://localhost:8000/health
http://localhost:8000/api/docs
```

### 方法 2: PowerShell 快速测试
```powershell
# 健康检查
curl http://localhost:8000/health

# 获取文档列表 (替换 {id} 为实际文档 ID)
curl http://localhost:8000/api/v1/documents
```

---

## 📊 完整诊断清单

请按顺序检查以下项目:

- [ ] **后端运行**: http://localhost:8000/health 返回 200
- [ ] **前端运行**: http://localhost:5174 可访问
- [ ] **Console 无错误**: F12 → Console 没有红色错误
- [ ] **文档请求成功**: Network → `GET /documents/{id}` 返回 200
- [ ] **PDF 文件可访问**: Network → `GET /documents/{id}/file` 返回 200
- [ ] **组件正常加载**: 没有 "Module not found" 错误
- [ ] **React 状态正确**: DevTools → `document` 有值, `isLoading` 为 false

---

## 💡 如果问题依然存在

请提供以下信息:

1. **Console 控制台截图** (包含所有错误消息)
2. **Network 面板截图** (显示所有请求的状态码)
3. **React DevTools 截图** (DocumentViewerPage 组件的 props)
4. **后端终端输出** (最后 20 行日志)

这将帮助快速定位问题!

---

## 🚀 快速恢复步骤

如果完全不确定问题在哪,按此顺序操作:

```powershell
# 1. 停止所有进程
taskkill /F /IM node.exe
taskkill /F /IM python.exe

# 2. 清理前端缓存
cd frontend
rm -r node_modules\.vite
cd ..

# 3. 启动后端 (新终端窗口)
cd backend
.\venv\Scripts\Activate.ps1
python main.py

# 4. 启动前端 (新终端窗口)
cd frontend
npm run dev

# 5. 等待 10 秒,然后访问
# http://localhost:5174
```

---

**最后更新**: 2025-10-08  
**相关文档**: BOOKMARK_INTEGRATION_TEST_GUIDE.md
