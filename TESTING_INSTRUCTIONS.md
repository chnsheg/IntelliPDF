# IntelliPDF 测试指南

## 当前测试状态

✅ **后端服务器启动成功** - 运行在 http://localhost:8000
✅ **已修复的问题**:
1. knowledge_graph API中的DocumentModel.title错误（改为使用metadata和filename）
2. Settings中SECRET_KEY/ALGORITHM大小写问题（修改为小写secret_key/algorithm）

## 📝 测试步骤（按顺序执行）

### 步骤1: 启动后端服务器

**方法A: 使用命令行（推荐用于开发）**
```powershell
# 打开新的PowerShell终端
cd d:\IntelliPDF\backend
.\venv\Scripts\activate
python main.py
```

**方法B: 使用批处理文件**
```powershell
# 双击运行
d:\IntelliPDF\backend\start_server_simple.bat
```

**验证后端是否启动成功**:
- 浏览器访问: http://localhost:8000/health
- 应该看到: `{"status":"healthy","version":"0.1.0","environment":"development"}`
- 或者访问 API 文档: http://localhost:8000/api/docs

### 步骤2: 测试书签API（在另一个终端）

```powershell
# 打开新的PowerShell终端（不要关闭后端服务器终端！）
cd d:\IntelliPDF
.\backend\venv\Scripts\python.exe test_bookmark_quick.py
```

### 步骤3: 启动前端服务器（在第三个终端）

```powershell
# 打开新的PowerShell终端
cd d:\IntelliPDF\frontend
npm run dev
```

前端将在 http://localhost:5173 启动

### 步骤4: 浏览器测试

1. **打开浏览器** http://localhost:5173

2. **登录/注册**
   - 使用测试账户或创建新账户

3. **上传PDF文档**
   - 点击上传按钮
   - 选择PDF文件（论文.pdf 或 Linux教程.pdf）
   - 等待上传和处理完成

4. **测试书签功能**
   - 在PDF阅读器中选中一段文本
   - 在右侧聊天面板中与AI对话
   - 点击"生成书签"按钮
   - 在书签面板中查看生成的书签

5. **测试书签管理**
   - 搜索书签
   - 编辑书签标题和笔记
   - 点击书签跳转到相应位置
   - 删除书签

### 步骤5: 监控后端日志

在后端服务器终端中，观察日志输出：
- ✅ 正常日志: `INFO: 127.0.0.1:xxxxx - "POST /api/v1/bookmarks HTTP/1.1" 201`
- ❌ 错误日志: `ERROR` 开头的行

如果看到错误，记录错误信息并报告。

## 🐛 常见问题和解决方案

### 问题1: 后端启动失败 - 端口被占用
```
ERROR: [WinError 10013] 以一种访问权限不允许的方式做了一个访问套接字的尝试。
```

**解决方案**:
```powershell
# 停止所有Python进程
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2
# 然后重新启动后端
```

### 问题2: 前端无法连接后端

**检查**:
1. 后端是否正在运行？访问 http://localhost:8000/health
2. 前端配置是否正确？检查 `frontend/vite.config.ts` 中的代理设置

### 问题3: 书签创建失败

**可能原因**:
1. 未登录或Token过期 - 重新登录
2. 文档ID无效 - 确保PDF已上传成功
3. AI API错误 - 检查后端日志中的Gemini API错误

### 问题4: 测试脚本无法运行

**确保使用虚拟环境**:
```powershell
# 正确的方式
d:\IntelliPDF\backend\venv\Scripts\python.exe test_bookmark_quick.py

# 错误的方式（会使用系统Python）
python test_bookmark_quick.py
```

## 📊 测试检查清单

### 后端测试
- [ ] 健康检查端点 `/health` 返回200
- [ ] 用户注册成功
- [ ] 用户登录成功并获取token
- [ ] 创建书签成功（返回201）
- [ ] 获取书签列表
- [ ] 更新书签成功
- [ ] 搜索书签功能正常
- [ ] 删除书签成功

### 前端测试
- [ ] 页面正常加载
- [ ] PDF上传成功
- [ ] PDF显示正常
- [ ] 文本选择功能正常
- [ ] AI对话功能正常
- [ ] 生成书签按钮出现
- [ ] 书签面板显示书签列表
- [ ] 书签搜索功能正常
- [ ] 书签编辑功能正常
- [ ] 点击书签跳转到正确位置
- [ ] PDF上的书签高亮显示

### 集成测试
- [ ] 完整流程：上传PDF → 选择文本 → AI对话 → 生成书签 → 查看书签
- [ ] 书签在刷新后保持存在
- [ ] 多个书签可以同时存在
- [ ] 不同用户的书签互不干扰

## 📝 测试报告模板

```
测试时间: YYYY-MM-DD HH:MM
测试人员: [您的名字]
测试环境: Windows / Python 3.10 / Node.js v18

[✅/❌] 后端启动
[✅/❌] 前端启动
[✅/❌] 书签创建
[✅/❌] 书签管理
[✅/❌] 完整流程

遇到的问题:
1. [描述问题]
2. [描述问题]

建议改进:
1. [建议]
2. [建议]
```

## 🚀 下一步计划

测试完成后：
1. 记录所有发现的bug
2. 优化用户体验
3. 添加更多错误处理
4. 完善文档
5. 准备部署

---

**重要提示**: 
- 始终在虚拟环境中运行Python脚本
- 不要同时在多个终端运行测试脚本（会干扰后端）
- 使用独立的终端窗口运行后端和前端服务器
- 浏览器测试时打开开发者工具的Console和Network标签监控错误
