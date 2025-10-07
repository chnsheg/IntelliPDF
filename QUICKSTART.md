# IntelliPDF 快速启动指南

本指南将帮助您在5分钟内启动IntelliPDF后端服务。

## 前置条件检查

在开始之前,请确保您已安装:

- ✅ Python 3.11+
- ✅ PostgreSQL 14+
- ✅ Redis 7+
- ✅ Git

## 快速启动步骤

### 1. 安装Python依赖

```powershell
# 进入backend目录
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
.\venv\Scripts\activate

# 安装开发依赖
pip install -r requirements\dev.txt
```

### 2. 配置环境变量

```powershell
# 复制环境变量模板
copy .env.example .env

# 使用你喜欢的编辑器打开.env文件
notepad .env
```

**必须配置的环境变量**:

```env
# 数据库连接
DATABASE_URL=postgresql+asyncpg://postgres:你的密码@localhost:5432/intellipdf

# OpenAI API Key
OPENAI_API_KEY=sk-你的OpenAI密钥

# 安全密钥(至少32字符)
SECRET_KEY=请生成一个随机的32字符以上的密钥
```

### 3. 创建数据库

```powershell
# 连接到PostgreSQL并创建数据库
psql -U postgres

# 在psql中执行
CREATE DATABASE intellipdf;
\q
```

### 4. 运行数据库迁移

```powershell
# 确保在backend目录且虚拟环境已激活
alembic upgrade head
```

### 5. 启动服务

```powershell
# 开发模式启动
python main.py
```

服务将在 http://localhost:8000 启动。

### 6. 验证安装

打开浏览器访问:

- **API文档**: http://localhost:8000/api/docs
- **健康检查**: http://localhost:8000/health

## 常见问题

### Q: 导入模块错误?
A: 确保虚拟环境已激活,并且在backend目录下。

### Q: 数据库连接失败?
A: 检查PostgreSQL服务是否运行,以及DATABASE_URL配置是否正确。

### Q: OpenAI API错误?
A: 验证OPENAI_API_KEY是否正确,并且有足够的配额。

### Q: 端口被占用?
A: 在.env中修改API_PORT为其他端口。

## 下一步

- 查看 [README.md](README.md) 了解完整文档
- 查看 [PROJECT_TODO.md](../PROJECT_TODO.md) 了解开发进度
- 访问 API文档开始探索接口

## 开发工作流

```powershell
# 代码格式化
black app/ tests/
isort app/ tests/

# 类型检查
mypy --strict app/

# 运行测试
pytest

# 创建数据库迁移
alembic revision --autogenerate -m "描述变更"

# 应用迁移
alembic upgrade head
```

## 获取帮助

如遇到问题,请:
1. 查看日志文件: `./logs/`
2. 检查项目文档
3. 提交Issue

---

祝开发愉快! 🚀
