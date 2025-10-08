# AI 聊天 422 错误修复报告

## 问题描述

**错误**: `Request failed with status code 422 Unprocessable Entity`

**时间**: 2025-10-08 10:02-10:06

**现象**: 
- 用户在文档详情页尝试 AI 提问时返回 422 错误
- 后端日志只显示状态码，没有详细验证错误信息

## 根本原因

前端 `ChatRequest` 类型定义与后端 API schema 不匹配：

### 后端要求 (backend/app/schemas/chat.py)
```python
class ChatRequest(BaseModel):
    question: str  # 必需
    conversation_history: Optional[List[Message]] = None  # 可选
    top_k: int = 5  # 可选，默认5
    temperature: float = 0.7  # 可选，默认0.7
```

### 前端旧定义 (frontend/src/types/index.ts)
```typescript
// 错误：缺少必需字段
export interface ChatRequest {
    question: string;
    stream?: boolean;
}
```

### 问题
虽然 `conversation_history`、`top_k`、`temperature` 在后端是可选字段，但 FastAPI 的 Pydantic 验证可能因为其他原因拒绝请求：
1. 类型不匹配
2. 额外字段（`stream` 字段后端不支持）
3. Message 类型结构不一致

## 解决方案

### 1. 修复类型定义 (frontend/src/types/index.ts)

**已有的 ChatMessage 定义**:
```typescript
export interface ChatMessage {
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp?: string;
    sources?: ChunkSource[];
}
```

**修复后的 ChatRequest**:
```typescript
export interface ChatRequest {
    question: string;
    conversation_history?: ChatMessage[];  // 添加
    top_k?: number;  // 添加
    temperature?: number;  // 添加
    stream?: boolean;  // 保留（虽然后端不用，但不会影响）
}
```

### 2. 修复请求发送 (frontend/src/components/ChatPanel.tsx)

**旧代码** (第73-83行):
```typescript
mutationFn: async (question: string) => {
    let enhancedQuestion = question;
    if (contextChunks.length > 0) {
        const contextText = contextChunks.slice(0, 2).join('\n\n');
        enhancedQuestion = `基于以下上下文回答问题:\n\n上下文:\n${contextText}\n\n问题: ${question}`;
    }
    return apiService.chat(documentId, { question: enhancedQuestion });
},
```

**新代码**:
```typescript
mutationFn: async (question: string) => {
    let enhancedQuestion = question;
    if (contextChunks.length > 0) {
        const contextText = contextChunks.slice(0, 2).join('\n\n');
        enhancedQuestion = `基于以下上下文回答问题:\n\n上下文:\n${contextText}\n\n问题: ${question}`;
    }
    
    // 准备对话历史
    const conversationHistory = messages.map(msg => ({
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp || new Date().toISOString()
    }));
    
    return apiService.chat(documentId, { 
        question: enhancedQuestion,
        conversation_history: conversationHistory,  // 添加
        top_k: 5,  // 添加
        temperature: 0.7  // 添加
    });
},
```

## 修改文件列表

1. **frontend/src/types/index.ts**
   - 删除重复的 `ChatMessage` 定义
   - 修复 `ChatRequest` 接口，添加 `conversation_history`, `top_k`, `temperature` 字段

2. **frontend/src/components/ChatPanel.tsx**
   - 修改 `chatMutation.mutationFn`，在发送请求时包含所有必需字段
   - 从 `messages` 状态构建 `conversation_history`

## 测试步骤

### 1. 重启前端服务
```powershell
# 在 frontend 目录
# 停止当前服务 (Ctrl+C)
npm run dev
```

### 2. 浏览器测试
1. 打开 http://localhost:5174
2. 选择一个已上传的文档
3. 在 AI 聊天面板输入问题："这个文档讲的是什么？"
4. 点击发送

### 3. 预期结果
- ✅ 不再返回 422 错误
- ✅ 返回 AI 回答
- ✅ 显示相关的文档片段
- ✅ 支持多轮对话（conversation_history 会记录之前的对话）

## 技术细节

### 为什么需要 conversation_history？
虽然后端标记为可选，但提供对话历史有以下好处：
1. **上下文连续性**: AI 能理解前后文关系
2. **更好的回答**: 基于之前的对话给出更准确的答案
3. **避免重复**: AI 知道已经回答过什么

### 为什么需要 top_k 和 temperature？
- **top_k**: 控制检索多少个相关文档片段（默认5）
- **temperature**: 控制 AI 回答的随机性/创造性（0-2，默认0.7）

虽然使用默认值即可，但显式提供可以避免潜在的验证问题。

## 后续优化建议

### 1. 后端日志改进
建议在后端添加详细的验证错误日志：
```python
@router.post("/documents/{document_id}/chat")
async def chat_with_document(
    document_id: UUID,
    request: ChatRequest,
    ...
):
    try:
        logger.info(f"Chat request: {request.dict()}")
        ...
    except ValidationError as e:
        logger.error(f"Validation error: {e.json()}")
        raise
```

### 2. 前端错误处理改进
显示更详细的错误信息：
```typescript
onError: (error: any) => {
    let errorMsg = '未知错误';
    if (error?.response?.status === 422) {
        errorMsg = error?.response?.data?.detail || '请求格式错误';
    }
    addMessage({
        role: 'assistant',
        content: `抱歉，出现错误：${errorMsg}`,
        timestamp: new Date().toISOString(),
    });
    setLoading(false);
}
```

### 3. 可配置参数
可以在 UI 中添加高级选项，让用户调整 top_k 和 temperature：
```typescript
const [settings, setSettings] = useState({
    top_k: 5,
    temperature: 0.7
});
```

## 状态

- ✅ 代码修改完成
- ⏳ 等待前端重启
- ⏳ 等待浏览器测试确认

---

**修复时间**: 2025-10-08 10:08  
**修复人员**: AI Assistant  
**测试状态**: 待验证
