"""
章节级别的智能分块器
针对技术文档（如 Linux 教程）优化，按章节和小节进行分块
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
import re

from loguru import logger

from .cache import get_pdf_cache


class SectionChunker:
    """章节级别的智能分块器"""

    def __init__(self, use_cache: bool = True):
        """
        初始化章节分块器

        Args:
            use_cache: 是否使用缓存
        """
        self.use_cache = use_cache
        self.cache = get_pdf_cache() if use_cache else None

        # 章节标题模式（支持多种格式）
        self.chapter_patterns = [
            r'^第\s*[一二三四五六七八九十\d]+\s*章',  # 第一章、第1章
            r'^Chapter\s+\d+',  # Chapter 1
            r'^\d+\.\s+[A-Z]',  # 1. Introduction
            r'^[A-Z][A-Z\s]+$',  # 全大写标题
        ]

        # 小节标题模式
        self.section_patterns = [
            r'^\d+\.\d+\s+',  # 1.1
            r'^\d+\.\d+\.\d+\s+',  # 1.1.1
            r'^[A-Z]\.\s+',  # A.
            r'^\([一二三四五六七八九十\d]+\)',  # (一) (1)
        ]

        logger.info("Initialized SectionChunker")

    def chunk_by_sections(
        self,
        structured_text: List[Dict[str, Any]],
        pdf_path: Optional[Path] = None,
        min_section_length: int = 100,
        max_section_length: int = 5000
    ) -> List[Dict[str, Any]]:
        """
        按章节和小节进行分块（支持缓存）

        Args:
            structured_text: 结构化文本列表（每页一个元素）
            pdf_path: PDF 文件路径（用于缓存）
            min_section_length: 最小小节长度
            max_section_length: 最大小节长度

        Returns:
            章节分块列表
        """
        # 尝试从缓存加载
        if self.use_cache and self.cache and pdf_path:
            cached_chunks = self.cache.load_chunks(
                pdf_path, chunk_strategy="section")
            if cached_chunks:
                logger.info(
                    f"✅ Loaded section chunks from cache ({len(cached_chunks)} chunks)")
                return cached_chunks

        try:
            chunks = []
            current_chapter = None
            current_section = None
            current_content = []
            current_pages = []
            chunk_index = 0

            # 合并所有页面文本
            all_text = ""
            page_map = {}  # 字符位置 -> 页码映射
            char_pos = 0

            for page_data in structured_text:
                page_num = page_data['page_index']
                page_text = page_data['text']

                # 记录每个字符的页码
                for char in page_text:
                    page_map[char_pos] = page_num
                    char_pos += 1

                all_text += page_text + "\n\n"
                char_pos += 2  # 添加的 \n\n

            # 按行分割
            lines = all_text.split('\n')
            line_start_pos = 0

            for line in lines:
                line = line.strip()

                if not line:
                    line_start_pos += 1
                    continue

                # 检测是否为章节标题
                is_chapter = self._is_chapter_title(line)
                is_section = self._is_section_title(line)

                if is_chapter:
                    # 保存上一个分块
                    if current_content and len(''.join(current_content)) >= min_section_length:
                        chunk = self._create_chunk(
                            content=''.join(current_content),
                            chapter=current_chapter,
                            section=current_section,
                            pages=current_pages,
                            index=chunk_index
                        )
                        chunks.append(chunk)
                        chunk_index += 1

                    # 开始新章节
                    current_chapter = line
                    current_section = None
                    current_content = [f"# {line}\n\n"]
                    current_pages = [page_map.get(line_start_pos, 0)]

                elif is_section:
                    # 保存上一个小节
                    if current_content and len(''.join(current_content)) >= min_section_length:
                        chunk = self._create_chunk(
                            content=''.join(current_content),
                            chapter=current_chapter,
                            section=current_section,
                            pages=current_pages,
                            index=chunk_index
                        )
                        chunks.append(chunk)
                        chunk_index += 1

                        # 如果当前块太长，分割
                        if chunk['char_count'] > max_section_length:
                            chunks.extend(self._split_large_chunk(
                                chunk, max_section_length))

                    # 开始新小节
                    current_section = line
                    current_content = [f"## {line}\n\n"]
                    current_pages = [page_map.get(line_start_pos, 0)]

                else:
                    # 普通内容
                    current_content.append(line + '\n')
                    page_num = page_map.get(line_start_pos, 0)
                    if not current_pages or current_pages[-1] != page_num:
                        current_pages.append(page_num)

                line_start_pos += len(line) + 1

            # 保存最后一个分块
            if current_content and len(''.join(current_content)) >= min_section_length:
                chunk = self._create_chunk(
                    content=''.join(current_content),
                    chapter=current_chapter,
                    section=current_section,
                    pages=current_pages,
                    index=chunk_index
                )
                chunks.append(chunk)

            logger.info(f"Created {len(chunks)} section-based chunks")

            # 添加统计信息
            for chunk in chunks:
                chunk['total_chunks'] = len(chunks)

            # 保存到缓存
            if self.use_cache and self.cache and pdf_path:
                self.cache.save_chunks(
                    pdf_path, chunks, chunk_strategy="section")
                logger.info(f"💾 Saved section chunks to cache")

            return chunks

        except Exception as e:
            logger.error(f"Error in section chunking: {e}")
            return []

    def _is_chapter_title(self, line: str) -> bool:
        """判断是否为章节标题"""
        for pattern in self.chapter_patterns:
            if re.match(pattern, line):
                return True
        return False

    def _is_section_title(self, line: str) -> bool:
        """判断是否为小节标题"""
        for pattern in self.section_patterns:
            if re.match(pattern, line):
                return True
        return False

    def _create_chunk(
        self,
        content: str,
        chapter: Optional[str],
        section: Optional[str],
        pages: List[int],
        index: int
    ) -> Dict[str, Any]:
        """创建分块"""
        return {
            'chunk_index': index,
            'text': content.strip(),
            'char_count': len(content),
            'word_count': len(content.split()),
            'chapter': chapter or "Unknown Chapter",
            'section': section or "Introduction",
            'page_numbers': list(set(pages)),
            'page_range': f"{min(pages)}-{max(pages)}" if pages else "0",
            'metadata': {
                'chapter': chapter,
                'section': section,
                'pages': sorted(set(pages)),
                'type': 'section_chunk'
            }
        }

    def _split_large_chunk(
        self,
        chunk: Dict[str, Any],
        max_length: int
    ) -> List[Dict[str, Any]]:
        """分割过大的块"""
        content = chunk['text']
        if len(content) <= max_length:
            return [chunk]

        # 按段落分割
        paragraphs = content.split('\n\n')
        sub_chunks = []
        current_chunk = []
        current_length = 0

        for para in paragraphs:
            para_length = len(para)

            if current_length + para_length > max_length and current_chunk:
                # 创建子块
                sub_chunk = chunk.copy()
                sub_chunk['text'] = '\n\n'.join(current_chunk)
                sub_chunk['char_count'] = current_length
                sub_chunk['is_split'] = True
                sub_chunks.append(sub_chunk)

                current_chunk = [para]
                current_length = para_length
            else:
                current_chunk.append(para)
                current_length += para_length + 2  # +2 for \n\n

        # 添加最后一个子块
        if current_chunk:
            sub_chunk = chunk.copy()
            sub_chunk['text'] = '\n\n'.join(current_chunk)
            sub_chunk['char_count'] = current_length
            sub_chunk['is_split'] = True
            sub_chunks.append(sub_chunk)

        logger.info(f"Split large chunk into {len(sub_chunks)} sub-chunks")
        return sub_chunks

    def get_chunk_summary(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取分块摘要统计

        Args:
            chunks: 分块列表

        Returns:
            统计信息
        """
        if not chunks:
            return {}

        chapters = set()
        sections = set()
        total_chars = 0
        total_pages = set()

        for chunk in chunks:
            if chunk.get('chapter'):
                chapters.add(chunk['chapter'])
            if chunk.get('section'):
                sections.add(chunk['section'])
            total_chars += chunk.get('char_count', 0)
            total_pages.update(chunk.get('page_numbers', []))

        return {
            'total_chunks': len(chunks),
            'total_chapters': len(chapters),
            'total_sections': len(sections),
            'total_characters': total_chars,
            'total_pages': len(total_pages),
            'avg_chunk_size': total_chars // len(chunks) if chunks else 0,
            'chapters': sorted(list(chapters)),
            'pages_covered': sorted(list(total_pages))
        }
