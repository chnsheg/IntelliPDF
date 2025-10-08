# 对话上下文管理功能使用说明

## 功能概述

实现了智能的对话上下文管理系统，使AI对话更加聚焦和有条理。

## 核心概念

### 1. 话题上下文 (Topic Context)
- **定义**: 用户选中的一段文本，作为一系列对话的讨论主题
- **作用**: 所有围绕这段文本的对话都归为同一个话题
- **包含信息**:
  - 选中的文本内容
  - 文本所在页码
  - 文本位置坐标
  - 相关的chunk上下文

### 2. 话题对话 (Topic Messages)
- **定义**: 从话题开始到新话题开始之间的所有对话
- **特点**: 这些对话共享同一个上下文背景
- **用途**: 生成书签时使用话题对话而非全部对话

## 使用流程

### 步骤1: 选择文本
1. 在PDF中用鼠标选中一段文字
2. 出现工具栏，显示5个按钮

### 步骤2: 点击"AI提问"按钮
⚠️ **重点**: 只有点击"AI提问"按钮，选中的文本才会设置为话题上下文

**不会触发的情况**:
- 仅选中文字但没点击按钮
- 点击了高亮、下划线等其他按钮

**会发生什么**:
- 聊天面板自动打开（如果未开）
- 选中文本显示在输入框上方的蓝紫色渐变区域
- 显示"💬 当前话题"标识
- 显示当前话题已有的对话数量

### 步骤3: 进行对话
1. 在输入框中输入问题
2. AI会基于话题上下文（选中文本+chunk上下文）回答
3. 所有对话都记录在当前话题下
4. 话题区域显示对话数量实时更新

### 步骤4: 生成书签
1. 当有话题上下文且进行过对话后，右上角显示"生成书签"按钮
2. 按钮显示当前话题的对话数量，如"生成书签 (3)"
3. 点击按钮生成书签

**书签包含内容**:
- 话题文本（选中的文字）
- 话题所在页码和位置
- **所有话题对话**（不是全部对话）
- chunk上下文信息
- AI生成的摘要

### 步骤5: 开始新话题（可选）
**方式1: 手动开始**
- 点击话题区域右侧的"开始新话题"链接
- 清除当前话题上下文

**方式2: 自动开始**
- 选择新的文本并点击"AI提问"
- 系统自动检测文本变化，开始新话题

## 界面说明

### 话题上下文显示区域
```
┌─────────────────────────────────────────────┐
│ 💬 当前话题           3 条对话    第 160 页 │
│                                              │
│ 为 find_file()和 find_path()命令指定搜...   │
│                                              │
│ 💡 当前对话都围绕这段文本展开    开始新话题  │
└─────────────────────────────────────────────┘
```

**元素说明**:
- `💬 当前话题`: 标识这是话题上下文
- `3 条对话`: 蓝色圆角标签，显示话题对话数量
- `第 160 页`: 话题文本所在页码
- 中间区域: 显示话题文本（最多2行）
- `开始新话题`: 点击手动清除当前话题

### 生成书签按钮
```
🔖 生成书签 (3)
```
- 数字表示将要包含的对话数量
- 悬停显示详细提示："根据当前话题的 3 条对话生成AI书签"

## 工作原理

### 数据结构
```typescript
// 话题上下文
topicContext: {
  text: string;              // 选中的文本
  pageNumber: number;        // 页码
  position: { x, y, w, h };  // 位置
  chunkContext?: string;     // chunk上下文
}

// 话题起始索引
topicStartIndex: number;     // 当前话题从第几条消息开始
```

### 流程图
```
用户选中文字
    ↓
点击"AI提问"按钮
    ↓
设置topicContext
    ↓
设置topicStartIndex = 当前消息数量
    ↓
用户输入问题 → 对话 → 对话 → ...
    ↓
点击"生成书签"
    ↓
使用messages[topicStartIndex:]作为对话历史
    ↓
调用API生成书签
```

### 状态检测
```typescript
// 检测是否需要开始新话题
if (selectedText变化) {
  if (!topicContext || topicContext.text !== selectedText) {
    // 开始新话题
    setTopicContext({ text: selectedText, ... });
    setTopicStartIndex(messages.length);
  }
}
```

## 示例场景

### 场景1: 连续提问同一段文字
```
1. 选中"find_file()命令"相关文字
2. 点击"AI提问"
3. 输入："这个命令是做什么的？"
   → 话题对话数: 1
4. 输入："它有哪些参数？"
   → 话题对话数: 2
5. 输入："能给个例子吗？"
   → 话题对话数: 3
6. 点击"生成书签 (3)"
   → 书签包含所有3轮对话
```

### 场景2: 切换话题
```
1. 选中"find_file()命令"
2. 点击"AI提问"，进行3轮对话
3. 选中"cmake命令"
4. 点击"AI提问"
   → 自动开始新话题
   → topicStartIndex更新为当前位置
5. 新话题的对话从0开始计数
```

### 场景3: 手动开始新话题
```
1. 当前话题有5条对话
2. 点击"开始新话题"
   → topicContext = null
   → topicStartIndex = 当前消息数量
3. 下次选择文字+点击AI提问，开始全新话题
```

## 优势

### 1. 清晰的对话组织
- 每个话题独立
- 避免对话混乱
- 容易回顾特定话题

### 2. 精准的书签生成
- 只包含相关对话
- 不会混入无关内容
- 摘要更准确

### 3. 更好的AI回答质量
- AI始终知道讨论主题
- 上下文保持一致
- 避免话题跳跃

### 4. 灵活的话题切换
- 自动检测文本变化
- 手动控制话题切换
- 保留历史对话

## 注意事项

⚠️ **重要**: 必须点击"AI提问"按钮才能设置话题上下文
- 仅选中文字不会创建话题
- 点击其他按钮（高亮、下划线等）不会创建话题

⚠️ 生成书签后，当前话题仍然保留
- 可以继续在当前话题下对话
- 想要新话题需要手动或自动开始

⚠️ 刷新页面会清除话题上下文
- 对话历史可能保留（取决于store实现）
- 话题上下文是临时状态

## 技术实现

### 关键文件
- `frontend/src/components/ChatPanel.tsx` - 话题管理核心
- `frontend/src/components/PDFViewerEnhanced.tsx` - AI提问按钮处理
- `frontend/src/pages/DocumentViewerPage.tsx` - 事件协调

### 关键代码片段

#### 1. 设置话题上下文
```typescript
useEffect(() => {
  if (selectedText && selectedTextPosition) {
    if (!topicContext || topicContext.text !== selectedText) {
      setTopicContext({
        text: selectedText,
        pageNumber: currentPage,
        position: selectedTextPosition,
        chunkContext: contextChunks.join('\n\n')
      });
      setTopicStartIndex(messages.length);
    }
  }
}, [selectedText, ...]);
```

#### 2. 生成书签
```typescript
const handleGenerateBookmark = async () => {
  const topicMessages = messages.slice(topicStartIndex);
  const conversationHistory = topicMessages.map(msg => ({
    role: msg.role,
    content: msg.content
  }));
  
  await apiService.generateBookmark({
    selected_text: topicContext.text,
    conversation_history: conversationHistory,
    context: topicContext.chunkContext,
    ...
  });
};
```

#### 3. 触发AI提问
```typescript
// PDFViewerEnhanced.tsx
const dispatchAIQuestion = () => {
  window.dispatchEvent(new CustomEvent('aiQuestion', { 
    detail: {
      selected_text: selectionInfo.text,
      action: 'set_context'  // 关键：标记为设置上下文
    } 
  }));
};
```

## 未来优化方向

1. **话题持久化**: 将话题上下文保存到本地存储
2. **话题历史**: 显示所有话题的列表，可以回到之前的话题
3. **话题合并**: 支持将多个话题合并为一个
4. **话题分支**: 从某个话题创建分支讨论
5. **话题标签**: 为话题添加自定义标签
6. **多话题书签**: 一次性为多个话题生成书签

## 测试

### 功能测试
```bash
# 启动前端
cd frontend
npm run dev
```

### 测试步骤
1. 打开PDF文档
2. 选中文字，点击"AI提问"
3. 验证话题区域出现
4. 进行3-5轮对话
5. 验证对话数量正确显示
6. 点击"生成书签"
7. 验证书签生成成功
8. 选择新文字，点击"AI提问"
9. 验证新话题自动开始

### 预期结果
✅ 话题区域显示正确的文本和页码
✅ 对话数量实时更新
✅ 生成书签按钮显示正确数量
✅ 书签包含所有话题对话
✅ 切换话题后对话数量重置
✅ 手动开始新话题功能正常
