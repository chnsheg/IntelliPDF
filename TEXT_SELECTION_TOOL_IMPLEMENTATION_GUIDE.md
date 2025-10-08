# 文本选择工具功能实现指南

## 当前状态

### 已完成 ✅
1. **书签和来源跳转修复**
   - DocumentViewerPage.tsx 中的跳转逻辑已修复
   - 点击书签和聊天面板的来源都能正确跳转

2. **数据库模型设计**
   - AnnotationModel (标注)
   - TagModel (标签)  
   - AIQuestionModel (AI问答记录)
   - 表已创建：tags, ai_questions

3. **Schema 定义**
   - TagCreate/TagUpdate/TagResponse
   - AIQuestionCreate/AIQuestionResponse
   - 对应的查询和列表响应schemas

## 待实现功能

### 后端API (优先级高)

#### 1. Repositories (数据访问层)
创建文件：
- `backend/app/repositories/annotation_repository.py`
- `backend/app/repositories/tag_repository.py`
- `backend/app/repositories/ai_question_repository.py`

每个repository应继承 `BaseRepository` 并实现特定查询方法。

#### 2. Services (业务逻辑层)
创建文件：
- `backend/app/services/annotation_service.py` - 标注管理服务
- `backend/app/services/tag_service.py` - 标签管理服务
- `backend/app/services/ai_question_service.py` - AI问答服务

AI问答服务需要：
- 根据选中文本位置找到对应的chunk
- 将chunk内容作为上下文
- 调用Gemini API生成回答
- 保存问答记录

#### 3. API Endpoints
创建文件：
- `backend/app/api/v1/endpoints/annotations.py` - 标注CRUD接口
- `backend/app/api/v1/endpoints/tags.py` - 标签CRUD接口  
- `backend/app/api/v1/endpoints/ai_questions.py` - AI问答接口

需要实现的端点：
```
POST   /api/v1/annotations          - 创建标注
GET    /api/v1/annotations          - 查询标注列表
PATCH  /api/v1/annotations/{id}     - 更新标注
DELETE /api/v1/annotations/{id}     - 删除标注

POST   /api/v1/tags                 - 创建标签
GET    /api/v1/tags                 - 获取标签列表
PATCH  /api/v1/tags/{id}            - 更新标签
DELETE /api/v1/tags/{id}            - 删除标签

POST   /api/v1/ai-questions         - 创建AI问答
GET    /api/v1/ai-questions         - 获取问答历史
GET    /api/v1/ai-questions/{id}    - 获取单个问答
```

### 前端实现 (优先级高)

#### 1. 文本选择工具栏组件
创建文件：`frontend/src/components/TextSelectionToolbar.tsx`

功能：
- 监听PDF文本选择事件
- 在选中文本上方浮动显示工具栏
- 5个按钮：
  1. 🎨 高亮 (Highlight)
  2. __ 下划线 (Underline)  
  3. ~~ 删除线 (Strikethrough)
  4. 🏷️ 生成标签 (Create Tag)
  5. 💬 AI提问 (Ask AI)

#### 2. 标注渲染
在 `PDFViewerEnhanced.tsx` 中：
- 加载文档的所有标注
- 在PDF页面上渲染标注（使用SVG overlay）
- 支持点击标注查看详情/编辑
- 支持标注的拖拽/调整大小（可选）

#### 3. AI问答对话框
创建文件：`frontend/src/components/AIQuestionDialog.tsx`

功能：
- 显示选中的文本
- 输入问题框
- 发送请求到后端
- 显示AI回答
- 保存问答记录

#### 4. 标签管理面板
创建文件：`frontend/src/components/TagManagementPanel.tsx`

功能：
- 显示用户的所有标签
- 创建/编辑/删除标签
- 为标注分配标签
- 按标签筛选标注

### API Service 更新
在 `frontend/src/services/api.ts` 中添加：

```typescript
// Annotations
async createAnnotation(data: AnnotationCreate): Promise<AnnotationResponse>
async getAnnotations(query: AnnotationQuery): Promise<AnnotationListResponse>
async updateAnnotation(id: string, data: AnnotationUpdate): Promise<AnnotationResponse>
async deleteAnnotation(id: string): Promise<void>

// Tags
async createTag(data: TagCreate): Promise<TagResponse>
async getTags(): Promise<TagListResponse>
async updateTag(id: string, data: TagUpdate): Promise<TagResponse>
async deleteTag(id: string): Promise<void>

// AI Questions
async createAIQuestion(data: AIQuestionCreate): Promise<AIQuestionResponse>
async getAIQuestions(query: AIQuestionQuery): Promise<AIQuestionListResponse>
```

## 实现建议

### Phase 1: 后端基础功能 (2-3小时)
1. 实现 repositories (模板化代码，较快)
2. 实现 services (核心业务逻辑)
3. 实现 API endpoints
4. 测试API (使用test_api_complete.py)

### Phase 2: 前端基础UI (2-3小时)
1. 实现TextSelectionToolbar组件
2. 集成到PDFViewerEnhanced
3. 实现基本的标注创建和显示

### Phase 3: 高级功能 (2-3小时)
1. AI问答对话框
2. 标签管理
3. 标注渲染和交互
4. 数据持久化和同步

### Phase 4: 测试和优化 (1-2小时)
1. 端到端测试
2. UI/UX优化
3. 错误处理
4. 性能优化

## 技术要点

### 前端文本选择
```typescript
// 监听文本选择
useEffect(() => {
  const handleSelection = () => {
    const selection = window.getSelection();
    if (selection && selection.toString().trim()) {
      const range = selection.getRangeAt(0);
      const rect = range.getBoundingClientRect();
      // 显示工具栏
      setToolbarPosition({ x: rect.x, y: rect.y - 50 });
      setSelectedText(selection.toString());
    }
  };
  
  document.addEventListener('mouseup', handleSelection);
  return () => document.removeEventListener('mouseup', handleSelection);
}, []);
```

### 后端查找相关chunk
```python
async def find_chunk_by_position(
    document_id: str,
    page_number: int,
    text_content: str,
    chunk_repo: ChunkRepository
) -> Optional[ChunkModel]:
    """Find the chunk containing the selected text."""
    chunks = await chunk_repo.get_chunks_by_page(document_id, page_number)
    for chunk in chunks:
        if text_content in chunk.content:
            return chunk
    return None
```

### AI问答上下文构建
```python
async def ask_question_with_context(
    selected_text: str,
    chunk: ChunkModel,
    question: str,
    gemini_client: GeminiClient
) -> str:
    """Ask AI a question with surrounding context."""
    system_instruction = f"""你是一个文档分析助手。
    用户选中了以下文本：
    \"{selected_text}\"
    
    这段文本来自以下上下文：
    {chunk.content[:500]}...
    
    请基于上下文回答用户的问题。"""
    
    response = await gemini_client.generate_content(
        prompt=question,
        system_instruction=system_instruction
    )
    return response.text
```

## 参考文件
- 已有的BookmarkPanel实现可作为参考
- PDFViewerEnhanced的文本选择处理
- ChatPanel的AI交互逻辑
- DocumentProcessingService的服务模式

## 下一步行动
建议从后端API开始实现，因为：
1. 后端结构清晰，有现成模板可follow
2. 可以先用测试脚本验证功能
3. 前端可以在后端就绪后快速集成

需要我开始实现哪个部分？
