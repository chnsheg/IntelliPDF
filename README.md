# IntelliPDF - 智能PDF知识管理平台

> 将静态文档转化为动态、互联、可交互的知识图谱系统

## 🎯 项目愿景

IntelliPDF 致力于革新传统的PDF文档阅读和学习方式,通过AI技术实现从"被动阅读"到"主动知识探索"的范式转变。

### 核心价值主张

1. **知识网络化** - 将线性文档转化为相互关联的知识节点
2. **交互智能化** - 通过AI对话实现主动知识探索
3. **学习个性化** - 基于用户行为构建个性化知识路径
4. **复习结构化** - 通过知识图谱实现高效复习回顾

## 📁 项目结构

```
IntelliPDF/
├── backend/                    # 后端服务(FastAPI)
│   ├── app/                   # 应用代码
│   │   ├── core/             # 核心基础设施
│   │   ├── models/           # 数据模型
│   │   ├── services/         # 业务逻辑
│   │   ├── api/              # API接口
│   │   └── infrastructure/   # 基础设施
│   ├── alembic/              # 数据库迁移
│   ├── tests/                # 测试
│   ├── requirements/         # 依赖管理
│   ├── main.py              # 应用入口
│   └── README.md            # 后端文档
├── frontend/                   # 前端应用(React) [待开发]
├── docs/                      # 项目文档
├── PROJECT_TODO.md           # 开发进度跟踪
├── QUICKSTART.md            # 快速启动指南
└── README.md                # 项目总览(本文件)
```

## 🛠️ 技术架构

### 后端技术栈

- **框架**: FastAPI + Python 3.11+
- **数据库**: PostgreSQL + Redis
- **向量数据库**: ChromaDB
- **AI/ML**: LangChain + OpenAI
- **PDF处理**: PyMuPDF + pdfplumber
- **ORM**: SQLAlchemy 2.0 (异步)

### 前端技术栈 [规划中]

- **框架**: React 18 + TypeScript
- **状态管理**: Zustand
- **UI组件**: TailwindCSS + Framer Motion
- **可视化**: D3.js + React Flow
- **PDF渲染**: PDF.js

## 🚀 快速开始

### 方式一: 使用启动脚本 (推荐)

```powershell
# 1. 进入backend目录
cd backend

# 2. 运行启动脚本
.\start.bat
```

脚本将自动完成环境检查、依赖安装、数据库迁移和服务启动。

### 方式二: 手动启动

详细步骤请参考 [QUICKSTART.md](QUICKSTART.md)

## 📊 当前进度

**开发阶段**: Phase 1 - 核心基础设施  
**完成度**: 40%

### ✅ 已完成

- [x] 项目架构设计与初始化
- [x] 核心配置管理系统
- [x] 数据模型设计(Domain + Database)
- [x] 基础设施层(Database, VectorDB, FileStorage)
- [x] API框架和路由
- [x] 日志、异常、安全系统
- [x] 数据库迁移配置
- [x] 项目文档和启动脚本

### 🚧 进行中

- [ ] PDF解析引擎实现
- [ ] 语义分块算法
- [ ] AI服务集成
- [ ] 文档上传和处理API

详细进度请查看 [PROJECT_TODO.md](PROJECT_TODO.md)

## 📖 文档导航

- **[快速启动指南](QUICKSTART.md)** - 5分钟快速启动服务
- **[后端文档](backend/README.md)** - 完整的后端开发文档
- **[开发进度](PROJECT_TODO.md)** - 详细的开发任务和进度
- **[Prompt规范](prompt.txt)** - 项目开发规范和要求

## 🎨 核心功能

### Phase 1: 基础功能 (当前)

- ✅ PDF文档上传和管理
- ✅ 多格式内容提取
- 🚧 智能语义分块
- 🚧 向量化和存储

### Phase 2: 智能交互

- ⏳ 实时AI对话
- ⏳ 上下文感知问答
- ⏳ 会话历史管理
- ⏳ 智能书签生成

### Phase 3: 知识图谱

- ⏳ 概念提取和关联
- ⏳ 知识图谱可视化
- ⏳ 学习路径推荐
- ⏳ 个性化复习

### Phase 4: 高级功能

- ⏳ 代码感知和执行
- ⏳ 多文档关联分析
- ⏳ 协作学习功能
- ⏳ 知识导出和分享

## 🔧 开发环境设置

### 系统要求

- **操作系统**: Windows 10/11, macOS, Linux
- **Python**: 3.11 或更高版本
- **Node.js**: 18+ (前端开发)
- **PostgreSQL**: 14+
- **Redis**: 7+
- **内存**: 至少 8GB RAM
- **存储**: 至少 10GB 可用空间

### 开发工具推荐

- **IDE**: VS Code + Python插件
- **数据库工具**: pgAdmin 4 或 DBeaver
- **API测试**: Postman 或 Thunder Client
- **Git**: Git for Windows

## 📝 开发规范

### 代码风格

- **Python**: PEP 8 + Black formatter
- **TypeScript**: ESLint + Prettier
- **命名**: 清晰、描述性、一致性
- **注释**: Google风格docstring

### 提交规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

类型:
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建/工具

### 质量标准

- ✅ 类型检查 (mypy)
- ✅ 代码格式 (black, isort)
- ✅ 单元测试覆盖率 > 80%
- ✅ API文档完整
- ✅ 错误处理完善

## 🧪 测试

```powershell
# 运行所有测试
pytest

# 带覆盖率
pytest --cov=app --cov-report=html

# 运行特定测试
pytest tests/unit/test_parser.py
```

## 📦 部署

### 开发环境
```powershell
python main.py
```

### 生产环境
```bash
# 使用 gunicorn + uvicorn workers
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### Docker (规划中)
```bash
docker-compose up -d
```

## 🐛 问题反馈

遇到问题? 请:
1. 查看 [QUICKSTART.md](QUICKSTART.md) 常见问题
2. 查看项目文档
3. 查看日志文件 `backend/logs/`
4. 提交 Issue (包含详细信息)

## 🤝 贡献

欢迎贡献! 请遵循以下步骤:

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 遵循代码规范
4. 编写测试
5. 提交更改 (`git commit -m 'feat: Add AmazingFeature'`)
6. 推送分支 (`git push origin feature/AmazingFeature`)
7. 开启 Pull Request

## 📄 许可证

[许可证信息待定]

## 🙏 致谢

- FastAPI - 高性能Web框架
- LangChain - LLM应用开发框架
- ChromaDB - 向量数据库
- OpenAI - AI能力支持

## 📧 联系方式

- **项目**: IntelliPDF
- **团队**: IntelliPDF Development Team
- **版本**: 0.1.0 (Alpha)
- **最后更新**: 2024-01-01

---

**⚡ 现在就开始**: 查看 [QUICKSTART.md](QUICKSTART.md) 快速启动项目!

**📚 深入学习**: 查看 [backend/README.md](backend/README.md) 了解详细架构

**🎯 跟踪进度**: 查看 [PROJECT_TODO.md](PROJECT_TODO.md) 了解开发状态
