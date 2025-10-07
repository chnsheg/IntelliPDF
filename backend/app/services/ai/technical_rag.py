"""
技术文档专用 RAG 服务
针对技术教程、编程指南等文档优化
支持按章节、知识点进行精准问答
"""
from typing import List, Dict, Any, Optional
from loguru import logger

from ...infrastructure.ai.gemini_client import get_gemini_client
from ...core.exceptions import AIServiceError
from .retrieval import RetrievalService


class TechnicalDocRAG:
    """技术文档专用 RAG 服务"""

    def __init__(
        self,
        retrieval_service: Optional[RetrievalService] = None
    ):
        """
        初始化技术文档 RAG 服务

        Args:
            retrieval_service: 检索服务实例
        """
        self.gemini_client = None  # 延迟初始化
        self.retrieval_service = retrieval_service or RetrievalService()

        logger.info("Initialized TechnicalDocRAG service")

    async def _ensure_client(self):
        """确保 Gemini 客户端已初始化"""
        if self.gemini_client is None:
            self.gemini_client = await get_gemini_client()

    def _build_technical_prompt(
        self,
        question: str,
        context_chunks: List[Dict[str, Any]],
        language: str = "zh"
    ) -> str:
        """
        构建技术文档专用 Prompt

        Args:
            question: 用户问题
            context_chunks: 上下文块（章节）
            language: 语言

        Returns:
            完整的 Prompt
        """
        if language == "zh":
            system_instruction = """你是一个专业的技术文档助手，专门解答编程、Linux、技术教程相关的问题。

你的职责：
1. **精准回答**：基于提供的文档章节，给出准确、专业的技术解答
2. **代码示例**：如果文档中有代码，请完整引用并解释
3. **步骤说明**：对于操作类问题，给出清晰的步骤
4. **概念解释**：对技术术语进行通俗易懂的解释
5. **引用来源**：说明答案来自哪个章节

回答要求：
- 使用专业但易懂的语言
- 包含具体的代码示例（如果相关）
- 给出实际的操作步骤
- 必要时补充注意事项
"""
            context_header = "### 相关章节内容\n\n"
            answer_header = "\n### 请基于以上章节内容回答问题\n\n"
        else:
            system_instruction = """You are a professional technical documentation assistant, specializing in programming, Linux, and technical tutorials.

Your responsibilities:
1. **Precise answers**: Provide accurate, professional technical explanations based on the document sections
2. **Code examples**: Quote and explain code from the documentation when available
3. **Step-by-step**: Provide clear steps for operational questions
4. **Concept explanation**: Explain technical terms in an accessible way
5. **Citation**: Indicate which section the answer comes from

Requirements:
- Use professional but understandable language
- Include specific code examples (if relevant)
- Provide actual operational steps
- Add notes when necessary
"""
            context_header = "### Relevant Section Content\n\n"
            answer_header = "\n### Please answer the question based on the above sections\n\n"

        # 构建上下文
        context_text = context_header
        for i, chunk in enumerate(context_chunks, 1):
            # 显示章节信息
            chunk_title = chunk.get('metadata', {}).get(
                'title', f'Section {i}')
            chunk_number = chunk.get('metadata', {}).get('number', '')

            if chunk_number:
                section_header = f"【章节 {chunk_number}】{chunk_title}"
            else:
                section_header = f"【{chunk_title}】"

            context_text += f"\n#### {section_header}\n\n"
            context_text += chunk['text'][:2000]  # 限制每个块的长度
            context_text += "\n\n"

            if i >= 3:  # 最多使用3个章节
                break

        # 构建完整 Prompt
        full_prompt = f"""{system_instruction}

{context_text}

{answer_header}

**问题**: {question}

请提供详细的技术解答：
"""

        return full_prompt

    async def answer_knowledge_point(
        self,
        question: str,
        document_id: Optional[str] = None,
        chapter_filter: Optional[str] = None,
        n_contexts: int = 2,
        language: str = "zh",
        include_code: bool = True
    ) -> Dict[str, Any]:
        """
        回答特定知识点的问题

        Args:
            question: 用户问题
            document_id: 文档ID
            chapter_filter: 章节过滤（例如："1.1" 只搜索1.1节）
            n_contexts: 检索的章节数量
            language: 语言
            include_code: 是否包含代码

        Returns:
            回答结果
        """
        try:
            logger.info(
                f"Answering knowledge point question: {question[:50]}...")

            # 1. 构建检索过滤器
            search_filters = {}
            if document_id:
                search_filters['document_id'] = document_id
            if chapter_filter:
                search_filters['number'] = chapter_filter
            if include_code:
                search_filters['has_code'] = True

            # 2. 检索相关章节
            if document_id and not chapter_filter:
                context_chunks = self.retrieval_service.search_by_document(
                    question,
                    document_id,
                    n_results=n_contexts
                )
            else:
                context_chunks = self.retrieval_service.search(
                    question,
                    n_results=n_contexts,
                    # where=search_filters if search_filters else None
                )

            if not context_chunks:
                return {
                    'answer': '抱歉，我没有找到相关的章节内容来回答这个问题。' if language == 'zh'
                    else 'Sorry, I could not find relevant sections to answer this question.',
                    'chapters': [],
                    'source_count': 0,
                    'has_code': False
                }

            logger.info(f"Retrieved {len(context_chunks)} relevant chapters")

            # 3. 确保 Gemini 客户端已初始化
            await self._ensure_client()

            # 4. 构建技术文档专用 Prompt
            prompt = self._build_technical_prompt(
                question, context_chunks, language)

            # 5. 调用 Gemini 生成回答
            response = await self.gemini_client.generate_content(
                prompt=prompt,
                temperature=0.3  # 技术文档使用更低的温度，确保准确性
            )

            # 6. 提取章节信息
            chapters = []
            has_code = False
            for chunk in context_chunks:
                metadata = chunk.get('metadata', {})
                chapter_info = {
                    'number': metadata.get('number', ''),
                    'title': metadata.get('title', ''),
                    'type': metadata.get('type', 'section'),
                    'level': metadata.get('level', 2),
                    'has_code': metadata.get('has_code', False),
                    'code_blocks': metadata.get('code_blocks', 0),
                    'page_range': metadata.get('page_range', ''),
                    'preview': chunk['text'][:200] + '...' if len(chunk['text']) > 200 else chunk['text'],
                }
                chapters.append(chapter_info)

                if chapter_info['has_code']:
                    has_code = True

            # 7. 构建结果
            result = {
                'answer': response,
                'chapters': chapters,
                'source_count': len(chapters),
                'has_code': has_code,
                'question': question,
                'filters': {
                    'document_id': document_id,
                    'chapter_filter': chapter_filter,
                }
            }

            logger.info(
                f"Generated answer ({len(response)} chars) from {len(chapters)} chapters")
            return result

        except Exception as e:
            logger.error(f"Error answering knowledge point: {e}")
            raise AIServiceError(f"Failed to answer question: {str(e)}")

    async def explain_code_snippet(
        self,
        code: str,
        document_id: Optional[str] = None,
        language: str = "zh"
    ) -> Dict[str, Any]:
        """
        解释代码片段（从文档中提取的代码）

        Args:
            code: 代码片段
            document_id: 文档ID（可选，用于获取上下文）
            language: 语言

        Returns:
            代码解释结果
        """
        try:
            logger.info(f"Explaining code snippet ({len(code)} chars)...")

            # 1. 如果提供了文档ID，尝试获取相关上下文
            context = ""
            if document_id:
                # 搜索包含此代码的章节
                context_chunks = self.retrieval_service.search(
                    code[:100],  # 使用代码开头搜索
                    n_results=1
                )
                if context_chunks:
                    context = f"\n\n上下文章节：\n{context_chunks[0]['text'][:500]}\n"

            # 2. 确保客户端已初始化
            await self._ensure_client()

            # 3. 构建代码解释 Prompt
            if language == "zh":
                prompt = f"""你是一个专业的代码解释助手。请详细解释以下代码：

```
{code}
```
{context}

请提供：
1. **代码功能**：这段代码的主要功能是什么
2. **逐行解释**：关键代码行的详细说明
3. **技术要点**：涉及的技术概念和API
4. **使用场景**：什么时候使用这种代码
5. **注意事项**：使用时需要注意的问题

请用通俗易懂的语言解释，适合初学者理解。
"""
            else:
                prompt = f"""You are a professional code explanation assistant. Please explain the following code in detail:

```
{code}
```
{context}

Please provide:
1. **Code Function**: What is the main function of this code
2. **Line-by-line Explanation**: Detailed explanation of key code lines
3. **Technical Points**: Technical concepts and APIs involved
4. **Use Cases**: When to use this type of code
5. **Notes**: Issues to be aware of when using

Please explain in an accessible way, suitable for beginners.
"""

            # 4. 生成解释
            explanation = await self.gemini_client.generate_content(
                prompt=prompt,
                temperature=0.5
            )

            result = {
                'code': code,
                'explanation': explanation,
                'has_context': bool(context),
            }

            logger.info(
                f"Generated code explanation ({len(explanation)} chars)")
            return result

        except Exception as e:
            logger.error(f"Error explaining code: {e}")
            raise AIServiceError(f"Failed to explain code: {str(e)}")

    async def compare_concepts(
        self,
        concept1: str,
        concept2: str,
        document_id: Optional[str] = None,
        language: str = "zh"
    ) -> Dict[str, Any]:
        """
        比较两个技术概念

        Args:
            concept1: 概念1
            concept2: 概念2
            document_id: 文档ID
            language: 语言

        Returns:
            比较结果
        """
        try:
            logger.info(f"Comparing concepts: {concept1} vs {concept2}")

            # 1. 分别检索两个概念的相关章节
            chunks1 = self.retrieval_service.search(
                concept1,
                n_results=2
            )
            chunks2 = self.retrieval_service.search(
                concept2,
                n_results=2
            )

            # 2. 确保客户端已初始化
            await self._ensure_client()

            # 3. 构建比较 Prompt
            context1 = chunks1[0]['text'][:1000] if chunks1 else "未找到相关内容"
            context2 = chunks2[0]['text'][:1000] if chunks2 else "未找到相关内容"

            if language == "zh":
                prompt = f"""请比较以下两个技术概念：

### 概念 1：{concept1}
{context1}

### 概念 2：{concept2}
{context2}

请提供详细的比较分析：
1. **定义对比**：两个概念各自的定义
2. **功能对比**：主要功能和用途的区别
3. **使用场景**：分别适用的场景
4. **优缺点**：各自的优势和劣势
5. **选择建议**：什么情况下选择哪个

请用表格或清晰的格式展示对比。
"""
            else:
                prompt = f"""Please compare the following two technical concepts:

### Concept 1: {concept1}
{context1}

### Concept 2: {concept2}
{context2}

Please provide a detailed comparative analysis:
1. **Definition Comparison**: Definitions of the two concepts
2. **Function Comparison**: Differences in main functions and uses
3. **Use Cases**: Applicable scenarios for each
4. **Pros and Cons**: Advantages and disadvantages of each
5. **Selection Advice**: When to choose which one

Please present the comparison in a table or clear format.
"""

            # 4. 生成比较
            comparison = await self.gemini_client.generate_content(
                prompt=prompt,
                temperature=0.5
            )

            result = {
                'concept1': concept1,
                'concept2': concept2,
                'comparison': comparison,
                'sources': {
                    'concept1_chapters': [c.get('metadata', {}).get('title', '') for c in chunks1],
                    'concept2_chapters': [c.get('metadata', {}).get('title', '') for c in chunks2],
                }
            }

            logger.info(
                f"Generated concept comparison ({len(comparison)} chars)")
            return result

        except Exception as e:
            logger.error(f"Error comparing concepts: {e}")
            raise AIServiceError(f"Failed to compare concepts: {str(e)}")
