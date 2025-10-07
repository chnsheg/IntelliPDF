"""
技术文档章节级分块器
专门针对技术教程、编程指南等文档
按章节、小节进行智能分块，保持知识点完整性
"""
from typing import List, Dict, Any, Optional, Tuple
import re

from loguru import logger

from ...core.exceptions import PDFProcessingError


class TechnicalDocChunker:
    """技术文档章节级智能分块器"""

    def __init__(self):
        """初始化技术文档分块器"""
        # 章节标题模式（按优先级排序）
        self.chapter_patterns = [
            # 中文章节: 第一章、第1章
            re.compile(
                r'^(第\s*[一二三四五六七八九十百\d]+\s*章)\s+(.{2,50})$', re.MULTILINE),
            # 英文章节: Chapter 1
            re.compile(
                r'^(Chapter\s+\d+)[:\s]+(.{2,50})$', re.MULTILINE | re.IGNORECASE),
        ]

        # 小节标题模式
        self.section_patterns = [
            # 数字编号: 1.1、1.1.1
            re.compile(r'^(\d+\.\d+(?:\.\d+)?)\s+(.{3,80})$', re.MULTILINE),
            # 中文编号: 一、二、
            re.compile(r'^([一二三四五六七八九十]+)[、.]\s*(.{2,60})$', re.MULTILINE),
            # 带括号: (1)、(一)
            re.compile(
                r'^[（(](\d+|[一二三四五六七八九十]+)[)）]\s*(.{2,60})$', re.MULTILINE),
        ]

        # 代码块模式
        self.code_patterns = {
            'c_function': re.compile(r'(int|void|char|float|double)\s+\w+\s*\([^)]*\)\s*\{', re.MULTILINE),
            'shell_command': re.compile(r'^[\$#]\s+(sudo|apt|cd|ls|mkdir|chmod|cat|echo|vim|gcc|make)\s', re.MULTILINE),
            'code_block': re.compile(r'```[\s\S]*?```', re.MULTILINE),
            'indented_code': re.compile(r'(^\s{4,}[\w#].*\n){3,}', re.MULTILINE),
        }

        logger.info(
            "Initialized TechnicalDocChunker for chapter-level chunking")

    def detect_headings(
        self,
        text: str
    ) -> List[Dict[str, Any]]:
        """
        检测所有章节和小节标题

        Args:
            text: 文档文本

        Returns:
            标题列表 [{'type': 'chapter/section', 'level': 1/2/3, 'number': '1.1', 'title': '...', 'pos': 100}]
        """
        headings = []

        # 1. 检测章节
        for pattern in self.chapter_patterns:
            for match in pattern.finditer(text):
                headings.append({
                    'type': 'chapter',
                    'level': 1,
                    'number': match.group(1).strip(),
                    'title': match.group(2).strip(),
                    'pos': match.start(),
                    'full_text': match.group(0).strip()
                })

        # 2. 检测小节
        for pattern in self.section_patterns:
            for match in pattern.finditer(text):
                number = match.group(1).strip()
                title = match.group(2).strip()

                # 判断级别
                if '.' in number:
                    dots = number.count('.')
                    level = min(dots + 1, 3)  # 1.1=level2, 1.1.1=level3
                else:
                    level = 2

                headings.append({
                    'type': 'section',
                    'level': level,
                    'number': number,
                    'title': title,
                    'pos': match.start(),
                    'full_text': match.group(0).strip()
                })

        # 按位置排序并去重
        headings.sort(key=lambda x: x['pos'])

        # 去重：如果两个标题位置很近（<50字符），保留更可能的那个
        unique_headings = []
        for heading in headings:
            if not unique_headings or heading['pos'] - unique_headings[-1]['pos'] > 50:
                unique_headings.append(heading)

        logger.info(
            f"Detected {len(unique_headings)} headings (chapters: {sum(1 for h in unique_headings if h['type']=='chapter')})")

        return unique_headings

    def detect_code_blocks(
        self,
        text: str
    ) -> List[Tuple[int, int, str]]:
        """
        检测代码块位置

        Args:
            text: 文档文本

        Returns:
            代码块列表 [(start, end, type)]
        """
        code_blocks = []

        for code_type, pattern in self.code_patterns.items():
            for match in pattern.finditer(text):
                code_blocks.append((match.start(), match.end(), code_type))

        # 按起始位置排序
        code_blocks.sort(key=lambda x: x[0])

        # 合并重叠的代码块
        merged_blocks = []
        for start, end, code_type in code_blocks:
            if merged_blocks and start <= merged_blocks[-1][1]:
                # 扩展上一个块
                merged_blocks[-1] = (merged_blocks[-1][0],
                                     max(merged_blocks[-1][1], end), merged_blocks[-1][2])
            else:
                merged_blocks.append((start, end, code_type))

        return merged_blocks

    def chunk_by_sections(
        self,
        text: str,
        structured_text: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        按章节和小节进行分块（核心方法）

        每个块包含一个完整的知识点：
        - 大章节（第X章）作为一个块
        - 小节（X.X）作为一个块
        - 包含该节下的所有内容（文本、代码）

        Args:
            text: 完整文档文本
            structured_text: 结构化文本（可选，包含页码信息）
            metadata: 额外元数据

        Returns:
            章节级分块列表
        """
        try:
            logger.info("Starting chapter-level chunking...")

            # 1. 检测所有标题
            headings = self.detect_headings(text)

            if not headings:
                logger.warning(
                    "No headings detected, falling back to fixed-size chunking")
                return self._fallback_chunking(text, metadata)

            # 2. 检测代码块
            code_blocks = self.detect_code_blocks(text)
            logger.info(f"Detected {len(code_blocks)} code blocks")

            # 3. 创建分块
            chunks = []
            text_length = len(text)

            for i, heading in enumerate(headings):
                # 确定块的范围
                start_pos = heading['pos']

                # 找到下一个同级或更高级的标题
                end_pos = text_length
                for next_heading in headings[i+1:]:
                    if next_heading['level'] <= heading['level']:
                        end_pos = next_heading['pos']
                        break

                # 提取块内容
                chunk_text = text[start_pos:end_pos].strip()

                # 跳过太短的块（可能是误检测）
                if len(chunk_text) < 100:
                    continue

                # 统计代码块
                code_count = sum(
                    1 for cb in code_blocks if start_pos <= cb[0] < end_pos)

                # 计算在哪些页面
                page_numbers = []
                if structured_text:
                    char_count = 0
                    for page in structured_text:
                        page_start = char_count
                        page_end = char_count + len(page['text'])

                        if page_start <= start_pos < page_end or page_start < end_pos <= page_end:
                            page_numbers.append(page['page_number'])

                        char_count = page_end

                # 创建块
                chunk = {
                    'chunk_index': len(chunks),
                    'type': heading['type'],  # 'chapter' or 'section'
                    'level': heading['level'],  # 1, 2, 3
                    'number': heading['number'],  # '1.1', '1.1.1'
                    'title': heading['title'],
                    'text': chunk_text,
                    'start_char': start_pos,
                    'end_char': end_pos,
                    'char_count': len(chunk_text),
                    'word_count': len(chunk_text.split()),
                    'code_blocks': code_count,
                    'has_code': code_count > 0,
                    'page_numbers': page_numbers,
                    'page_range': f"{min(page_numbers)}-{max(page_numbers)}" if page_numbers else None,
                }

                # 添加元数据
                if metadata:
                    chunk['metadata'] = metadata.copy()

                chunks.append(chunk)

                # 每处理100个块记录一次
                if (len(chunks) % 100) == 0:
                    logger.info(f"Processed {len(chunks)} chunks...")

            logger.info(f"Created {len(chunks)} chapter/section-level chunks")

            # 4. 分块统计
            chapter_count = sum(1 for c in chunks if c['type'] == 'chapter')
            section_count = sum(1 for c in chunks if c['type'] == 'section')
            logger.info(
                f"Chapters: {chapter_count}, Sections: {section_count}")

            return chunks

        except Exception as e:
            logger.error(f"Error in chapter-level chunking: {e}")
            raise PDFProcessingError(f"Failed to chunk by sections: {str(e)}")

    def _fallback_chunking(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        chunk_size: int = 2000
    ) -> List[Dict[str, Any]]:
        """
        降级分块策略（当检测不到章节时）

        Args:
            text: 文本
            metadata: 元数据
            chunk_size: 块大小

        Returns:
            分块列表
        """
        chunks = []
        start = 0
        chunk_index = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))

            # 在段落边界截断
            if end < len(text):
                last_para = text[start:end].rfind('\n\n')
                if last_para > chunk_size * 0.5:
                    end = start + last_para

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunk = {
                    'chunk_index': chunk_index,
                    'type': 'fixed',
                    'level': 0,
                    'title': f'Section {chunk_index + 1}',
                    'text': chunk_text,
                    'start_char': start,
                    'end_char': end,
                    'char_count': len(chunk_text),
                }

                if metadata:
                    chunk['metadata'] = metadata.copy()

                chunks.append(chunk)
                chunk_index += 1

            start = end

        logger.info(f"Fallback chunking created {len(chunks)} chunks")
        return chunks

    def get_chunk_context(
        self,
        chunks: List[Dict[str, Any]],
        chunk_index: int,
        include_before: int = 0,
        include_after: int = 0
    ) -> Dict[str, Any]:
        """
        获取块的上下文（前后章节）

        Args:
            chunks: 所有块
            chunk_index: 目标块索引
            include_before: 包含前N个块
            include_after: 包含后N个块

        Returns:
            包含上下文的块信息
        """
        if chunk_index < 0 or chunk_index >= len(chunks):
            raise ValueError(f"Invalid chunk_index: {chunk_index}")

        target_chunk = chunks[chunk_index]

        # 获取前后块
        before_chunks = chunks[max(
            0, chunk_index - include_before):chunk_index]
        after_chunks = chunks[chunk_index +
                              1:min(len(chunks), chunk_index + 1 + include_after)]

        return {
            'target': target_chunk,
            'before': before_chunks,
            'after': after_chunks,
            'context_text': '\n\n---\n\n'.join(
                [c['text'] for c in before_chunks] +
                [target_chunk['text']] +
                [c['text'] for c in after_chunks]
            )
        }
