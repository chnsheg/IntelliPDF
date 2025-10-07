# IntelliPDF Backend

下一代智能PDF知识管理平台 - 后端服务

## 📋 项目概述

IntelliPDF 是一个创新的PDF知识管理平台,通过AI技术将静态文档转化为动态、互联、可交互的知识图谱系统。本仓库包含后端API服务,基于FastAPI构建,提供文档处理、AI对话、知识图谱等核心功能。

## 🎯 核心特性

- **智能PDF解析**: 多格式内容提取(文本、图像、代码、表格、公式)
- **语义分块**: AI驱动的智能内容分块和主题提取
- **向量检索**: 基于ChromaDB的高效相似性搜索
- **知识图谱**: 自动构建概念关联和学习路径
- **AI对话**: 基于LangChain的智能文档问答
- **异步架构**: 高性能异步处理和并发支持

## 🛠️ 技术栈

### 核心框架
- **Python 3.11+**: 现代Python特性和类型提示
- **FastAPI**: 高性能异步Web框架
- **SQLAlchemy 2.0**: 异步ORM和数据库操作
- **Pydantic V2**: 数据验证和设置管理

### 数据存储
- **PostgreSQL**: 主数据库(文档、分块、知识图谱)
- **ChromaDB**: 向量数据库(语义检索)
- **Redis**: 缓存和会话管理

### AI/ML
- **LangChain**: LLM应用框架
- **OpenAI API**: GPT-4和Embeddings
- **spaCy**: 自然语言处理

### PDF处理
- **PyMuPDF**: 高性能PDF解析
- **pdfplumber**: 表格和结构提取
- **pdf2image**: PDF渲染

## 🚀 快速开始

### 前置要求

- Python 3.11 或更高版本
- PostgreSQL 14+
- Redis 7+
- OpenAI API Key

### 安装步骤

1. **克隆仓库**
```bash
git clone <repository-url>
cd IntelliPDF/backend
```

2. **创建虚拟环境**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **安装依赖**
```bash
# 开发环境
pip install -r requirements/dev.txt

# 生产环境
pip install -r requirements/prod.txt
```

4. **配置环境变量**
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件,设置必要的配置
# 特别是:
# - DATABASE_URL
# - OPENAI_API_KEY
# - SECRET_KEY
```

5. **初始化数据库**
```bash
# 创建数据库
psql -U postgres -c "CREATE DATABASE intellipdf;"

# 运行迁移
alembic upgrade head
```

6. **启动服务**
```bash
# 开发模式(热重载)
python main.py

# 或使用 uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

7. **访问API文档**
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## 📁 项目结构

```
backend/
├── app/
│   ├── core/                 # 核心基础设施
│   │   ├── config.py        # 配置管理
│   │   ├── logging.py       # 日志系统
│   │   ├── exceptions.py    # 异常定义
│   │   ├── dependencies.py  # 依赖注入
│   │   └── security.py      # 安全认证
│   ├── models/              # 数据模型
│   │   ├── domain/          # 领域模型
│   │   │   ├── document.py
│   │   │   ├── chunk.py
│   │   │   └── knowledge.py
│   │   └── db/              # 数据库模型
│   │       ├── base.py
│   │       └── models.py
│   ├── services/            # 业务逻辑层
│   │   ├── pdf/            # PDF处理服务
│   │   ├── ai/             # AI集成服务
│   │   └── knowledge/      # 知识管理服务
│   ├── api/                # API接口层
│   │   └── v1/
│   │       ├── endpoints/
│   │       └── router.py
│   └── infrastructure/     # 基础设施层
│       ├── database/       # 数据库连接
│       ├── vector_db/      # 向量数据库
│       └── file_storage/   # 文件存储
├── alembic/                # 数据库迁移
├── tests/                  # 测试目录
├── requirements/           # 依赖管理
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
├── main.py                 # 应用入口
├── alembic.ini            # Alembic配置
└── .env.example           # 环境变量模板
```

## 🔧 配置说明

### 必需配置

1. **数据库连接**
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/intellipdf
```

2. **OpenAI API**
```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
```

3. **安全密钥**
```env
SECRET_KEY=your-secret-key-minimum-32-characters
```

### 可选配置

- `CHROMA_DB_PATH`: ChromaDB存储路径
- `UPLOAD_DIR`: 文件上传目录
- `MAX_FILE_SIZE`: 最大文件大小限制
- `CHUNK_SIZE`: 文本分块大小
- `LOG_LEVEL`: 日志级别

## 🧪 开发指南

### 代码质量

项目遵循严格的代码质量标准:

```bash
# 类型检查
mypy --strict app/

# 代码格式化
black app/ tests/
isort app/ tests/

# 代码检查
flake8 app/ tests/
pylint app/
```

### 数据库迁移

```bash
# 创建新迁移
alembic revision --autogenerate -m "描述"

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1

# 查看迁移历史
alembic history
```

### 运行测试

```bash
# 运行所有测试
pytest

# 带覆盖率报告
pytest --cov=app --cov-report=html

# 运行特定测试
pytest tests/unit/test_pdf_parser.py
```

## 🌐 API端点

### 健康检查
- `GET /health` - 系统健康状态

### 文档管理
- `GET /api/v1/documents` - 列出所有文档
- `POST /api/v1/documents` - 上传新文档
- `GET /api/v1/documents/{id}` - 获取文档详情
- `DELETE /api/v1/documents/{id}` - 删除文档

### 对话系统
- `POST /api/v1/chat/sessions` - 创建对话会话
- `POST /api/v1/chat/messages` - 发送消息
- `GET /api/v1/chat/sessions/{id}` - 获取会话历史

### 知识图谱
- `GET /api/v1/knowledge/graph/{document_id}` - 获取知识图谱
- `POST /api/v1/knowledge/learning-path` - 生成学习路径

详细API文档请访问 `/api/docs`

## 📊 性能指标

项目设计目标:

- **PDF解析**: < 30秒 (100页文档)
- **向量检索**: Recall@5 > 0.85
- **AI响应**: P95 < 4.5秒
- **并发支持**: ≥ 200活跃会话

## 🔒 安全性

- JWT身份认证
- CORS跨域配置
- 输入验证和清理
- SQL注入防护
- 文件上传限制

## 📝 日志记录

日志存储在 `./logs/` 目录:

- `intellipdf_YYYY-MM-DD.log` - 常规日志
- `errors_YYYY-MM-DD.log` - 错误日志

日志自动轮转,保留30天(错误日志90天)

## 🐛 故障排除

### 数据库连接失败
```bash
# 检查PostgreSQL服务状态
systemctl status postgresql

# 验证连接
psql -U postgres -d intellipdf -c "SELECT 1;"
```

### ChromaDB错误
```bash
# 清理ChromaDB数据
rm -rf ./data/chroma_db/*
```

### 依赖冲突
```bash
# 重新创建虚拟环境
deactivate
rm -rf venv/
python -m venv venv
source venv/bin/activate
pip install -r requirements/dev.txt
```

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

[许可证信息待定]

## 📧 联系方式

项目维护者: IntelliPDF Team

---

**当前版本**: 0.1.0  
**开发阶段**: Phase 1 - 核心基础设施  
**最后更新**: 2024-01-01
