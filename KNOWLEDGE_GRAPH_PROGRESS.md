# 知识图谱可视化开发报告

## 📅 开发时间
**2025年10月7日** - IntelliPDF v2.0 Phase 3

---

## 🎯 开发目标
实现知识图谱可视化功能，展示文档之间的关系和知识结构。

---

## ✅ 已完成功能

### 1. 前端知识图谱页面 (KnowledgeGraphPage.tsx)
**文件**: `frontend/src/pages/KnowledgeGraphPage.tsx` (350+ 行)

#### 核心功能
- ✅ **React Flow 集成**: 使用 reactflow 库实现交互式图谱
- ✅ **自定义节点类型**: 
  - `DocumentNode`: 文档节点（渐变背景、阴影效果）
  - `EntityNode`: 实体节点（白色背景、边框样式）
- ✅ **多种布局算法**:
  - 横向布局 (horizontal)
  - 纵向布局 (vertical)
  - 环形布局 (circular)
- ✅ **交互式控件**:
  - 缩放控制 (Controls)
  - 小地图 (MiniMap)
  - 背景网格 (Background with dots)
  - 节点拖拽
  - 连接线动画

#### UI 组件
```typescript
// 布局切换按钮组
- 横向 / 纵向 / 环形

// 工具栏
- 小地图开关
- 刷新按钮
- 导出按钮（待实现）

// 统计面板（底部）
- 节点数量
- 连接数量
- 节点类型图例
```

#### 技术亮点
- **TanStack Query**: 数据获取和缓存
- **TypeScript 类型安全**: 所有参数和回调完整类型
- **响应式设计**: 全屏布局适配
- **Fluent Design**: 渐变、阴影、圆角统一设计语言

---

### 2. 后端知识图谱 API (knowledge_graph.py)
**文件**: `backend/app/api/v1/endpoints/knowledge_graph.py` (140+ 行)

#### API 端点

##### 1. GET `/knowledge-graph/graph-data`
**功能**: 获取图谱数据（节点和边）
```python
参数:
- limit: int (默认 50) - 返回的最大节点数

返回:
{
  "nodes": [
    {
      "id": "doc123",
      "label": "文档标题",
      "type": "document",
      "pages": 25,
      "size": 1024000,
      "created_at": "2025-10-07T10:00:00"
    }
  ],
  "edges": [
    {
      "id": "e123-456",
      "source": "doc123",
      "target": "doc456",
      "type": "similar",
      "weight": 0.75
    }
  ],
  "stats": {
    "total_nodes": 10,
    "total_edges": 15,
    "avg_connections": 1.5
  }
}
```

##### 2. GET `/knowledge-graph/entities`
**功能**: 获取文档中的实体
```python
参数:
- document_id: str - 文档 ID

返回:
{
  "document_id": "doc123",
  "entities": [
    {"id": "e1", "label": "机器学习", "type": "concept", "frequency": 15}
  ],
  "total": 3
}
```

##### 3. GET `/knowledge-graph/relationships`
**功能**: 获取实体关系
```python
参数:
- entity_id: str - 实体 ID

返回:
{
  "entity_id": "e1",
  "relationships": [
    {"from": "e1", "to": "e2", "type": "related_to", "strength": 0.85}
  ],
  "total": 2
}
```

##### 4. POST `/knowledge-graph/analyze`
**功能**: 触发文档图谱分析
```python
参数:
- document_id: str - 文档 ID

返回:
{
  "document_id": "doc123",
  "status": "analysis_queued",
  "message": "Graph analysis started..."
}
```

---

### 3. API 服务集成
**文件**: `frontend/src/services/api.ts`

新增方法:
```typescript
// 获取图谱数据
async getGraphData(limit: number = 50)

// 获取文档实体
async getDocumentEntities(documentId: string)

// 获取实体关系
async getEntityRelationships(entityId: string)

// 分析文档图谱
async analyzeDocumentGraph(documentId: string)
```

---

### 4. 路由和导航
**更新文件**:
- `frontend/src/App.tsx`: 添加 `/knowledge-graph` 路由
- `frontend/src/components/Sidebar.tsx`: 已包含知识图谱导航链接

**访问地址**: http://localhost:5174/knowledge-graph

---

## 📦 依赖更新

### 前端
```bash
npm install reactflow
```
新增依赖:
- `reactflow@11.x`: React Flow 图谱可视化库
- 包含: 节点、边、控件、背景、小地图等组件

### 后端
```bash
pip install --upgrade "fastapi[standard]>=0.115.0"
```
升级依赖:
- `fastapi`: 0.92.0 → 0.118.0 (兼容 Pydantic 2)
- `starlette`: 0.25.0 → 0.48.0
- 新增: `python-multipart`, `email-validator`, `fastapi-cli`

---

## 🎨 设计特点

### 视觉设计
- **文档节点**: 渐变背景（蓝紫色系）+ 白色半透明图标框
- **实体节点**: 白色背景 + 彩色边框
- **连接线**: 蓝色动画线条
- **布局**: 三种算法自动计算节点位置
- **小地图**: 节点颜色区分，半透明遮罩

### 交互设计
- **拖拽**: 节点可自由拖动调整位置
- **缩放**: 鼠标滚轮 / 控件按钮
- **平移**: 拖动画布背景
- **动画**: 连接线流动效果

---

## ⚙️ 技术实现

### 布局算法
```typescript
function calculateNodePosition(
  index: number, 
  total: number, 
  layout: 'horizontal' | 'vertical' | 'circular'
) {
  // 横向: 5 列网格布局
  // 纵向: 5 行网格布局
  // 环形: 圆形分布算法 (2πr)
}
```

### 数据流
```
API (/knowledge-graph/graph-data)
  ↓
TanStack Query (缓存 + 自动刷新)
  ↓
useEffect (生成 React Flow 节点和边)
  ↓
React Flow (渲染和交互)
```

---

## 🐛 已知问题

### 1. 后端启动问题 ⚠️
**症状**: 后端服务启动后立即关闭
```
INFO: Application startup complete.
INFO: Shutting down
INFO: Application shutdown complete.
```

**可能原因**:
- 数据库连接问题
- 异步上下文管理器错误
- FastAPI 升级后的兼容性问题

**待解决**: 需要调试 `main.py` 的 lifespan 事件

### 2. Mock 数据 📝
**当前状态**: 图谱关系使用模拟数据
```python
# Mock similarity condition
if (i + j) % 3 == 0:
    create_edge(doc1, doc2)
```

**待实现**:
- 基于 embeddings 的真实相似度计算
- LLM 提取的实体关系
- 引用链接分析

---

## 🔮 下一步计划

### Phase 3.1: 修复后端启动 🔧
- [ ] 调试并修复后端服务启动问题
- [ ] 确保所有 API 端点可正常访问
- [ ] 测试知识图谱数据获取

### Phase 3.2: 真实数据集成 📊
- [ ] 实现文档相似度计算（基于 embeddings）
- [ ] 集成 LLM 进行实体提取
- [ ] 分析文档引用和交叉引用

### Phase 3.3: 高级功能 🚀
- [ ] 导出图谱为 PNG/SVG
- [ ] 节点点击展开详情
- [ ] 搜索和高亮功能
- [ ] 图谱保存和加载
- [ ] 多文档联合分析

### Phase 3.4: 性能优化 ⚡
- [ ] 大规模图谱虚拟化渲染
- [ ] 懒加载和分页
- [ ] WebWorker 计算布局
- [ ] Canvas 渲染优化

---

## 📊 代码统计

### 新增文件
```
frontend/src/pages/KnowledgeGraphPage.tsx     350 lines
backend/app/api/v1/endpoints/knowledge_graph.py  140 lines
---
总计                                          490 lines
```

### 修改文件
```
frontend/src/App.tsx                    +3 lines (路由)
frontend/src/services/api.ts            +20 lines (API)
backend/app/api/v1/router.py            +5 lines (注册)
---
总修改                                   +28 lines
```

---

## 🧪 测试清单

### 前端
- [x] KnowledgeGraphPage 组件渲染
- [x] React Flow 依赖安装
- [x] TypeScript 编译通过
- [ ] 布局算法正确性
- [ ] 用户交互响应
- [ ] 空数据状态显示

### 后端
- [x] knowledge_graph.py 端点创建
- [x] 路由注册成功
- [ ] API 响应数据格式
- [ ] 数据库查询性能
- [ ] 错误处理覆盖

### 集成
- [ ] 前后端数据流通
- [ ] API 调用成功率
- [ ] 图谱渲染性能
- [ ] 实时更新机制

---

## 💡 技术亮点总结

1. **React Flow**: 专业级图谱可视化库，功能强大
2. **自定义节点**: 完全控制节点样式和交互
3. **多种布局**: 灵活的布局算法适应不同场景
4. **TypeScript**: 完整类型安全保障
5. **模块化设计**: API 和组件清晰分离
6. **Fluent Design**: 统一的现代化视觉语言

---

## 📝 下次迭代建议

1. **优先修复后端启动问题** - 阻塞所有功能测试
2. **实现真实相似度计算** - 提升图谱价值
3. **添加实体提取功能** - 深化知识挖掘
4. **完善交互体验** - 节点详情、搜索、导出

---

**开发者**: GitHub Copilot  
**报告生成时间**: 2025-10-07 18:47  
**项目版本**: IntelliPDF v2.0-alpha  
**总开发进度**: 5/12 任务完成 (42%)
