# PDF 详情页面空白问题 - 根本原因和解决方案

**问题**: 点击 PDF 查看详情,页面全白,没有内容显示  
**诊断时间**: 2025-10-08  
**状态**: ✅ 已找到并修复

---

## 🔍 根本原因

### 问题: Vite 配置缺少代理设置

**文件**: `frontend/vite.config.ts`

**问题描述**:
前端配置中没有设置 API 代理,导致所有对 `/api/v1/*` 的请求都失败 (404 或 CORS 错误)。

### 为什么会导致页面空白?

1. **DocumentViewerPage** 尝试获取文档数据:
   ```typescript
   const { data: document, isLoading, error } = useQuery({
       queryKey: ['document', id],
       queryFn: () => apiService.getDocument(id!),
   });
   ```

2. **API 请求失败** (因为没有代理到后端):
   - `GET /api/v1/documents/{id}` → 404 Not Found
   - 前端无法获取文档数据

3. **React 组件渲染空白**:
   - `document` 为 undefined
   - `error` 存在但未正确显示
   - 页面显示为空白

---

## ✅ 解决方案

### 修复: 添加 Vite 代理配置

**修改文件**: `frontend/vite.config.ts`

**修改前**:
```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    host: true,
    strictPort: true,
  },
})
```

**修改后**:
```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    host: true,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
```

### 代理配置说明

| 路径      | 目标                    | 作用                    |
| --------- | ----------------------- | ----------------------- |
| `/api`    | `http://localhost:8000` | 转发所有 API 请求到后端 |
| `/health` | `http://localhost:8000` | 转发健康检查请求        |

**工作原理**:
```
浏览器请求: http://localhost:5174/api/v1/documents/123
   ↓
Vite 代理: http://localhost:8000/api/v1/documents/123
   ↓
后端响应: 返回文档数据
```

---

## 🚀 应用修复

### 步骤 1: 重启前端服务器 (必须)

**方法 A: 使用自动脚本**
```powershell
.\RESTART_FRONTEND.bat
```

**方法 B: 手动重启**
```powershell
# 1. 停止前端 (Ctrl+C 或关闭终端)
# 或使用命令:
taskkill /F /IM node.exe

# 2. 重新启动
cd frontend
npm run dev
```

### 步骤 2: 验证代理生效

打开浏览器访问 http://localhost:5174,按 F12:

1. **Network 标签** - 查看请求:
   - `GET /api/v1/documents` 应该返回 **200 OK**
   - 不应该有 404 或 CORS 错误

2. **Console 标签** - 应该没有:
   - ❌ "Failed to fetch"
   - ❌ "Network Error"
   - ❌ "CORS policy"

### 步骤 3: 测试 PDF 详情页面

1. 访问主页 http://localhost:5174
2. 上传一个测试 PDF (如 `论文.pdf`)
3. 点击文档查看详情
4. **页面应该正常显示 PDF 内容** ✅

---

## 🧪 验证清单

完成重启后,验证以下功能:

- [ ] **主页正常显示** - 文档列表可见
- [ ] **可以上传 PDF** - 上传进度显示正常
- [ ] **详情页显示内容** - PDF 渲染正常,不再空白
- [ ] **书签面板可用** - 点击书签图标显示面板
- [ ] **AI 聊天正常** - 可以发送消息并收到回复
- [ ] **文本选择工作** - 选中文字后聊天面板自动打开

---

## 🐛 如果问题仍然存在

### 检查 1: 确认后端运行

```powershell
# 检查后端进程
Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.Path -like "*IntelliPDF*backend*"}

# 测试后端健康
curl http://localhost:8000/health
```

**预期结果**: 
```json
{"status":"healthy","version":"0.1.0"}
```

### 检查 2: 查看浏览器 Console 错误

按 F12,切换到 Console 标签,查找:

**常见错误**:
```
❌ Failed to fetch
   → 后端未运行或端口错误

❌ CORS policy error
   → 代理配置未生效,需要完全重启前端

❌ 404 Not Found
   → API 路径错误或后端路由未注册
```

### 检查 3: 查看 Network 请求详情

1. 切换到 Network 标签
2. 刷新页面
3. 找到 `/api/v1/documents` 请求
4. 点击查看:
   - **Request URL**: 应该是 `http://localhost:5174/api/v1/...`
   - **Status**: 应该是 200
   - **Response**: 应该有 JSON 数据

---

## 📊 技术细节

### 为什么需要代理?

**浏览器同源策略 (CORS)**:
- 前端: `http://localhost:5174`
- 后端: `http://localhost:8000`
- 这是不同的源 (端口不同)

**解决方案**:
1. **方案 A**: 后端配置 CORS 头 (已配置,但不够)
2. **方案 B**: 前端代理请求 ✅ (推荐,开发环境常用)

### Vite 代理 vs 生产环境

**开发环境 (Vite)**:
```
浏览器 → http://localhost:5174/api → Vite Proxy → http://localhost:8000/api
```

**生产环境 (Nginx/Docker)**:
```
浏览器 → https://yourdomain.com/api → Nginx → Backend Container
```

---

## ✅ 预期修复效果

修复后的用户体验:

### 修复前 ❌
- 点击 PDF 详情 → 页面空白
- Console 显示网络错误
- Network 显示 404

### 修复后 ✅
- 点击 PDF 详情 → PDF 正常显示
- 可以看到页码、缩放按钮
- 书签面板可以打开
- AI 聊天正常工作
- 文本选择功能正常

---

## 🎯 总结

### 问题
PDF 详情页面空白

### 原因
Vite 配置缺少 API 代理,导致前端无法连接后端

### 解决
在 `vite.config.ts` 中添加代理配置

### 操作
重启前端服务器应用配置

### 验证
访问 PDF 详情页面,应该正常显示内容

---

**修复状态**: ✅ 已完成  
**需要操作**: 重启前端服务器  
**预计时间**: 1 分钟  

---

**立即执行**:
```powershell
cd D:\IntelliPDF
.\RESTART_FRONTEND.bat
```

然后访问 http://localhost:5174 测试! 🚀
