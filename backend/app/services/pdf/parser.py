"""
PDF 解析器模块
支持多种 PDF 解析引擎：PyPDF2, pdfplumber, PyMuPDF
"""
from pathlib import Path
from typing import Dict, List, Optional, Any
import io

from loguru import logger
import PyPDF2
import pdfplumber
import fitz  # PyMuPDF

from ...core.exceptions import PDFProcessingError
from .cache import get_pdf_cache


class PDFParser:
    """PDF 解析器，支持多种解析引擎"""

    def __init__(self, pdf_path: str | Path, use_cache: bool = True):
        """
        初始化 PDF 解析器

        Args:
            pdf_path: PDF 文件路径
            use_cache: 是否使用缓存
        """
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        self.page_count: Optional[int] = None
        self.metadata: Optional[Dict[str, Any]] = {}
        self.use_cache = use_cache
        self.cache = get_pdf_cache() if use_cache else None

        logger.info(
            f"Initialized PDF parser for: {self.pdf_path.name} (cache={'enabled' if use_cache else 'disabled'})")

    def get_metadata(self) -> Dict[str, Any]:
        """
        获取 PDF 元数据（支持缓存）

        Returns:
            包含元数据的字典
        """
        # 尝试从缓存加载
        if self.use_cache and self.cache:
            cached_metadata = self.cache.load_metadata(self.pdf_path)
            if cached_metadata:
                logger.info(
                    f"✅ Loaded metadata from cache for: {self.pdf_path.name}")
                self.metadata = cached_metadata
                self.page_count = cached_metadata.get('page_count')
                return cached_metadata

        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)

                metadata = {
                    'page_count': len(pdf_reader.pages),
                    'title': pdf_reader.metadata.get('/Title', '') if pdf_reader.metadata else '',
                    'author': pdf_reader.metadata.get('/Author', '') if pdf_reader.metadata else '',
                    'subject': pdf_reader.metadata.get('/Subject', '') if pdf_reader.metadata else '',
                    'creator': pdf_reader.metadata.get('/Creator', '') if pdf_reader.metadata else '',
                    'producer': pdf_reader.metadata.get('/Producer', '') if pdf_reader.metadata else '',
                    'creation_date': pdf_reader.metadata.get('/CreationDate', '') if pdf_reader.metadata else '',
                    'modification_date': pdf_reader.metadata.get('/ModDate', '') if pdf_reader.metadata else '',
                }

                self.page_count = metadata['page_count']
                self.metadata = metadata

                # 保存到缓存
                if self.use_cache and self.cache:
                    self.cache.save_metadata(self.pdf_path, metadata)
                    logger.info(f"💾 Saved metadata to cache")

                logger.info(
                    f"Extracted metadata: {metadata['page_count']} pages")
                return metadata

        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            raise PDFProcessingError(
                f"Failed to extract PDF metadata: {str(e)}")

    def extract_text_pypdf2(self, page_numbers: Optional[List[int]] = None) -> Dict[int, str]:
        """
        使用 PyPDF2 提取文本（快速但准确度较低）

        Args:
            page_numbers: 要提取的页码列表，None 表示全部页面

        Returns:
            页码到文本的映射
        """
        try:
            text_by_page = {}

            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)

                pages_to_extract = page_numbers if page_numbers else range(
                    total_pages)

                for page_num in pages_to_extract:
                    if page_num >= total_pages:
                        logger.warning(
                            f"Page {page_num} exceeds total pages {total_pages}")
                        continue

                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    text_by_page[page_num] = text

                logger.info(
                    f"Extracted text from {len(text_by_page)} pages using PyPDF2")
                return text_by_page

        except Exception as e:
            logger.error(f"Error extracting text with PyPDF2: {e}")
            raise PDFProcessingError(
                f"Failed to extract text with PyPDF2: {str(e)}")

    def extract_text_pdfplumber(self, page_numbers: Optional[List[int]] = None) -> Dict[int, str]:
        """
        使用 pdfplumber 提取文本（准确度高，支持表格）

        Args:
            page_numbers: 要提取的页码列表，None 表示全部页面

        Returns:
            页码到文本的映射
        """
        try:
            text_by_page = {}

            with pdfplumber.open(self.pdf_path) as pdf:
                total_pages = len(pdf.pages)
                pages_to_extract = page_numbers if page_numbers else range(
                    total_pages)

                for page_num in pages_to_extract:
                    if page_num >= total_pages:
                        logger.warning(
                            f"Page {page_num} exceeds total pages {total_pages}")
                        continue

                    page = pdf.pages[page_num]
                    text = page.extract_text() or ""
                    text_by_page[page_num] = text

                logger.info(
                    f"Extracted text from {len(text_by_page)} pages using pdfplumber")
                return text_by_page

        except Exception as e:
            logger.error(f"Error extracting text with pdfplumber: {e}")
            raise PDFProcessingError(
                f"Failed to extract text with pdfplumber: {str(e)}")

    def extract_text_pymupdf(self, page_numbers: Optional[List[int]] = None) -> Dict[int, str]:
        """
        使用 PyMuPDF 提取文本（速度快，准确度高）

        Args:
            page_numbers: 要提取的页码列表，None 表示全部页面

        Returns:
            页码到文本的映射
        """
        try:
            text_by_page = {}

            doc = fitz.open(self.pdf_path)
            total_pages = len(doc)
            pages_to_extract = page_numbers if page_numbers else range(
                total_pages)

            for page_num in pages_to_extract:
                if page_num >= total_pages:
                    logger.warning(
                        f"Page {page_num} exceeds total pages {total_pages}")
                    continue

                page = doc[page_num]
                text = page.get_text()
                text_by_page[page_num] = text

            doc.close()

            logger.info(
                f"Extracted text from {len(text_by_page)} pages using PyMuPDF")
            return text_by_page

        except Exception as e:
            logger.error(f"Error extracting text with PyMuPDF: {e}")
            raise PDFProcessingError(
                f"Failed to extract text with PyMuPDF: {str(e)}")

    def extract_text(
        self,
        engine: str = "pymupdf",
        page_numbers: Optional[List[int]] = None
    ) -> Dict[int, str]:
        """
        提取 PDF 文本（自动选择最佳引擎）

        Args:
            engine: 解析引擎 ('pypdf2', 'pdfplumber', 'pymupdf')
            page_numbers: 要提取的页码列表，None 表示全部页面

        Returns:
            页码到文本的映射
        """
        engine = engine.lower()

        if engine == "pypdf2":
            return self.extract_text_pypdf2(page_numbers)
        elif engine == "pdfplumber":
            return self.extract_text_pdfplumber(page_numbers)
        elif engine == "pymupdf":
            return self.extract_text_pymupdf(page_numbers)
        else:
            logger.warning(
                f"Unknown engine '{engine}', falling back to pymupdf")
            return self.extract_text_pymupdf(page_numbers)

    def extract_tables(self, page_numbers: Optional[List[int]] = None) -> Dict[int, List[List[str]]]:
        """
        使用 pdfplumber 提取表格

        Args:
            page_numbers: 要提取的页码列表，None 表示全部页面

        Returns:
            页码到表格列表的映射
        """
        try:
            tables_by_page = {}

            with pdfplumber.open(self.pdf_path) as pdf:
                total_pages = len(pdf.pages)
                pages_to_extract = page_numbers if page_numbers else range(
                    total_pages)

                for page_num in pages_to_extract:
                    if page_num >= total_pages:
                        continue

                    page = pdf.pages[page_num]
                    tables = page.extract_tables()

                    if tables:
                        tables_by_page[page_num] = tables

                logger.info(
                    f"Extracted tables from {len(tables_by_page)} pages")
                return tables_by_page

        except Exception as e:
            logger.error(f"Error extracting tables: {e}")
            raise PDFProcessingError(f"Failed to extract tables: {str(e)}")

    def extract_images(self, page_numbers: Optional[List[int]] = None) -> Dict[int, List[Dict[str, Any]]]:
        """
        使用 PyMuPDF 提取图片信息

        Args:
            page_numbers: 要提取的页码列表，None 表示全部页面

        Returns:
            页码到图片信息列表的映射
        """
        try:
            images_by_page = {}

            doc = fitz.open(self.pdf_path)
            total_pages = len(doc)
            pages_to_extract = page_numbers if page_numbers else range(
                total_pages)

            for page_num in pages_to_extract:
                if page_num >= total_pages:
                    continue

                page = doc[page_num]
                image_list = page.get_images(full=True)

                if image_list:
                    page_images = []
                    for img_index, img_info in enumerate(image_list):
                        xref = img_info[0]
                        base_image = doc.extract_image(xref)

                        image_data = {
                            'index': img_index,
                            'xref': xref,
                            'width': base_image['width'],
                            'height': base_image['height'],
                            'colorspace': base_image.get('colorspace'),
                            'bpc': base_image.get('bpc'),
                            'ext': base_image['ext'],
                            'size': len(base_image['image'])
                        }
                        page_images.append(image_data)

                    images_by_page[page_num] = page_images

            doc.close()

            logger.info(
                f"Extracted images metadata from {len(images_by_page)} pages")
            return images_by_page

        except Exception as e:
            logger.error(f"Error extracting images: {e}")
            raise PDFProcessingError(f"Failed to extract images: {str(e)}")

    def get_page_dimensions(self) -> Dict[int, Dict[str, float]]:
        """
        获取所有页面的尺寸

        Returns:
            页码到尺寸信息的映射
        """
        try:
            dimensions = {}

            doc = fitz.open(self.pdf_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                rect = page.rect

                dimensions[page_num] = {
                    'width': rect.width,
                    'height': rect.height,
                    'x0': rect.x0,
                    'y0': rect.y0,
                    'x1': rect.x1,
                    'y1': rect.y1
                }

            doc.close()

            return dimensions

        except Exception as e:
            logger.error(f"Error getting page dimensions: {e}")
            raise PDFProcessingError(
                f"Failed to get page dimensions: {str(e)}")

    def parse_full(self, engine: str = "pymupdf") -> Dict[str, Any]:
        """
        完整解析 PDF，提取所有信息

        Args:
            engine: 文本提取引擎

        Returns:
            包含所有解析信息的字典
        """
        try:
            logger.info(f"Starting full PDF parsing with engine: {engine}")

            result = {
                'metadata': self.get_metadata(),
                'text_by_page': self.extract_text(engine=engine),
                'tables_by_page': self.extract_tables(),
                'images_by_page': self.extract_images(),
                'dimensions': self.get_page_dimensions()
            }

            # 统计信息
            total_text_length = sum(len(text)
                                    for text in result['text_by_page'].values())
            total_tables = sum(len(tables)
                               for tables in result['tables_by_page'].values())
            total_images = sum(len(images)
                               for images in result['images_by_page'].values())

            result['statistics'] = {
                'total_pages': result['metadata']['page_count'],
                'total_text_length': total_text_length,
                'total_tables': total_tables,
                'total_images': total_images,
                'pages_with_text': len(result['text_by_page']),
                'pages_with_tables': len(result['tables_by_page']),
                'pages_with_images': len(result['images_by_page'])
            }

            logger.info(f"PDF parsing complete: {result['statistics']}")
            return result

        except Exception as e:
            logger.error(f"Error in full PDF parsing: {e}")
            raise PDFProcessingError(f"Failed to parse PDF: {str(e)}")
