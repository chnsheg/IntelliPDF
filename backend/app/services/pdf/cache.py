"""
PDF 解析结果缓存服务
实现解析结果的持久化存储，避免重复解析
"""
import hashlib
import json
import pickle
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from loguru import logger


class PDFParseCache:
    """PDF 解析结果缓存管理器"""

    def __init__(self, cache_dir: str = "./data/pdf_cache"):
        """
        初始化缓存管理器

        Args:
            cache_dir: 缓存目录路径
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 创建子目录
        self.metadata_dir = self.cache_dir / "metadata"
        self.chunks_dir = self.cache_dir / "chunks"
        self.structured_text_dir = self.cache_dir / "structured_text"

        for dir_path in [self.metadata_dir, self.chunks_dir, self.structured_text_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized PDF cache at: {self.cache_dir}")

    def _get_file_hash(self, file_path: Path) -> str:
        """
        计算文件的 SHA-256 哈希值

        Args:
            file_path: 文件路径

        Returns:
            文件哈希值
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _get_cache_key(self, file_path: Path, operation: str) -> str:
        """
        生成缓存键

        Args:
            file_path: PDF 文件路径
            operation: 操作类型 (metadata/chunks/structured_text)

        Returns:
            缓存键 (文件哈希 + 操作类型)
        """
        file_hash = self._get_file_hash(file_path)
        return f"{file_hash}_{operation}"

    def save_metadata(
        self,
        file_path: Path,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        保存文档元数据

        Args:
            file_path: PDF 文件路径
            metadata: 元数据字典

        Returns:
            是否保存成功
        """
        try:
            cache_key = self._get_cache_key(file_path, "metadata")
            cache_file = self.metadata_dir / f"{cache_key}.json"

            # 添加缓存时间戳
            cache_data = {
                "file_path": str(file_path),
                "file_hash": self._get_file_hash(file_path),
                "cached_at": datetime.now().isoformat(),
                "metadata": metadata
            }

            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)

            logger.info(f"Saved metadata cache: {cache_key}")
            return True

        except Exception as e:
            logger.error(f"Failed to save metadata cache: {e}")
            return False

    def load_metadata(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        加载文档元数据

        Args:
            file_path: PDF 文件路径

        Returns:
            元数据字典，如果不存在则返回 None
        """
        try:
            cache_key = self._get_cache_key(file_path, "metadata")
            cache_file = self.metadata_dir / f"{cache_key}.json"

            if not cache_file.exists():
                logger.debug(f"Metadata cache not found: {cache_key}")
                return None

            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            # 验证文件哈希
            current_hash = self._get_file_hash(file_path)
            if cache_data.get("file_hash") != current_hash:
                logger.warning(
                    f"File hash mismatch, cache invalid: {cache_key}")
                cache_file.unlink()  # 删除无效缓存
                return None

            logger.info(f"Loaded metadata cache: {cache_key}")
            return cache_data["metadata"]

        except Exception as e:
            logger.error(f"Failed to load metadata cache: {e}")
            return None

    def save_chunks(
        self,
        file_path: Path,
        chunks: List[Dict[str, Any]],
        chunk_strategy: str = "section"
    ) -> bool:
        """
        保存文档分块结果

        Args:
            file_path: PDF 文件路径
            chunks: 分块列表
            chunk_strategy: 分块策略名称

        Returns:
            是否保存成功
        """
        try:
            cache_key = self._get_cache_key(
                file_path, f"chunks_{chunk_strategy}")
            cache_file = self.chunks_dir / f"{cache_key}.pkl"

            # 使用 pickle 存储以保留对象结构
            cache_data = {
                "file_path": str(file_path),
                "file_hash": self._get_file_hash(file_path),
                "cached_at": datetime.now().isoformat(),
                "chunk_strategy": chunk_strategy,
                "chunk_count": len(chunks),
                "chunks": chunks
            }

            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)

            logger.info(
                f"Saved chunks cache: {cache_key} ({len(chunks)} chunks)")
            return True

        except Exception as e:
            logger.error(f"Failed to save chunks cache: {e}")
            return False

    def load_chunks(
        self,
        file_path: Path,
        chunk_strategy: str = "section"
    ) -> Optional[List[Dict[str, Any]]]:
        """
        加载文档分块结果

        Args:
            file_path: PDF 文件路径
            chunk_strategy: 分块策略名称

        Returns:
            分块列表，如果不存在则返回 None
        """
        try:
            cache_key = self._get_cache_key(
                file_path, f"chunks_{chunk_strategy}")
            cache_file = self.chunks_dir / f"{cache_key}.pkl"

            if not cache_file.exists():
                logger.debug(f"Chunks cache not found: {cache_key}")
                return None

            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)

            # 验证文件哈希
            current_hash = self._get_file_hash(file_path)
            if cache_data.get("file_hash") != current_hash:
                logger.warning(
                    f"File hash mismatch, cache invalid: {cache_key}")
                cache_file.unlink()
                return None

            chunks = cache_data["chunks"]
            logger.info(
                f"Loaded chunks cache: {cache_key} ({len(chunks)} chunks)")
            return chunks

        except Exception as e:
            logger.error(f"Failed to load chunks cache: {e}")
            return None

    def save_structured_text(
        self,
        file_path: Path,
        structured_text: List[Dict[str, Any]]
    ) -> bool:
        """
        保存结构化文本

        Args:
            file_path: PDF 文件路径
            structured_text: 结构化文本列表

        Returns:
            是否保存成功
        """
        try:
            cache_key = self._get_cache_key(file_path, "structured_text")
            cache_file = self.structured_text_dir / f"{cache_key}.pkl"

            cache_data = {
                "file_path": str(file_path),
                "file_hash": self._get_file_hash(file_path),
                "cached_at": datetime.now().isoformat(),
                "page_count": len(structured_text),
                "structured_text": structured_text
            }

            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)

            logger.info(
                f"Saved structured text cache: {cache_key} ({len(structured_text)} pages)")
            return True

        except Exception as e:
            logger.error(f"Failed to save structured text cache: {e}")
            return False

    def load_structured_text(
        self,
        file_path: Path
    ) -> Optional[List[Dict[str, Any]]]:
        """
        加载结构化文本

        Args:
            file_path: PDF 文件路径

        Returns:
            结构化文本列表，如果不存在则返回 None
        """
        try:
            cache_key = self._get_cache_key(file_path, "structured_text")
            cache_file = self.structured_text_dir / f"{cache_key}.pkl"

            if not cache_file.exists():
                logger.debug(f"Structured text cache not found: {cache_key}")
                return None

            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)

            # 验证文件哈希
            current_hash = self._get_file_hash(file_path)
            if cache_data.get("file_hash") != current_hash:
                logger.warning(
                    f"File hash mismatch, cache invalid: {cache_key}")
                cache_file.unlink()
                return None

            structured_text = cache_data["structured_text"]
            logger.info(
                f"Loaded structured text cache: {cache_key} ({len(structured_text)} pages)")
            return structured_text

        except Exception as e:
            logger.error(f"Failed to load structured text cache: {e}")
            return None

    def clear_cache(self, file_path: Optional[Path] = None) -> bool:
        """
        清除缓存

        Args:
            file_path: PDF 文件路径，如果为 None 则清除所有缓存

        Returns:
            是否清除成功
        """
        try:
            if file_path is None:
                # 清除所有缓存
                for cache_dir in [self.metadata_dir, self.chunks_dir, self.structured_text_dir]:
                    for cache_file in cache_dir.glob("*.json"):
                        cache_file.unlink()
                    for cache_file in cache_dir.glob("*.pkl"):
                        cache_file.unlink()
                logger.info("Cleared all PDF cache")
            else:
                # 清除指定文件的缓存
                file_hash = self._get_file_hash(file_path)
                for cache_dir in [self.metadata_dir, self.chunks_dir, self.structured_text_dir]:
                    for cache_file in cache_dir.glob(f"{file_hash}_*"):
                        cache_file.unlink()
                logger.info(f"Cleared cache for: {file_path}")

            return True

        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            缓存统计信息
        """
        try:
            stats = {
                "cache_dir": str(self.cache_dir),
                "metadata_count": len(list(self.metadata_dir.glob("*.json"))),
                "chunks_count": len(list(self.chunks_dir.glob("*.pkl"))),
                "structured_text_count": len(list(self.structured_text_dir.glob("*.pkl"))),
                "total_size_mb": sum(
                    f.stat().st_size for f in self.cache_dir.rglob("*") if f.is_file()
                ) / 1024 / 1024
            }
            return stats

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}


# 全局缓存实例
_cache_instance: Optional[PDFParseCache] = None


def get_pdf_cache(cache_dir: str = "./data/pdf_cache") -> PDFParseCache:
    """
    获取 PDF 缓存单例

    Args:
        cache_dir: 缓存目录路径

    Returns:
        PDFParseCache 实例
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = PDFParseCache(cache_dir)
    return _cache_instance
