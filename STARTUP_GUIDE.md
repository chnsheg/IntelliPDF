# IntelliPDF 启动和测试指南

## 📋 前置要求

- Python 3.10+
- 虚拟环境已创建并激活
- 依赖已安装（requirements/base.txt）

## 🚀 启动步骤

### 1. 激活虚拟环境

```powershell
cd d:\IntelliPDF\backend
.\venv\Scripts\Activate.ps1
```

### 2. 启动后端服务器

#### 方法一：使用 Python 直接启动
```powershell
python main.py
```

#### 方法二：使用 uvicorn（推荐用于生产）
```powershell
uvicorn main:app --host 0.0.0.0 --port 8000
```

#### 方法三：使用启动脚本（后台运行）
```powershell
# 在 PowerShell 中
Start-Process -WindowStyle Hidden -FilePath "d:\IntelliPDF\backend\venv\Scripts\uvicorn.exe" -ArgumentList "main:app","--host","0.0.0.0","--port","8000" -WorkingDirectory "d:\IntelliPDF\backend"
```

### 3. 验证服务器运行

访问以下地址验证服务器状态：

- **健康检查**: http://127.0.0.1:8000/api/v1/health
- **API 文档**: http://127.0.0.1:8000/api/docs
- **交互式文档**: http://127.0.0.1:8000/api/redoc

使用 PowerShell 测试：
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/health" -Method GET
```

## 🧪 运行测试

### 测试 Gemini API 连接（独立测试）

```powershell
python backend\test_gemini.py
```

**预期输出**：
```
============================================================
🧪 测试 1: 简单文本生成
============================================================
✅ 成功生成内容 (XX 字符)
Response: 我是Google开发的大型语言模型Gemini。

============================================================
🧪 测试 2: 带系统指令的生成
============================================================
✅ 成功生成内容 (XX 字符)
Response: 您好！我是您的AI助手...

============================================================
🧪 测试 3: 对话功能
============================================================
✅ 成功生成回复 (XX 字符)
Response: Python是一种高级编程语言...
```

### 测试完整 API（需要服务器运行）

```powershell
python backend\test_api.py
```

**预期输出**：
```
============================================================
🏥 测试健康检查端点
============================================================
Status: 200
Response: {'status': 'healthy', 'version': '0.1.0', 'environment': 'development'}

============================================================
🤖 测试 Gemini 简单生成
============================================================
Status: 200
Response: 我是一个大型语言模型...

============================================================
💬 测试 Gemini 对话功能
============================================================
Status: 200
Response: Python 是一种高级的、通用的编程语言...

============================================================
✅ 所有测试完成！
============================================================
```

## 🔧 常见问题

### 问题 1: httpx 返回 502 错误

**症状**: Python httpx 库返回 502 Bad Gateway，但浏览器和 PowerShell 可以访问

**原因**: Windows 系统代理设置影响 httpx

**解决方案**: 在创建 AsyncClient 时添加 `trust_env=False`

```python
async with httpx.AsyncClient(trust_env=False) as client:
    response = await client.get("http://127.0.0.1:8000/api/v1/health")
```

### 问题 2: 端口 8000 已被占用

**解决方案**:
```powershell
# 查找占用端口的进程
netstat -ano | findstr :8000

# 停止进程（替换 PID）
taskkill /F /PID <PID>
```

### 问题 3: uvicorn 自动重载导致崩溃

**症状**: 在 backend 目录创建新文件时服务器崩溃

**解决方案**: 启动时不使用 `--reload` 选项，或将测试文件移到 backend 外

```powershell
# 不使用 reload
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 问题 4: 配置文件 .env 解析错误

**症状**: `SettingsError: error parsing value for field "cors_origins"`

**原因**: 列表类型字段需要使用 JSON 格式

**解决方案**: 在 .env 中使用 JSON 数组格式
```env
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
ALLOWED_EXTENSIONS=[".pdf"]
```

## 📊 API 端点概览

### 健康检查
- **GET** `/api/v1/health` - 服务健康状态

### 测试端点
- **GET** `/api/v1/test/ping` - 简单 ping 测试
- **POST** `/api/v1/test/gemini` - Gemini 简单生成测试
- **POST** `/api/v1/test/gemini/chat` - Gemini 对话测试

### 文档相关（待实现）
- **POST** `/api/v1/documents/upload` - 上传文档
- **GET** `/api/v1/documents/{id}` - 获取文档详情
- **POST** `/api/v1/documents/{id}/chat` - 与文档对话

## 🎯 下一步计划

根据 PROJECT_TODO.md，接下来需要实现：

1. **PDF 解析服务** (Sprint 1.2)
   - 实现 `services/pdf/parser.py`
   - 实现 `services/pdf/extraction.py`
   - 实现 `services/pdf/chunking.py`

2. **AI 服务模块** (Sprint 1.3)
   - 实现 `services/ai/embeddings.py`
   - 实现 `services/ai/retrieval.py`
   - 集成 LangChain

3. **完整 CRUD 操作** (Sprint 1.4)
   - 文档上传和管理
   - 知识库构建
   - 向量存储集成

## 📝 配置说明

### Gemini API 配置

当前配置（`.env`）：
```env
GEMINI_API_KEY=chensheng
GEMINI_BASE_URL=http://152.32.207.237:8132
GEMINI_MODEL=gemini-2.0-flash-exp
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_TOKENS=2048
```

### 数据库配置

开发环境使用 SQLite：
```env
DATABASE_URL=sqlite+aiosqlite:///./data/intellipdf.db
```

生产环境切换到 PostgreSQL：
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/intellipdf
```

## 🛠️ 开发工具

- **API 文档**: FastAPI 自动生成的 Swagger UI
- **日志文件**: `logs/intellipdf_2025-10-07.log`
- **错误日志**: `logs/errors_2025-10-07.log`
- **数据库**: `data/intellipdf.db`
- **向量数据库**: `data/chroma_db/`

---

**项目状态**: ✅ 基础架构完成，Gemini API 集成测试通过
**最后更新**: 2025-10-07
