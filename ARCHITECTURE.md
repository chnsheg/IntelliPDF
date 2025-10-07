# IntelliPDF 项目架构文档

## 📐 总体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户界面层                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  PDF阅读器   │  │  AI对话界面  │  │  知识图谱    │          │
│  │  (React)     │  │  (WebSocket) │  │  (D3.js)     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ↕ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────────┐
│                         API网关层                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  FastAPI Router (CORS, Auth, Rate Limiting)              │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                         业务逻辑层                               │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  │
│  │ PDF处理   │  │ AI服务    │  │ 知识管理  │  │ 用户管理  │  │
│  │ Service   │  │ Service   │  │ Service   │  │ Service   │  │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                         数据访问层                               │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  │
│  │Repository │  │Repository │  │Repository │  │Repository │  │
│  │ (Document)│  │ (Chunk)   │  │(Knowledge)│  │  (User)   │  │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                         存储层                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │PostgreSQL│  │ ChromaDB │  │  Redis   │  │LocalFile │      │
│  │(关系数据)│  │(向量数据)│  │  (缓存)  │  │ Storage  │      │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                         外部服务                                 │
│  ┌──────────────┐              ┌──────────────┐               │
│  │  OpenAI API  │              │  其他AI服务  │               │
│  │(GPT-4, Embed)│              │   (可选)     │               │
│  └──────────────┘              └──────────────┘               │
└─────────────────────────────────────────────────────────────────┘
```

## 🏗️ 后端分层架构

### 1. 核心层 (Core)

**职责**: 提供跨层次的基础设施和工具

```
app/core/
├── config.py          # 配置管理(Pydantic Settings)
├── logging.py         # 结构化日志(Loguru)
├── exceptions.py      # 异常体系
├── dependencies.py    # 依赖注入
└── security.py        # 安全工具(JWT, Hash)
```

**设计原则**:
- 单例模式 (配置)
- 依赖注入 (FastAPI Depends)
- 分层异常 (业务 → 技术)

### 2. 模型层 (Models)

**职责**: 定义数据结构和验证规则

```
app/models/
├── domain/            # 领域模型(业务逻辑)
│   ├── document.py   # 文档领域模型
│   ├── chunk.py      # 分块领域模型
│   └── knowledge.py  # 知识图谱模型
└── db/               # 数据库模型(持久化)
    ├── base.py       # Base + Mixins
    └── models.py     # SQLAlchemy模型
```

**设计原则**:
- 领域驱动设计 (DDD)
- 业务逻辑与持久化分离
- Pydantic验证

### 3. 服务层 (Services)

**职责**: 实现核心业务逻辑

```
app/services/
├── pdf/              # PDF处理服务
│   ├── parser.py     # PDF解析
│   ├── extraction.py # 内容提取
│   └── chunking.py   # 智能分块
├── ai/               # AI服务
│   ├── llm.py        # 大语言模型
│   ├── embeddings.py # 向量嵌入
│   └── retrieval.py  # 检索增强
└── knowledge/        # 知识管理
    ├── graph.py      # 知识图谱
    ├── bookmarks.py  # 书签管理
    └── analysis.py   # 内容分析
```

**设计模式**:
- 策略模式 (多种PDF解析器)
- 工厂模式 (服务实例化)
- 责任链模式 (处理管道)

### 4. API层 (API)

**职责**: 暴露HTTP接口

```
app/api/
└── v1/
    ├── endpoints/
    │   ├── documents.py  # 文档CRUD
    │   ├── chat.py       # 对话接口
    │   ├── bookmarks.py  # 书签接口
    │   └── health.py     # 健康检查
    ├── dependencies/
    │   ├── database.py   # DB依赖
    │   ├── auth.py       # 认证依赖
    │   └── validation.py # 验证依赖
    └── router.py         # 路由聚合
```

**设计原则**:
- RESTful规范
- 标准化响应格式
- 自动API文档

### 5. 基础设施层 (Infrastructure)

**职责**: 提供技术基础设施

```
app/infrastructure/
├── database/
│   └── session.py    # 数据库会话管理
├── vector_db/
│   └── client.py     # ChromaDB客户端
└── file_storage/
    └── local.py      # 本地文件存储
```

**设计模式**:
- 仓储模式 (Repository)
- 单例模式 (连接池)
- 适配器模式 (存储抽象)

## 🔄 数据流示例

### PDF上传和处理流程

```
1. 用户上传PDF
   ↓
2. API接收请求 (documents.py)
   ↓
3. 文件验证和存储 (LocalFileStorage)
   ↓
4. 创建Document记录 (DocumentRepository)
   ↓
5. 异步任务: PDF解析 (PDFParser)
   ↓
6. 内容提取 (ContentExtractor)
   ├─ 文本提取
   ├─ 图像提取
   ├─ 表格提取
   └─ 代码提取
   ↓
7. 智能分块 (SemanticChunker)
   ├─ 结构化分块
   ├─ 语义分块
   └─ 质量评估
   ↓
8. 生成向量嵌入 (EmbeddingService)
   ↓
9. 存储到ChromaDB (VectorRepository)
   ↓
10. 更新Document状态
   ↓
11. 返回处理结果
```

### AI对话流程

```
1. 用户发送问题
   ↓
2. WebSocket接收 (chat.py)
   ↓
3. 向量检索相关内容 (RetrievalService)
   ├─ 查询向量化
   ├─ 相似度搜索
   └─ 重排序
   ↓
4. 构建上下文 (ContextBuilder)
   ↓
5. 调用LLM (LLMService)
   ├─ Prompt工程
   ├─ 流式生成
   └─ Token管理
   ↓
6. 存储对话历史 (ChatRepository)
   ↓
7. 流式返回响应
```

## 📦 模块依赖关系

```
┌─────────────────────┐
│    API Layer        │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│   Service Layer     │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│  Repository Layer   │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│Infrastructure Layer │
└─────────────────────┘

横向依赖:
Core ← → 所有层
Models ← → Service, Repository
```

**依赖规则**:
- ✅ 上层可依赖下层
- ❌ 下层不可依赖上层
- ✅ 同层模块间低耦合
- ✅ 通过接口/抽象依赖

## 🔐 安全架构

```
┌─────────────────────────────────────┐
│          安全层                      │
├─────────────────────────────────────┤
│  认证: JWT Token                     │
│  授权: RBAC (Role-Based)             │
│  加密: Bcrypt (密码)                 │
│  验证: Pydantic (输入)                │
│  限流: Redis (Rate Limiting)         │
│  CORS: 白名单配置                    │
└─────────────────────────────────────┘
```

## 📈 性能优化策略

### 1. 数据库层
- 连接池管理 (SQLAlchemy Pool)
- 查询优化 (索引, N+1)
- 异步操作 (asyncpg)

### 2. 缓存层
- Redis缓存 (热数据)
- 应用级缓存 (LRU)
- HTTP缓存 (ETag)

### 3. 应用层
- 异步IO (asyncio)
- 批处理 (Batch Processing)
- 流式响应 (Streaming)

### 4. 外部服务
- 连接复用 (httpx)
- 重试机制 (tenacity)
- 熔断器 (Circuit Breaker)

## 🧪 测试策略

```
tests/
├── unit/              # 单元测试
│   ├── test_parser.py
│   ├── test_chunker.py
│   └── test_embeddings.py
├── integration/       # 集成测试
│   ├── test_api.py
│   ├── test_db.py
│   └── test_vectordb.py
└── fixtures/          # 测试数据
    ├── sample.pdf
    └── test_data.json
```

**测试金字塔**:
- 70% 单元测试 (快速, 隔离)
- 20% 集成测试 (真实场景)
- 10% E2E测试 (关键流程)

## 📊 监控和日志

### 日志级别
- **DEBUG**: 开发调试信息
- **INFO**: 正常运行日志
- **WARNING**: 警告信息
- **ERROR**: 错误信息
- **CRITICAL**: 严重错误

### 日志格式
```json
{
  "timestamp": "2024-01-01T10:00:00.000Z",
  "level": "INFO",
  "logger": "app.services.pdf.parser",
  "function": "parse_document",
  "line": 42,
  "message": "PDF parsing started",
  "context": {
    "document_id": "123e4567-...",
    "file_size": 1048576
  }
}
```

### 监控指标
- 请求延迟 (P50, P95, P99)
- 错误率
- 吞吐量
- 数据库连接数
- 缓存命中率

## 🔧 配置管理

### 环境层次
```
.env.local          # 本地覆盖(不提交)
.env.development    # 开发环境
.env.staging        # 测试环境
.env.production     # 生产环境
```

### 配置优先级
```
环境变量 > .env.local > .env.{environment} > 默认值
```

---

**文档维护者**: IntelliPDF Architecture Team  
**最后更新**: 2024-01-01  
**版本**: 1.0
