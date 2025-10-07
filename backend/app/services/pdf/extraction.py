"""
PDF 内容提取服务
提供结构化的文本、表格、图片提取功能
"""
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import re

from loguru import logger

from .parser import PDFParser
from .cache import get_pdf_cache
from ...core.exceptions import PDFProcessingError


class PDFExtractor:
    """PDF 内容提取器"""

    def __init__(self, pdf_path: str | Path, use_cache: bool = True):
        """
        初始化提取器

        Args:
            pdf_path: PDF 文件路径
            use_cache: 是否使用缓存
        """
        self.parser = PDFParser(pdf_path, use_cache=use_cache)
        self.pdf_path = Path(pdf_path)
        self.use_cache = use_cache
        self.cache = get_pdf_cache() if use_cache else None

    def extract_structured_text(
        self,
        preserve_formatting: bool = True,
        clean_text: bool = True
    ) -> List[Dict[str, Any]]:
        """
        提取结构化文本，每页作为一个结构化单元（支持缓存）

        Args:
            preserve_formatting: 是否保留格式（换行、缩进等）
            clean_text: 是否清理文本（去除多余空白、特殊字符等）

        Returns:
            结构化文本列表
        """
        # 尝试从缓存加载
        if self.use_cache and self.cache:
            cached_text = self.cache.load_structured_text(self.pdf_path)
            if cached_text:
                logger.info(
                    f"✅ Loaded structured text from cache ({len(cached_text)} pages)")
                return cached_text

        try:
            text_by_page = self.parser.extract_text(engine="pymupdf")
            dimensions = self.parser.get_page_dimensions()

            structured_content = []

            for page_num, raw_text in text_by_page.items():
                # 清理文本
                text = self._clean_text(raw_text) if clean_text else raw_text

                if not text.strip():
                    continue

                # 构建结构化数据
                page_data = {
                    'page_number': page_num + 1,  # 从 1 开始计数
                    'page_index': page_num,
                    'text': text,
                    'char_count': len(text),
                    'word_count': len(text.split()),
                    'line_count': len(text.split('\n')),
                    'dimensions': dimensions.get(page_num, {})
                }

                # 提取页面标题（启发式：第一行非空文本）
                lines = [line.strip()
                         for line in text.split('\n') if line.strip()]
                if lines:
                    page_data['first_line'] = lines[0]
                    page_data['has_content'] = True
                else:
                    page_data['has_content'] = False

                structured_content.append(page_data)

            # 保存到缓存
            if self.use_cache and self.cache:
                self.cache.save_structured_text(
                    self.pdf_path, structured_content)
                logger.info(f"💾 Saved structured text to cache")

            logger.info(
                f"Extracted structured text from {len(structured_content)} pages")
            return structured_content

        except Exception as e:
            logger.error(f"Error extracting structured text: {e}")
            raise PDFProcessingError(
                f"Failed to extract structured text: {str(e)}")

    def _clean_text(self, text: str) -> str:
        """
        清理文本

        Args:
            text: 原始文本

        Returns:
            清理后的文本
        """
        if not text:
            return ""

        # 统一换行符
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # 移除多余的空白行（连续3个以上换行符压缩为2个）
        text = re.sub(r'\n{3,}', '\n\n', text)

        # 移除行尾空白
        text = '\n'.join(line.rstrip() for line in text.split('\n'))

        # 移除 PDF 特殊字符和控制字符
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', text)

        return text

    def extract_sections(
        self,
        title_patterns: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        提取文档章节（基于标题模式）

        Args:
            title_patterns: 标题匹配模式列表（正则表达式）

        Returns:
            章节列表
        """
        try:
            # 默认标题模式
            if title_patterns is None:
                title_patterns = [
                    r'^第[一二三四五六七八九十\d]+章\s+.+$',  # 第X章
                    r'^\d+\.\s+.+$',  # 1. 标题
                    r'^\d+\.\d+\s+.+$',  # 1.1 标题
                    r'^[A-Z\u4e00-\u9fa5]{2,20}$',  # 全大写或中文标题
                ]

            compiled_patterns = [re.compile(
                pattern, re.MULTILINE) for pattern in title_patterns]

            text_by_page = self.parser.extract_text(engine="pymupdf")
            sections = []
            current_section = None

            for page_num in sorted(text_by_page.keys()):
                text = text_by_page[page_num]
                lines = text.split('\n')

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    # 检查是否匹配标题模式
                    is_title = False
                    for pattern in compiled_patterns:
                        if pattern.match(line):
                            is_title = True
                            break

                    if is_title:
                        # 保存上一个章节
                        if current_section and current_section.get('content'):
                            sections.append(current_section)

                        # 开始新章节
                        current_section = {
                            'title': line,
                            'start_page': page_num + 1,
                            'content': []
                        }
                    elif current_section is not None:
                        # 添加内容到当前章节
                        current_section['content'].append(line)

            # 添加最后一个章节
            if current_section and current_section.get('content'):
                sections.append(current_section)

            # 计算章节统计
            for section in sections:
                section['content_text'] = '\n'.join(section['content'])
                section['char_count'] = len(section['content_text'])
                section['word_count'] = len(section['content_text'].split())
                del section['content']  # 移除临时数组

            logger.info(f"Extracted {len(sections)} sections")
            return sections

        except Exception as e:
            logger.error(f"Error extracting sections: {e}")
            raise PDFProcessingError(f"Failed to extract sections: {str(e)}")

    def extract_tables_formatted(self) -> List[Dict[str, Any]]:
        """
        提取格式化的表格数据

        Returns:
            表格列表，每个表格包含元数据和数据
        """
        try:
            tables_by_page = self.parser.extract_tables()
            formatted_tables = []

            for page_num, page_tables in tables_by_page.items():
                for table_index, table_data in enumerate(page_tables):
                    if not table_data:
                        continue

                    # 分析表格结构
                    row_count = len(table_data)
                    col_count = len(table_data[0]) if table_data else 0

                    # 提取表头（假设第一行是表头）
                    headers = table_data[0] if table_data else []
                    data_rows = table_data[1:] if len(table_data) > 1 else []

                    formatted_table = {
                        'page_number': page_num + 1,
                        'page_index': page_num,
                        'table_index': table_index,
                        'row_count': row_count,
                        'column_count': col_count,
                        'headers': headers,
                        'data': data_rows,
                        'has_headers': bool(headers and any(h for h in headers if h)),
                    }

                    formatted_tables.append(formatted_table)

            logger.info(f"Extracted {len(formatted_tables)} formatted tables")
            return formatted_tables

        except Exception as e:
            logger.error(f"Error extracting formatted tables: {e}")
            raise PDFProcessingError(
                f"Failed to extract formatted tables: {str(e)}")

    def extract_metadata_enhanced(self) -> Dict[str, Any]:
        """
        提取增强的元数据（包括内容分析）

        Returns:
            增强元数据字典
        """
        try:
            # 基础元数据
            metadata = self.parser.get_metadata()

            # 内容统计
            text_by_page = self.parser.extract_text(engine="pymupdf")
            all_text = ' '.join(text_by_page.values())

            # 语言检测（简单的启发式）
            chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', all_text))
            english_chars = len(re.findall(r'[a-zA-Z]', all_text))
            total_chars = len(all_text.strip())

            if chinese_chars > english_chars:
                language = 'zh'
                language_confidence = chinese_chars / total_chars if total_chars > 0 else 0
            else:
                language = 'en'
                language_confidence = english_chars / total_chars if total_chars > 0 else 0

            # 内容类型检测
            has_tables = bool(self.parser.extract_tables())
            has_images = bool(self.parser.extract_images())

            # 增强元数据
            metadata['content_analysis'] = {
                'total_characters': total_chars,
                'chinese_characters': chinese_chars,
                'english_characters': english_chars,
                'detected_language': language,
                'language_confidence': round(language_confidence, 3),
                'has_tables': has_tables,
                'has_images': has_images,
                'avg_chars_per_page': total_chars // metadata['page_count'] if metadata['page_count'] > 0 else 0
            }

            logger.info(f"Enhanced metadata: {metadata['content_analysis']}")
            return metadata

        except Exception as e:
            logger.error(f"Error extracting enhanced metadata: {e}")
            raise PDFProcessingError(
                f"Failed to extract enhanced metadata: {str(e)}")

    def extract_all(self) -> Dict[str, Any]:
        """
        提取所有内容（一站式提取）

        Returns:
            包含所有提取内容的字典
        """
        try:
            logger.info(
                f"Starting comprehensive extraction for {self.pdf_path.name}")

            result = {
                'metadata': self.extract_metadata_enhanced(),
                'structured_text': self.extract_structured_text(),
                'sections': self.extract_sections(),
                'tables': self.extract_tables_formatted(),
            }

            # 统计摘要
            result['summary'] = {
                'total_pages': result['metadata']['page_count'],
                'pages_with_text': len(result['structured_text']),
                'total_sections': len(result['sections']),
                'total_tables': len(result['tables']),
                'total_characters': result['metadata']['content_analysis']['total_characters'],
                'detected_language': result['metadata']['content_analysis']['detected_language']
            }

            logger.info(
                f"Comprehensive extraction complete: {result['summary']}")
            return result

        except Exception as e:
            logger.error(f"Error in comprehensive extraction: {e}")
            raise PDFProcessingError(
                f"Failed to extract all content: {str(e)}")
