"""
PDF 文档智能分块服务
实现基于语义的文档分块策略
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
import re

from loguru import logger

from ...core.exceptions import PDFProcessingError
from .cache import get_pdf_cache


class PDFChunker:
    """PDF 文档智能分块器"""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separator: str = "\n\n",
        use_cache: bool = True
    ):
        """
        初始化分块器

        Args:
            chunk_size: 每个块的目标字符数
            chunk_overlap: 块之间的重叠字符数
            separator: 分隔符
            use_cache: 是否使用缓存
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separator = separator
        self.use_cache = use_cache
        self.cache = get_pdf_cache() if use_cache else None

        logger.info(
            f"Initialized chunker: size={chunk_size}, overlap={chunk_overlap}, cache={'enabled' if use_cache else 'disabled'}")

    def chunk_by_fixed_size(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        固定大小分块

        Args:
            text: 要分块的文本
            metadata: 额外的元数据

        Returns:
            分块列表
        """
        try:
            if not text:
                return []

            chunks = []
            start = 0
            text_length = len(text)
            chunk_index = 0

            while start < text_length:
                # 计算结束位置
                end = start + self.chunk_size

                # 如果不是最后一个块，尝试在分隔符处截断
                if end < text_length:
                    # 在结束位置附近寻找合适的断点
                    search_start = max(start, end - 100)
                    search_end = min(text_length, end + 100)
                    chunk_text = text[search_start:search_end]

                    # 寻找段落分隔符
                    separators = ['\n\n', '\n', '。',
                                  '！', '？', '.', '!', '?', ' ']
                    best_break = -1

                    for sep in separators:
                        pos = chunk_text.rfind(sep, 0, end - search_start)
                        if pos != -1:
                            best_break = search_start + pos + len(sep)
                            break

                    if best_break != -1:
                        end = best_break
                    else:
                        end = min(end, text_length)

                # 提取块文本
                chunk_text = text[start:end].strip()

                if chunk_text:
                    chunk = {
                        'chunk_index': chunk_index,
                        'text': chunk_text,
                        'start_char': start,
                        'end_char': end,
                        'char_count': len(chunk_text),
                        'word_count': len(chunk_text.split()),
                    }

                    # 添加额外元数据
                    if metadata:
                        chunk['metadata'] = metadata

                    chunks.append(chunk)
                    chunk_index += 1

                # 移动到下一个块的起始位置（考虑重叠）
                start = end - self.chunk_overlap if end < text_length else text_length

            logger.info(f"Created {len(chunks)} fixed-size chunks")
            return chunks

        except Exception as e:
            logger.error(f"Error in fixed-size chunking: {e}")
            raise PDFProcessingError(
                f"Failed to chunk by fixed size: {str(e)}")

    def chunk_by_paragraph(
        self,
        text: str,
        min_chunk_size: int = 100,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        按段落分块

        Args:
            text: 要分块的文本
            min_chunk_size: 最小块大小
            metadata: 额外的元数据

        Returns:
            分块列表
        """
        try:
            if not text:
                return []

            # 按段落分割
            paragraphs = re.split(r'\n\s*\n', text)
            chunks = []
            current_chunk = ""
            chunk_index = 0
            start_char = 0

            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue

                # 如果当前块加上新段落不超过目标大小，就合并
                if len(current_chunk) + len(para) + 2 <= self.chunk_size:
                    if current_chunk:
                        current_chunk += "\n\n" + para
                    else:
                        current_chunk = para
                else:
                    # 保存当前块
                    if current_chunk and len(current_chunk) >= min_chunk_size:
                        chunk = {
                            'chunk_index': chunk_index,
                            'text': current_chunk,
                            'start_char': start_char,
                            'end_char': start_char + len(current_chunk),
                            'char_count': len(current_chunk),
                            'word_count': len(current_chunk.split()),
                            'paragraph_count': current_chunk.count('\n\n') + 1
                        }

                        if metadata:
                            chunk['metadata'] = metadata

                        chunks.append(chunk)
                        chunk_index += 1
                        start_char += len(current_chunk) + 2

                    # 开始新块
                    current_chunk = para

            # 保存最后一个块
            if current_chunk and len(current_chunk) >= min_chunk_size:
                chunk = {
                    'chunk_index': chunk_index,
                    'text': current_chunk,
                    'start_char': start_char,
                    'end_char': start_char + len(current_chunk),
                    'char_count': len(current_chunk),
                    'word_count': len(current_chunk.split()),
                    'paragraph_count': current_chunk.count('\n\n') + 1
                }

                if metadata:
                    chunk['metadata'] = metadata

                chunks.append(chunk)

            logger.info(f"Created {len(chunks)} paragraph-based chunks")
            return chunks

        except Exception as e:
            logger.error(f"Error in paragraph chunking: {e}")
            raise PDFProcessingError(f"Failed to chunk by paragraph: {str(e)}")

    def chunk_by_sentence(
        self,
        text: str,
        sentences_per_chunk: int = 5,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        按句子分块

        Args:
            text: 要分块的文本
            sentences_per_chunk: 每个块包含的句子数
            metadata: 额外的元数据

        Returns:
            分块列表
        """
        try:
            if not text:
                return []

            # 分割句子（支持中英文）
            sentence_endings = r'[。！？\.!?]+'
            sentences = re.split(sentence_endings, text)
            sentences = [s.strip() for s in sentences if s.strip()]

            chunks = []
            chunk_index = 0

            for i in range(0, len(sentences), sentences_per_chunk):
                chunk_sentences = sentences[i:i + sentences_per_chunk]
                chunk_text = '。'.join(chunk_sentences) + '。'

                chunk = {
                    'chunk_index': chunk_index,
                    'text': chunk_text,
                    'sentence_count': len(chunk_sentences),
                    'char_count': len(chunk_text),
                    'word_count': len(chunk_text.split()),
                }

                if metadata:
                    chunk['metadata'] = metadata

                chunks.append(chunk)
                chunk_index += 1

            logger.info(f"Created {len(chunks)} sentence-based chunks")
            return chunks

        except Exception as e:
            logger.error(f"Error in sentence chunking: {e}")
            raise PDFProcessingError(f"Failed to chunk by sentence: {str(e)}")

    def chunk_by_page(
        self,
        pages_data: List[Dict[str, Any]],
        merge_small_pages: bool = True,
        min_page_chars: int = 200
    ) -> List[Dict[str, Any]]:
        """
        按页面分块

        Args:
            pages_data: 页面数据列表（来自 PDFExtractor）
            merge_small_pages: 是否合并过小的页面
            min_page_chars: 最小页面字符数

        Returns:
            分块列表
        """
        try:
            chunks = []
            chunk_index = 0
            current_merge = None

            for page_data in pages_data:
                text = page_data.get('text', '').strip()
                if not text:
                    continue

                # 如果需要合并小页面
                if merge_small_pages and len(text) < min_page_chars:
                    if current_merge is None:
                        current_merge = {
                            'pages': [page_data['page_number']],
                            'text': text,
                            'start_page': page_data['page_number']
                        }
                    else:
                        current_merge['pages'].append(page_data['page_number'])
                        current_merge['text'] += '\n\n' + text

                    # 如果合并后达到最小大小，保存
                    if len(current_merge['text']) >= min_page_chars:
                        chunk = {
                            'chunk_index': chunk_index,
                            'text': current_merge['text'],
                            'page_numbers': current_merge['pages'],
                            'start_page': current_merge['start_page'],
                            'end_page': current_merge['pages'][-1],
                            'char_count': len(current_merge['text']),
                            'word_count': len(current_merge['text'].split()),
                        }
                        chunks.append(chunk)
                        chunk_index += 1
                        current_merge = None
                else:
                    # 保存之前合并的内容
                    if current_merge:
                        chunk = {
                            'chunk_index': chunk_index,
                            'text': current_merge['text'],
                            'page_numbers': current_merge['pages'],
                            'start_page': current_merge['start_page'],
                            'end_page': current_merge['pages'][-1],
                            'char_count': len(current_merge['text']),
                            'word_count': len(current_merge['text'].split()),
                        }
                        chunks.append(chunk)
                        chunk_index += 1
                        current_merge = None

                    # 创建单页块
                    chunk = {
                        'chunk_index': chunk_index,
                        'text': text,
                        'page_numbers': [page_data['page_number']],
                        'start_page': page_data['page_number'],
                        'end_page': page_data['page_number'],
                        'char_count': len(text),
                        'word_count': len(text.split()),
                    }
                    chunks.append(chunk)
                    chunk_index += 1

            # 保存最后的合并内容
            if current_merge:
                chunk = {
                    'chunk_index': chunk_index,
                    'text': current_merge['text'],
                    'page_numbers': current_merge['pages'],
                    'start_page': current_merge['start_page'],
                    'end_page': current_merge['pages'][-1],
                    'char_count': len(current_merge['text']),
                    'word_count': len(current_merge['text'].split()),
                }
                chunks.append(chunk)

            logger.info(f"Created {len(chunks)} page-based chunks")
            return chunks

        except Exception as e:
            logger.error(f"Error in page chunking: {e}")
            raise PDFProcessingError(f"Failed to chunk by page: {str(e)}")

    def chunk_smart(
        self,
        text: str,
        strategy: str = "hybrid",
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        智能分块（自动选择最佳策略）

        Args:
            text: 要分块的文本
            strategy: 策略 ('fixed', 'paragraph', 'sentence', 'hybrid')
            metadata: 额外的元数据

        Returns:
            分块列表
        """
        try:
            if strategy == "fixed":
                return self.chunk_by_fixed_size(text, metadata)
            elif strategy == "paragraph":
                return self.chunk_by_paragraph(text, metadata=metadata)
            elif strategy == "sentence":
                return self.chunk_by_sentence(text, metadata=metadata)
            elif strategy == "hybrid":
                # 混合策略：优先段落，段落过长时使用固定大小
                para_chunks = self.chunk_by_paragraph(text, metadata=metadata)

                # 检查是否有过大的块需要再分割
                final_chunks = []
                for chunk in para_chunks:
                    if chunk['char_count'] > self.chunk_size * 1.5:
                        # 过大的块使用固定大小再分割
                        sub_chunks = self.chunk_by_fixed_size(
                            chunk['text'],
                            metadata=chunk.get('metadata')
                        )
                        final_chunks.extend(sub_chunks)
                    else:
                        final_chunks.append(chunk)

                # 重新编号
                for i, chunk in enumerate(final_chunks):
                    chunk['chunk_index'] = i

                logger.info(f"Created {len(final_chunks)} hybrid chunks")
                return final_chunks
            else:
                logger.warning(
                    f"Unknown strategy '{strategy}', using fixed size")
                return self.chunk_by_fixed_size(text, metadata)

        except Exception as e:
            logger.error(f"Error in smart chunking: {e}")
            raise PDFProcessingError(f"Failed to chunk smartly: {str(e)}")
