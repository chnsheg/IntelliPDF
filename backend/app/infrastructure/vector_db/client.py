"""
ChromaDB client management for IntelliPDF.

This module provides ChromaDB client initialization and collection management
for vector similarity search.
"""

from typing import Optional

import chromadb
from chromadb import Collection, ClientAPI
from chromadb.config import Settings as ChromaSettings

from ...core.config import Settings, get_settings
from ...core.logging import get_logger
from ...core.exceptions import ChromaDBConnectionError, CollectionNotFoundError

logger = get_logger(__name__)

# Global client instance
_chroma_client: Optional[ClientAPI] = None


def get_chroma_client(settings: Optional[Settings] = None) -> ClientAPI:
    """
    Get or create ChromaDB client.

    Args:
        settings: Optional settings override

    Returns:
        ClientAPI: ChromaDB client

    Raises:
        ChromaDBConnectionError: If connection fails
    """
    global _chroma_client

    if _chroma_client is None:
        if settings is None:
            settings = get_settings()

        try:
            chroma_settings = ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=not settings.is_production,
            )

            _chroma_client = chromadb.PersistentClient(
                path=settings.chroma_db_path,
                settings=chroma_settings
            )

            logger.info(
                f"ChromaDB client initialized at {settings.chroma_db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {str(e)}")
            raise ChromaDBConnectionError(
                f"ChromaDB connection failed: {str(e)}")

    return _chroma_client


def get_collection(
    collection_name: Optional[str] = None,
    create_if_not_exists: bool = True,
    settings: Optional[Settings] = None
) -> Collection:
    """
    Get or create ChromaDB collection.

    Args:
        collection_name: Collection name (uses default from settings if None)
        create_if_not_exists: Create collection if it doesn't exist
        settings: Optional settings override

    Returns:
        Collection: ChromaDB collection

    Raises:
        CollectionNotFoundError: If collection doesn't exist and create_if_not_exists is False
    """
    if settings is None:
        settings = get_settings()

    if collection_name is None:
        collection_name = settings.chroma_collection_name

    client = get_chroma_client(settings)

    try:
        if create_if_not_exists:
            collection = client.get_or_create_collection(
                name=collection_name,
                metadata={
                    "description": "IntelliPDF document chunks with embeddings"}
            )
            logger.info(f"Collection '{collection_name}' ready")
        else:
            collection = client.get_collection(name=collection_name)
            logger.info(f"Retrieved collection '{collection_name}'")

        return collection
    except Exception as e:
        logger.error(f"Failed to get collection '{collection_name}': {str(e)}")
        if not create_if_not_exists:
            raise CollectionNotFoundError(
                f"Collection '{collection_name}' not found",
                details={"collection_name": collection_name}
            )
        raise


def delete_collection(collection_name: Optional[str] = None, settings: Optional[Settings] = None) -> None:
    """
    Delete a ChromaDB collection.

    Args:
        collection_name: Collection name (uses default from settings if None)
        settings: Optional settings override
    """
    if settings is None:
        settings = get_settings()

    if collection_name is None:
        collection_name = settings.chroma_collection_name

    client = get_chroma_client(settings)

    try:
        client.delete_collection(name=collection_name)
        logger.info(f"Deleted collection '{collection_name}'")
    except Exception as e:
        logger.error(
            f"Failed to delete collection '{collection_name}': {str(e)}")
        raise


def reset_client() -> None:
    """Reset ChromaDB client (for testing purposes)."""
    global _chroma_client
    _chroma_client = None
    logger.info("ChromaDB client reset")
