"""
LLM 服务 - 检索增强生成 (RAG)
集成 Gemini API 实现基于文档的问答
"""
from typing import List, Dict, Any, Optional

from loguru import logger

from ...infrastructure.ai.gemini_client import get_gemini_client
from ...core.exceptions import AIServiceError
from .retrieval import RetrievalService


class LLMService:
    """大语言模型服务"""

    def __init__(
        self,
        retrieval_service: Optional[RetrievalService] = None
    ):
        """
        初始化 LLM 服务

        Args:
            retrieval_service: 检索服务实例
        """
        self.gemini_client = None  # 延迟初始化
        self.retrieval_service = retrieval_service or RetrievalService()

        logger.info("Initialized LLM service with Gemini")

    async def _ensure_client(self):
        """确保 Gemini 客户端已初始化"""
        if self.gemini_client is None:
            self.gemini_client = await get_gemini_client()

    def _build_rag_prompt(
        self,
        question: str,
        context_chunks: List[Dict[str, Any]],
        language: str = "zh"
    ) -> str:
        """
        构建 RAG prompt

        Args:
            question: 用户问题
            context_chunks: 上下文文档块
            language: 语言 ('zh' 或 'en')

        Returns:
            完整的 prompt
        """
        if language == "zh":
            system_instruction = """你是一个专业的文档助手。请根据提供的文档内容回答用户的问题。

规则：
1. 只根据提供的文档内容回答，不要编造信息
2. 如果文档中没有相关信息，请明确告知用户
3. 回答要准确、简洁、有条理
4. 可以引用文档中的原文来支持你的回答
5. 如果问题不清楚，可以要求用户澄清"""

            # Defensive: chunk may have 'text' or 'content' key depending on source
            def _chunk_text(chunk):
                if not chunk:
                    return ''
                if isinstance(chunk, dict):
                    return chunk.get('text') or chunk.get('content') or ''
                # Fallback for unexpected structures
                try:
                    return getattr(chunk, 'text', None) or getattr(chunk, 'content', None) or ''
                except Exception:
                    return ''

            context_text = "\n\n---\n\n".join([
                f"【文档片段 {i+1}】\n{_chunk_text(chunk)}"
                for i, chunk in enumerate(context_chunks)
            ])

            prompt = f"""{system_instruction}

=== 相关文档内容 ===

{context_text}

=== 用户问题 ===

{question}

=== 你的回答 ===
"""
        else:
            system_instruction = """You are a professional document assistant. Please answer the user's question based on the provided document content.

Rules:
1. Answer only based on the provided document content, don't make up information
2. If the document doesn't contain relevant information, clearly inform the user
3. Answers should be accurate, concise, and well-organized
4. You can quote original text from the document to support your answer
5. If the question is unclear, you can ask the user for clarification"""

            context_text = "\n\n---\n\n".join([
                f"【Document Chunk {i+1}】\n{chunk['text']}"
                for i, chunk in enumerate(context_chunks)
            ])

            prompt = f"""{system_instruction}

=== Relevant Document Content ===

{context_text}

=== User Question ===

{question}

=== Your Answer ===
"""

        return prompt

    async def answer_question(
        self,
        question: str,
        document_id: Optional[str] = None,
        n_contexts: int = 3,
        language: str = "zh",
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        回答问题（RAG）

        Args:
            question: 用户问题
            document_id: 限定文档ID（可选）
            n_contexts: 检索的上下文数量
            language: 语言
            temperature: 生成温度

        Returns:
            回答结果
        """
        try:
            logger.info(f"Answering question: {question[:50]}...")

            # 1. 检索相关文档块
            if document_id:
                context_chunks = self.retrieval_service.search_by_document(
                    question,
                    document_id,
                    n_results=n_contexts
                )
            else:
                context_chunks = self.retrieval_service.search(
                    question,
                    n_results=n_contexts
                )

            if not context_chunks:
                return {
                    'answer': '抱歉，我没有找到相关的文档内容来回答这个问题。' if language == 'zh'
                    else 'Sorry, I could not find relevant document content to answer this question.',
                    'contexts': [],
                    'source_count': 0
                }

            logger.info(f"Retrieved {len(context_chunks)} context chunks")

            # 2. 确保 Gemini 客户端已初始化
            await self._ensure_client()

            # 3. 构建 prompt
            prompt = self._build_rag_prompt(question, context_chunks, language)

            # 4. 调用 Gemini 生成回答
            response = await self.gemini_client.generate_content(
                prompt=prompt,
                temperature=temperature
            )

            # 4. 构建结果
            # Build contexts defensively
            contexts = []
            for chunk in context_chunks:
                if not chunk:
                    continue
                text = None
                metadata = {}
                distance = None
                if isinstance(chunk, dict):
                    text = chunk.get('text') or chunk.get('content') or ''
                    metadata = chunk.get('metadata') or {}
                    distance = chunk.get('distance')
                else:
                    # try attribute access
                    text = getattr(chunk, 'text', None) or getattr(
                        chunk, 'content', None) or ''
                    metadata = getattr(chunk, 'metadata', None) or {}

                snippet = text[:200] + \
                    '...' if isinstance(text, str) and len(
                        text) > 200 else text
                contexts.append({
                    'text': snippet,
                    'metadata': metadata,
                    'relevance_score': 1 - distance if distance is not None else None
                })

            result = {
                'answer': response,
                'contexts': contexts,
                'source_count': len(contexts),
                'question': question
            }

            logger.info(f"Generated answer ({len(response)} chars)")
            return result

        except Exception as e:
            logger.error(f"Error answering question: {e}")
            raise AIServiceError(f"Failed to answer question: {str(e)}")

    async def chat_with_document(
        self,
        messages: List[Dict[str, str]],
        document_id: Optional[str] = None,
        n_contexts: int = 3,
        language: str = "zh"
    ) -> Dict[str, Any]:
        """
        与文档对话

        Args:
            messages: 对话历史 [{"role": "user/assistant", "content": "..."}]
            document_id: 文档ID
            n_contexts: 上下文数量
            language: 语言

        Returns:
            对话结果
        """
        try:
            # Normalize messages: support pydantic Message models or dicts
            normalized_msgs = []
            if messages:
                for msg in messages:
                    if hasattr(msg, 'dict'):
                        m = msg.dict()
                    elif isinstance(msg, dict):
                        m = msg
                    else:
                        # Fallback: try attribute access
                        m = {
                            'role': getattr(msg, 'role', None),
                            'content': getattr(msg, 'content', None)
                        }
                    normalized_msgs.append(m)

            # 获取最后一个用户消息
            user_messages = [
                m for m in normalized_msgs if m.get('role') == 'user']
            if not user_messages:
                raise AIServiceError("No user message found")

            last_question = user_messages[-1].get('content')

            # 使用 RAG 回答
            result = await self.answer_question(
                question=last_question,
                document_id=document_id,
                n_contexts=n_contexts,
                language=language
            )

            # 添加对话历史
            result['conversation_history'] = messages

            return result

        except Exception as e:
            logger.error(f"Error in chat: {e}")
            raise AIServiceError(f"Failed to chat with document: {str(e)}")

    async def summarize_document(
        self,
        document_id: str,
        max_chunks: int = 10,
        language: str = "zh"
    ) -> Dict[str, Any]:
        """
        总结文档

        Args:
            document_id: 文档ID
            max_chunks: 最大使用的文档块数
            language: 语言

        Returns:
            总结结果
        """
        try:
            logger.info(f"Summarizing document: {document_id}")

            # 获取文档块
            chunks = self.retrieval_service.get_document_chunks(
                document_id,
                limit=max_chunks
            )

            if not chunks:
                return {
                    'summary': '无法找到文档内容。' if language == 'zh' else 'Could not find document content.',
                    'chunk_count': 0
                }

            # 合并文本
            combined_text = '\n\n'.join([chunk['text'] for chunk in chunks])

            # 构建总结 prompt
            if language == "zh":
                prompt = f"""请对以下文档内容进行总结。总结应该包括：

1. 文档的主要主题和目的
2. 关键要点（3-5点）
3. 重要结论或发现

文档内容：

{combined_text[:8000]}  # 限制长度

请提供简洁但全面的总结："""
            else:
                prompt = f"""Please summarize the following document content. The summary should include:

1. Main topic and purpose of the document
2. Key points (3-5 points)
3. Important conclusions or findings

Document content:

{combined_text[:8000]}  # Limit length

Please provide a concise but comprehensive summary:"""

            # 确保 Gemini 客户端已初始化
            await self._ensure_client()

            # 生成总结
            summary = await self.gemini_client.generate_content(
                prompt=prompt,
                temperature=0.5
            )

            result = {
                'summary': summary,
                'chunk_count': len(chunks),
                'document_id': document_id
            }

            logger.info(f"Generated summary ({len(summary)} chars)")
            return result

        except Exception as e:
            logger.error(f"Error summarizing document: {e}")
            raise AIServiceError(f"Failed to summarize document: {str(e)}")

    async def extract_keywords(
        self,
        document_id: str,
        max_keywords: int = 10,
        language: str = "zh"
    ) -> Dict[str, Any]:
        """
        提取文档关键词

        Args:
            document_id: 文档ID
            max_keywords: 最大关键词数
            language: 语言

        Returns:
            关键词列表
        """
        try:
            logger.info(f"Extracting keywords from document: {document_id}")

            # 确保 Gemini 客户端已初始化
            await self._ensure_client()

            # 获取部分文档块
            chunks = self.retrieval_service.get_document_chunks(
                document_id,
                limit=5
            )

            if not chunks:
                return {'keywords': [], 'document_id': document_id}

            # 合并文本
            combined_text = '\n\n'.join(
                [chunk['text'] for chunk in chunks[:3]])

            # 构建关键词提取 prompt
            if language == "zh":
                prompt = f"""请从以下文档内容中提取 {max_keywords} 个最重要的关键词。

要求：
1. 关键词应该是名词或名词短语
2. 按重要性排序
3. 每行一个关键词
4. 不要添加编号或其他符号

文档内容：

{combined_text[:5000]}

关键词："""
            else:
                prompt = f"""Please extract {max_keywords} most important keywords from the following document content.

Requirements:
1. Keywords should be nouns or noun phrases
2. Sort by importance
3. One keyword per line
4. No numbering or other symbols

Document content:

{combined_text[:5000]}

Keywords:"""

            # 生成关键词
            response = await self.gemini_client.generate_content(
                prompt=prompt,
                temperature=0.3
            )

            # 解析关键词
            keywords = [kw.strip()
                        for kw in response.split('\n') if kw.strip()]
            keywords = keywords[:max_keywords]

            result = {
                'keywords': keywords,
                'document_id': document_id,
                'count': len(keywords)
            }

            logger.info(f"Extracted {len(keywords)} keywords")
            return result

        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            raise AIServiceError(f"Failed to extract keywords: {str(e)}")
