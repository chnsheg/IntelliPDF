# IntelliPDF 功能改进计划

## 版本: v1.1
## 日期: 2025-10-07
## 目标: 解决当前问题并完善核心功能

---

## 📋 当前问题总结

### 1. PDF阅读体验问题
**现状**:
- PDF每页显示不全，需要滚动才能看到完整内容
- 缺乏沉浸式阅读模式
- 不支持翻页/滚动两种阅读方式切换
- 无快捷键支持

**目标**:
- 实现类似Kindle的沉浸式阅读体验
- 支持翻页模式(Page Mode)和滚动模式(Scroll Mode)
- 添加快捷键: 方向键翻页、空格翻页、滚轮滚动
- 最大化阅读区域，同时保持AI辅助功能可访问

### 2. PDF分块功能缺失
**现状**:
- 后端已实现智能分块，但前端不可见
- 用户无法看到文档的语义结构
- AI对话时未使用当前分块上下文

**目标**:
- 在PDF渲染时显示分块边界(可选显示/隐藏)
- 高亮当前阅读位置所在分块
- AI对话时自动使用当前分块作为上下文
- 提供分块导航功能

### 3. 书签系统不完善
**需求理解** (基于prompt.txt):
- 会话驱动的知识点书签生成
- 书签应包含: 位置、内容摘要、AI对话记录、标签
- 支持手动创建和AI自动生成
- 书签可视化和快速跳转

**当前状态**: 基础API已有,需要完善前后端实现

### 4. 用户认证缺失
**问题**:
- 所有配置(API密钥等)硬编码或存储在前端
- 无法支持多用户
- 安全风险

**目标**:
- 实现JWT认证系统
- 用户注册/登录/登出
- 每个用户独立的文档和书签数据
- API密钥等敏感信息存储在后端

---

## 🎯 实施计划

### Phase 1: 沉浸式PDF阅读器 (预计1周)

#### 1.1 后端API增强
**文件**: `backend/app/api/v1/endpoints/documents.py`

新增API:
```python
GET /api/v1/documents/{doc_id}/chunks
  # 返回文档所有分块的位置信息和边界框

GET /api/v1/documents/{doc_id}/chunks/{chunk_id}
  # 获取特定分块的详细内容

POST /api/v1/documents/{doc_id}/current-context
  # 根据当前阅读位置(页码+坐标)获取相关分块上下文
```

#### 1.2 前端阅读器重构
**文件**: `frontend/src/components/PDFViewer.tsx`

新功能:
- [ ] 添加阅读模式切换器 (翻页/滚动)
- [ ] 实现全页适配显示
- [ ] 沉浸式模式 (F11/Esc切换)
- [ ] 快捷键支持:
  - `→` / `PageDown` / `Space`: 下一页
  - `←` / `PageUp` / `Shift+Space`: 上一页
  - `Home` / `End`: 首页/末页
  - `F11`: 全屏切换
  - `Ctrl+D`: 切换分块边界显示

#### 1.3 分块可视化
**新组件**: `frontend/src/components/ChunkOverlay.tsx`

功能:
- 在PDF页面上绘制分块边界框
- 高亮当前分块
- 点击分块显示详情
- 分块缩略导航

#### 1.4 AI上下文集成
**文件**: `frontend/src/components/ChatPanel.tsx`

改进:
- 自动检测用户当前阅读位置
- 发送AI请求时附加当前分块上下文
- 显示使用的上下文来源

---

### Phase 2: 智能书签系统 (预计5天)

#### 2.1 数据库模型
**文件**: `backend/app/models/db/models_simple.py`

```python
class BookmarkModel(Base):
    """书签模型"""
    id: UUID
    document_id: UUID
    user_id: UUID  # 需要用户系统
    title: str  # 书签标题
    description: str  # 描述/笔记
    chunk_ids: List[UUID]  # 关联的分块
    page_number: int  # 页码
    bounding_box: Dict  # 位置
    tags: List[str]  # 标签
    created_from_chat: bool  # 是否来自AI对话
    chat_session_id: UUID  # 关联的对话会话
    importance_score: float  # 重要性评分
    created_at: datetime
    updated_at: datetime
```

#### 2.2 书签API
**文件**: `backend/app/api/v1/endpoints/bookmarks.py`

```python
POST /api/v1/documents/{doc_id}/bookmarks
  # 创建书签

GET /api/v1/documents/{doc_id}/bookmarks
  # 获取文档所有书签

PUT /api/v1/bookmarks/{bookmark_id}
  # 更新书签

DELETE /api/v1/bookmarks/{bookmark_id}
  # 删除书签

POST /api/v1/bookmarks/generate
  # AI自动生成书签 (基于对话历史)
```

#### 2.3 前端书签UI
**新组件**: `frontend/src/components/BookmarkPanel.tsx`

功能:
- 书签列表展示
- 快速跳转到书签位置
- 书签编辑/删除
- 标签过滤
- AI生成书签按钮

---

### Phase 3: 用户认证系统 (预计1周)

#### 3.1 后端认证服务
**新文件**: `backend/app/services/auth/`

```
auth/
├── __init__.py
├── auth_service.py      # 认证核心逻辑
├── jwt_handler.py       # JWT token生成验证
└── password_handler.py  # 密码加密验证
```

核心功能:
- 用户注册/登录
- JWT token生成和验证
- 密码bcrypt加密
- Token刷新机制

#### 3.2 用户数据模型
**文件**: `backend/app/models/db/models_simple.py`

```python
class UserModel(Base):
    """用户模型"""
    id: UUID
    username: str  # 唯一用户名
    email: str  # 邮箱
    password_hash: str  # 密码哈希
    full_name: str
    is_active: bool
    is_superuser: bool
    gemini_api_key: str  # 用户自己的API密钥
    gemini_base_url: str
    created_at: datetime
    last_login: datetime
```

#### 3.3 认证API
**新文件**: `backend/app/api/v1/endpoints/auth.py`

```python
POST /api/v1/auth/register
  # 用户注册

POST /api/v1/auth/login
  # 用户登录,返回access_token

POST /api/v1/auth/refresh
  # 刷新token

POST /api/v1/auth/logout
  # 登出

GET /api/v1/auth/me
  # 获取当前用户信息

PUT /api/v1/auth/me
  # 更新用户信息(包括API密钥)
```

#### 3.4 前端认证集成
**新页面**: 
- `frontend/src/pages/LoginPage.tsx`
- `frontend/src/pages/RegisterPage.tsx`
- `frontend/src/pages/ProfilePage.tsx`

**认证拦截器**: `frontend/src/services/api.ts`
```typescript
// 添加JWT token到所有请求
// 401错误自动跳转登录页
// Token刷新逻辑
```

**状态管理**: `frontend/src/stores/authStore.ts`
```typescript
interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  register: (data: RegisterData) => Promise<void>;
}
```

#### 3.5 权限中间件
**文件**: `backend/app/core/dependencies.py`

```python
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> UserModel:
    """验证JWT token并返回当前用户"""
    # 验证token
    # 查询用户
    # 返回用户或抛出401异常
```

应用到所有需要认证的API端点:
```python
@router.get("/documents")
async def list_documents(
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 只返回当前用户的文档
    pass
```

---

## 📊 数据库迁移

### 新增表
1. `users` - 用户表
2. `bookmarks` - 书签表
3. 修改 `documents` 表,添加 `user_id` 外键
4. 修改 `chunks` 表,添加额外元数据字段

### 迁移命令
```bash
cd backend
alembic revision --autogenerate -m "add_user_and_bookmark_models"
alembic upgrade head
```

---

## 🧪 测试计划

### 单元测试
- [ ] 用户认证服务测试
- [ ] JWT token生成验证测试
- [ ] 书签CRUD测试
- [ ] 分块上下文提取测试

### 集成测试
- [ ] 端到端认证流程
- [ ] PDF上传+分块+AI对话完整流程
- [ ] 书签创建和跳转
- [ ] 沉浸式阅读器所有模式

### 性能测试
- [ ] 大PDF(500+页)分块可视化性能
- [ ] 并发用户认证负载测试
- [ ] AI上下文检索响应时间

---

## 🚀 部署计划

### 环境变量更新
需要添加到 `.env`:
```env
# JWT配置
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# 用户系统
ALLOW_REGISTRATION=true
REQUIRE_EMAIL_VERIFICATION=false
DEFAULT_USER_QUOTA_GB=10
```

### 依赖更新
```bash
# 后端新增依赖
pip install python-jose[cryptography] passlib[bcrypt] python-multipart

# 前端新增依赖
npm install jwt-decode @tanstack/react-query zustand
```

---

## 📝 文档更新

需要更新的文档:
1. `README.md` - 添加用户认证说明
2. `ARCHITECTURE.md` - 更新架构图,包含认证层
3. `API.md` - 新API端点文档
4. `USER_GUIDE.md` - 用户使用指南

---

## ⚠️ 风险和注意事项

### 安全风险
1. **密码存储**: 必须使用bcrypt,禁止明文
2. **JWT密钥**: 生产环境必须使用强随机密钥
3. **API密钥**: 用户的Gemini密钥必须加密存储
4. **SQL注入**: 使用ORM参数化查询

### 性能风险
1. **分块可视化**: 大PDF可能导致渲染性能下降
   - 解决: 虚拟滚动,仅渲染可见分块边界
2. **JWT验证**: 每个请求都验证token
   - 解决: 使用Redis缓存用户会话
3. **AI上下文**: 大分块可能超过token限制
   - 解决: 智能截断,优先关键句子

### 兼容性风险
1. **数据库迁移**: 现有数据需要关联到默认用户
2. **前端状态**: 登录状态需持久化到localStorage
3. **API变更**: 所有端点需要认证,需要版本兼容

---

## 📅 时间线 (预计3周)

### Week 1: PDF阅读器重构
- Day 1-2: 后端分块API
- Day 3-4: 前端阅读器重构
- Day 5: 分块可视化
- Day 6-7: AI上下文集成+测试

### Week 2: 书签系统
- Day 8-9: 数据库模型+迁移
- Day 10-11: 后端书签API
- Day 12-13: 前端书签UI
- Day 14: AI自动书签生成

### Week 3: 用户认证
- Day 15-16: 后端认证服务
- Day 17-18: 前端认证UI
- Day 19: 权限中间件+数据隔离
- Day 20-21: 集成测试+修复

---

## ✅ 验收标准

### Phase 1: PDF阅读器
- [ ] 可以翻页/滚动两种模式阅读
- [ ] 快捷键完全可用
- [ ] 分块边界清晰可见
- [ ] AI对话使用正确的分块上下文
- [ ] 性能: 500页PDF渲染<3秒

### Phase 2: 书签系统
- [ ] 可以手动创建书签
- [ ] AI可以基于对话生成书签
- [ ] 书签跳转准确
- [ ] 支持标签过滤
- [ ] 书签数据持久化

### Phase 3: 用户认证
- [ ] 用户可以注册登录
- [ ] JWT token正确验证
- [ ] 每个用户数据隔离
- [ ] 用户可以配置自己的API密钥
- [ ] 登出后无法访问受保护资源

---

## 🎓 学习资源

开发过程中需要参考:
1. FastAPI Security: https://fastapi.tiangolo.com/tutorial/security/
2. JWT Best Practices: https://tools.ietf.org/html/rfc8725
3. React Query Auth: https://tanstack.com/query/latest/docs/react/examples/auth
4. PDF.js API: https://mozilla.github.io/pdf.js/

---

**下一步**: 开始实施Phase 1 - 沉浸式PDF阅读器
