"""
AI Embeddings 服务
使用 sentence-transformers 生成文本向量嵌入
"""
from typing import List, Dict, Any, Optional
import numpy as np

from loguru import logger
from sentence_transformers import SentenceTransformer

from ...core.exceptions import AIServiceError


class EmbeddingsService:
    """文本向量嵌入服务"""

    def __init__(
        self,
        model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
        device: str = "cpu"
    ):
        """
        初始化 Embeddings 服务

        Args:
            model_name: 模型名称（支持中英文的多语言模型）
            device: 设备 ('cpu' 或 'cuda')
        """
        self.model_name = model_name
        self.device = device
        self.model: Optional[SentenceTransformer] = None
        self.embedding_dim: Optional[int] = None

        logger.info(
            f"Initializing Embeddings service with model: {model_name}")

    def _load_model(self):
        """延迟加载模型"""
        if self.model is None:
            try:
                logger.info(f"Loading embedding model: {self.model_name}")
                self.model = SentenceTransformer(
                    self.model_name, device=self.device)
                self.embedding_dim = self.model.get_sentence_embedding_dimension()
                logger.info(
                    f"Model loaded successfully, embedding dimension: {self.embedding_dim}")
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                raise AIServiceError(
                    f"Failed to load embedding model: {str(e)}")

    def encode_text(
        self,
        text: str,
        normalize: bool = True,
        show_progress: bool = False
    ) -> np.ndarray:
        """
        编码单个文本

        Args:
            text: 要编码的文本
            normalize: 是否归一化向量
            show_progress: 是否显示进度

        Returns:
            向量数组
        """
        try:
            self._load_model()

            if not text or not text.strip():
                logger.warning("Empty text provided for encoding")
                return np.zeros(self.embedding_dim)

            embedding = self.model.encode(
                text,
                normalize_embeddings=normalize,
                show_progress_bar=show_progress
            )

            logger.debug(
                f"Encoded text ({len(text)} chars) -> vector ({self.embedding_dim}d)")
            return embedding

        except Exception as e:
            logger.error(f"Error encoding text: {e}")
            raise AIServiceError(f"Failed to encode text: {str(e)}")

    def encode_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
        normalize: bool = True,
        show_progress: bool = True
    ) -> np.ndarray:
        """
        批量编码文本

        Args:
            texts: 文本列表
            batch_size: 批处理大小
            normalize: 是否归一化向量
            show_progress: 是否显示进度

        Returns:
            向量矩阵 (n_texts, embedding_dim)
        """
        try:
            self._load_model()

            if not texts:
                logger.warning("Empty text list provided for encoding")
                return np.array([])

            # 过滤空文本
            filtered_texts = [
                text if text and text.strip() else " " for text in texts]

            logger.info(f"Encoding batch of {len(texts)} texts...")
            embeddings = self.model.encode(
                filtered_texts,
                batch_size=batch_size,
                normalize_embeddings=normalize,
                show_progress_bar=show_progress
            )

            logger.info(f"Batch encoding complete: {embeddings.shape}")
            return embeddings

        except Exception as e:
            logger.error(f"Error in batch encoding: {e}")
            raise AIServiceError(f"Failed to encode batch: {str(e)}")

    def encode_chunks(
        self,
        chunks: List[Dict[str, Any]],
        text_field: str = "text",
        batch_size: int = 32
    ) -> List[Dict[str, Any]]:
        """
        为文档块生成嵌入向量

        Args:
            chunks: 文档块列表
            text_field: 文本字段名
            batch_size: 批处理大小

        Returns:
            添加了 embedding 字段的块列表
        """
        try:
            if not chunks:
                return []

            # 提取文本
            texts = [chunk.get(text_field, "") for chunk in chunks]

            # 批量编码
            embeddings = self.encode_batch(
                texts,
                batch_size=batch_size,
                show_progress=True
            )

            # 添加嵌入向量到每个块
            for chunk, embedding in zip(chunks, embeddings):
                chunk['embedding'] = embedding.tolist()  # 转换为列表以便序列化
                chunk['embedding_model'] = self.model_name
                chunk['embedding_dim'] = self.embedding_dim

            logger.info(f"Added embeddings to {len(chunks)} chunks")
            return chunks

        except Exception as e:
            logger.error(f"Error encoding chunks: {e}")
            raise AIServiceError(f"Failed to encode chunks: {str(e)}")

    def compute_similarity(
        self,
        query_embedding: np.ndarray,
        doc_embeddings: np.ndarray
    ) -> np.ndarray:
        """
        计算查询向量与文档向量的相似度

        Args:
            query_embedding: 查询向量 (embedding_dim,)
            doc_embeddings: 文档向量矩阵 (n_docs, embedding_dim)

        Returns:
            相似度分数数组 (n_docs,)
        """
        try:
            # 使用余弦相似度（归一化后的点积）
            if len(query_embedding.shape) == 1:
                query_embedding = query_embedding.reshape(1, -1)

            similarity_scores = np.dot(
                doc_embeddings, query_embedding.T).flatten()

            return similarity_scores

        except Exception as e:
            logger.error(f"Error computing similarity: {e}")
            raise AIServiceError(f"Failed to compute similarity: {str(e)}")

    def find_most_similar(
        self,
        query_text: str,
        doc_texts: List[str],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        查找与查询最相似的文档

        Args:
            query_text: 查询文本
            doc_texts: 文档文本列表
            top_k: 返回前 K 个结果

        Returns:
            相似文档列表，包含索引和分数
        """
        try:
            # 编码查询和文档
            query_emb = self.encode_text(query_text, show_progress=False)
            doc_embs = self.encode_batch(doc_texts, show_progress=False)

            # 计算相似度
            similarities = self.compute_similarity(query_emb, doc_embs)

            # 获取 top-k 索引
            top_k = min(top_k, len(doc_texts))
            top_indices = np.argsort(similarities)[-top_k:][::-1]

            # 构建结果
            results = []
            for idx in top_indices:
                results.append({
                    'index': int(idx),
                    'text': doc_texts[idx],
                    'score': float(similarities[idx]),
                })

            logger.info(f"Found top {len(results)} similar documents")
            return results

        except Exception as e:
            logger.error(f"Error finding similar documents: {e}")
            raise AIServiceError(f"Failed to find similar documents: {str(e)}")

    def get_embedding_dimension(self) -> int:
        """
        获取嵌入向量维度

        Returns:
            向量维度
        """
        self._load_model()
        return self.embedding_dim

    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息

        Returns:
            模型信息字典
        """
        self._load_model()

        return {
            'model_name': self.model_name,
            'embedding_dimension': self.embedding_dim,
            'device': self.device,
            'max_seq_length': self.model.max_seq_length if hasattr(self.model, 'max_seq_length') else None,
        }
