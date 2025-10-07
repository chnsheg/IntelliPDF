"""
向量检索服务
基于 ChromaDB 实现文档向量存储和检索
"""
from typing import List, Dict, Any, Optional
import uuid

from loguru import logger

from ...infrastructure.vector_db.client import get_chroma_client
from ...core.config import get_settings
from ...core.exceptions import AIServiceError
from .embeddings import EmbeddingsService


class RetrievalService:
    """文档检索服务"""

    def __init__(
        self,
        collection_name: Optional[str] = None,
        embeddings_service: Optional[EmbeddingsService] = None
    ):
        """
        初始化检索服务

        Args:
            collection_name: 集合名称
            embeddings_service: 嵌入服务实例
        """
        settings = get_settings()
        self.collection_name = collection_name or settings.chroma_collection_name
        self.embeddings_service = embeddings_service or EmbeddingsService()

        # ChromaDB 客户端和集合
        self.client = None
        self.collection = None

        logger.info(
            f"Initialized Retrieval service for collection: {self.collection_name}")

    def _ensure_collection(self):
        """确保集合已创建"""
        if self.collection is None:
            self.client = get_chroma_client()
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "IntelliPDF document collection"}
            )
            logger.info(f"Collection '{self.collection_name}' ready")

    def add_documents(
        self,
        chunks: List[Dict[str, Any]],
        document_id: Optional[str] = None,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        添加文档块到向量数据库

        Args:
            chunks: 文档块列表
            document_id: 文档ID
            batch_size: 批处理大小

        Returns:
            添加结果统计
        """
        try:
            self._ensure_collection()

            if not chunks:
                logger.warning("No chunks to add")
                return {'added': 0}

            # 生成嵌入向量（如果还没有）
            if 'embedding' not in chunks[0]:
                logger.info("Generating embeddings for chunks...")
                chunks = self.embeddings_service.encode_chunks(chunks)

            # 准备数据
            ids = []
            embeddings = []
            documents = []
            metadatas = []

            for i, chunk in enumerate(chunks):
                # 生成唯一 ID
                chunk_id = f"{document_id}_{chunk.get('chunk_index', i)}" if document_id else str(
                    uuid.uuid4())
                ids.append(chunk_id)

                # 嵌入向量
                embeddings.append(chunk['embedding'])

                # 文档文本
                documents.append(chunk.get('text', ''))

                # 元数据
                metadata = {
                    'document_id': document_id or 'unknown',
                    'chunk_index': chunk.get('chunk_index', i),
                    'char_count': chunk.get('char_count', 0),
                    'word_count': chunk.get('word_count', 0),
                }

                # 添加页面信息（如果有）
                if 'page_numbers' in chunk:
                    metadata['page_numbers'] = str(chunk['page_numbers'])
                if 'start_page' in chunk:
                    metadata['start_page'] = chunk['start_page']
                if 'end_page' in chunk:
                    metadata['end_page'] = chunk['end_page']

                metadatas.append(metadata)

            # 批量添加到 ChromaDB
            logger.info(f"Adding {len(ids)} chunks to ChromaDB...")

            for i in range(0, len(ids), batch_size):
                end_idx = min(i + batch_size, len(ids))
                self.collection.add(
                    ids=ids[i:end_idx],
                    embeddings=embeddings[i:end_idx],
                    documents=documents[i:end_idx],
                    metadatas=metadatas[i:end_idx]
                )

            logger.info(f"Successfully added {len(ids)} chunks")

            return {
                'added': len(ids),
                'document_id': document_id,
                'collection': self.collection_name
            }

        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise AIServiceError(f"Failed to add documents: {str(e)}")

    def search(
        self,
        query_text: str,
        n_results: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索相关文档

        Args:
            query_text: 查询文本
            n_results: 返回结果数量
            filter_dict: 过滤条件

        Returns:
            搜索结果列表
        """
        try:
            self._ensure_collection()

            # 生成查询向量
            logger.info(f"Searching for: {query_text[:50]}...")
            query_embedding = self.embeddings_service.encode_text(
                query_text, show_progress=False)

            # 执行查询
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=n_results,
                where=filter_dict
            )

            # 格式化结果
            formatted_results = []
            if results and results['ids']:
                for i in range(len(results['ids'][0])):
                    result = {
                        'id': results['ids'][0][i],
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if 'distances' in results else None,
                    }
                    formatted_results.append(result)

            logger.info(f"Found {len(formatted_results)} results")
            return formatted_results

        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            raise AIServiceError(f"Failed to search documents: {str(e)}")

    def search_by_document(
        self,
        query_text: str,
        document_id: str,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        在特定文档中搜索

        Args:
            query_text: 查询文本
            document_id: 文档ID
            n_results: 返回结果数量

        Returns:
            搜索结果列表
        """
        filter_dict = {"document_id": document_id}
        return self.search(query_text, n_results, filter_dict)

    def get_document_chunks(
        self,
        document_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取文档的所有块

        Args:
            document_id: 文档ID
            limit: 限制返回数量

        Returns:
            文档块列表
        """
        try:
            self._ensure_collection()

            # 使用过滤条件查询
            results = self.collection.get(
                where={"document_id": document_id},
                limit=limit
            )

            # 格式化结果
            chunks = []
            if results and results['ids']:
                for i in range(len(results['ids'])):
                    chunk = {
                        'id': results['ids'][i],
                        'text': results['documents'][i] if results['documents'] else None,
                        'metadata': results['metadatas'][i] if results['metadatas'] else {},
                    }
                    chunks.append(chunk)

            logger.info(
                f"Retrieved {len(chunks)} chunks for document {document_id}")
            return chunks

        except Exception as e:
            logger.error(f"Error getting document chunks: {e}")
            raise AIServiceError(f"Failed to get document chunks: {str(e)}")

    def delete_document(self, document_id: str) -> Dict[str, Any]:
        """
        删除文档的所有块

        Args:
            document_id: 文档ID

        Returns:
            删除结果
        """
        try:
            self._ensure_collection()

            # 获取要删除的 IDs
            chunks = self.get_document_chunks(document_id)
            ids_to_delete = [chunk['id'] for chunk in chunks]

            if ids_to_delete:
                self.collection.delete(ids=ids_to_delete)
                logger.info(
                    f"Deleted {len(ids_to_delete)} chunks for document {document_id}")

            return {
                'deleted': len(ids_to_delete),
                'document_id': document_id
            }

        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            raise AIServiceError(f"Failed to delete document: {str(e)}")

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        获取集合统计信息

        Returns:
            统计信息字典
        """
        try:
            self._ensure_collection()

            count = self.collection.count()

            return {
                'collection_name': self.collection_name,
                'total_chunks': count,
                'embedding_model': self.embeddings_service.model_name,
                'embedding_dimension': self.embeddings_service.get_embedding_dimension()
            }

        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            raise AIServiceError(f"Failed to get collection stats: {str(e)}")

    def clear_collection(self) -> Dict[str, Any]:
        """
        清空集合

        Returns:
            操作结果
        """
        try:
            if self.client and self.collection:
                self.client.delete_collection(name=self.collection_name)
                self.collection = None
                logger.info(f"Cleared collection: {self.collection_name}")

            return {
                'status': 'cleared',
                'collection_name': self.collection_name
            }

        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            raise AIServiceError(f"Failed to clear collection: {str(e)}")
