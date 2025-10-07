# IntelliPDF 前端项目启动指南

## 🚀 快速开始

### 1. 安装依赖

```bash
cd frontend
npm install
```

如果安装过程中遇到问题，尝试：
```bash
npm install --legacy-peer-deps
```

### 2. 配置环境变量

创建 `.env` 文件（已创建）：
```env
VITE_API_URL=http://localhost:8000/api/v1
```

### 3. 启动开发服务器

```bash
npm run dev
```

访问: http://localhost:3000

### 4. 构建生产版本

```bash
npm run build
npm run preview
```

## 📦 已安装依赖

核心框架：
- react 19.1.1
- react-dom 19.1.1
- react-router-dom
- @tanstack/react-query
- zustand

UI & 工具：
- tailwindcss
- postcss
- autoprefixer
- react-icons
- clsx

PDF & Markdown：
- react-pdf
- pdfjs-dist
- react-markdown
- remark-gfm
- react-syntax-highlighter

API 通信：
- axios

## 🏗️ 项目结构

```
frontend/
├── src/
│   ├── components/           # UI组件
│   │   ├── Layout.tsx        # 主布局
│   │   ├── Header.tsx        # 头部导航
│   │   └── Sidebar.tsx       # 侧边栏/抽屉
│   ├── pages/                # 页面
│   │   ├── HomePage.tsx      # 首页（文档列表）
│   │   ├── UploadPage.tsx    # 上传页面
│   │   └── DocumentViewerPage.tsx  # 文档查看器
│   ├── services/             # API服务
│   │   └── api.ts            # API客户端
│   ├── stores/               # 状态管理
│   │   └── index.ts          # Zustand stores
│   ├── hooks/                # 自定义Hooks
│   │   └── useResponsive.ts  # 响应式检测
│   ├── types/                # TypeScript类型
│   │   └── index.ts          # 类型定义
│   ├── App.tsx               # 根组件
│   ├── main.tsx              # 入口文件
│   └── index.css             # 全局样式
├── public/                   # 静态资源
├── index.html                # HTML模板
├── vite.config.ts            # Vite配置
├── tailwind.config.js        # Tailwind配置
├── tsconfig.json             # TypeScript配置
└── package.json              # 依赖配置
```

## 📱 响应式设计

### 断点
- mobile: < 768px
- tablet: 768px - 1023px
- desktop: >= 1024px

### 适配策略
- PC端：固定侧边栏 + 主内容区
- 移动端：抽屉式侧边栏 + 全屏内容

### 触摸优化
- 最小点击区域: 44x44px
- 支持手势操作
- iOS安全区域适配

## 🔧 开发命令

```bash
# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview

# 代码检查
npm run lint
```

## 🎨 使用Tailwind CSS

组件中使用Tailwind类名：
```tsx
<div className="flex items-center gap-4 p-4 bg-white rounded-lg shadow">
  <button className="btn btn-primary">
    点击我
  </button>
</div>
```

响应式设计：
```tsx
<div className="w-full md:w-1/2 lg:w-1/3">
  响应式宽度
</div>
```

## 🔌 API 调用示例

```typescript
import { apiService } from './services/api';

// 上传文档
const response = await apiService.uploadDocument(file, (progress) => {
  console.log(`上传进度: ${progress.percentage}%`);
});

// 获取文档列表
const docs = await apiService.getDocuments(1, 20);

// AI问答
const chat = await apiService.chat(documentId, {
  question: '这个文档主要讲了什么？'
});
```

## 📊 状态管理

```typescript
import { useUIStore, useDocumentStore } from './stores';

// UI状态
const { sidebarOpen, toggleSidebar } = useUIStore();

// 文档状态
const { currentDocument, setCurrentDocument } = useDocumentStore();
```

## 🐛 常见问题

### Q: npm install 卡住？
A: 使用国内镜像：
```bash
npm config set registry https://registry.npmmirror.com
npm install
```

### Q: Tailwind样式不生效？
A: 确保已运行 `npm install tailwindcss postcss autoprefixer`

### Q: 类型错误？
A: 等待依赖安装完成，然后重启VSCode

## 📝 下一步开发

- [ ] 完善PDF查看器组件
- [ ] 实现AI聊天界面
- [ ] 添加知识图谱可视化
- [ ] 实现暗黑模式
- [ ] 添加PWA支持
- [ ] 优化移动端体验

## 📄 许可

MIT License
