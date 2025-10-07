"""
Local file storage implementation for IntelliPDF.

This module provides local filesystem storage for uploaded PDF files
with organized directory structure and file management.
"""

import hashlib
import shutil
from datetime import datetime
from pathlib import Path
from typing import BinaryIO, Optional
from uuid import UUID

from ...core.config import Settings, get_settings
from ...core.logging import get_logger
from ...core.exceptions import (
    FileNotFoundError,
    FileSizeExceededError,
    UnsupportedFileTypeError,
    FileProcessingError
)

logger = get_logger(__name__)


class LocalFileStorage:
    """
    Local filesystem storage for PDF files.

    Organizes files in year/month directory structure for better management.
    """

    def __init__(self, settings: Optional[Settings] = None) -> None:
        """
        Initialize local file storage.

        Args:
            settings: Optional settings override
        """
        self.settings = settings or get_settings()
        self.base_path = Path(self.settings.upload_dir)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Local file storage initialized at {self.base_path}")

    def _get_storage_path(self, document_id: UUID, filename: str) -> Path:
        """
        Get organized storage path for a file.

        Creates structure: uploads/YYYY/MM/document_id_filename

        Args:
            document_id: Document unique identifier
            filename: Original filename

        Returns:
            Path: Full storage path
        """
        now = datetime.utcnow()
        year_month_path = self.base_path / str(now.year) / f"{now.month:02d}"
        year_month_path.mkdir(parents=True, exist_ok=True)

        # Sanitize filename
        safe_filename = self._sanitize_filename(filename)
        file_path = year_month_path / f"{document_id}_{safe_filename}"

        return file_path

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent directory traversal and invalid characters.

        Args:
            filename: Original filename

        Returns:
            str: Sanitized filename
        """
        # Remove path components
        filename = Path(filename).name

        # Replace unsafe characters
        unsafe_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        for char in unsafe_chars:
            filename = filename.replace(char, '_')

        return filename

    def _calculate_hash(self, file_obj: BinaryIO) -> str:
        """
        Calculate SHA-256 hash of file content.

        Args:
            file_obj: File object

        Returns:
            str: Hexadecimal hash string
        """
        sha256 = hashlib.sha256()

        # Read in chunks to handle large files
        for chunk in iter(lambda: file_obj.read(8192), b''):
            sha256.update(chunk)

        file_obj.seek(0)  # Reset file pointer
        return sha256.hexdigest()

    def validate_file(self, filename: str, file_size: int) -> None:
        """
        Validate file before storage.

        Args:
            filename: File name
            file_size: File size in bytes

        Raises:
            UnsupportedFileTypeError: If file type is not allowed
            FileSizeExceededError: If file exceeds size limit
        """
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.settings.allowed_extensions:
            raise UnsupportedFileTypeError(
                f"File type {file_ext} is not supported",
                details={
                    "filename": filename,
                    "allowed_extensions": self.settings.allowed_extensions
                }
            )

        # Check file size
        if file_size > self.settings.max_file_size:
            raise FileSizeExceededError(
                f"File size {file_size} bytes exceeds limit of {self.settings.max_file_size} bytes",
                details={
                    "file_size": file_size,
                    "max_size": self.settings.max_file_size
                }
            )

    async def save_file(
        self,
        file_obj: BinaryIO,
        filename: str,
        document_id: UUID
    ) -> tuple[str, str, int]:
        """
        Save uploaded file to storage.

        Args:
            file_obj: File object to save
            filename: Original filename
            document_id: Document unique identifier

        Returns:
            tuple: (file_path, content_hash, file_size)

        Raises:
            FileProcessingError: If file save fails
        """
        try:
            # Get file size
            file_obj.seek(0, 2)  # Seek to end
            file_size = file_obj.tell()
            file_obj.seek(0)  # Reset

            # Validate file
            self.validate_file(filename, file_size)

            # Calculate hash
            content_hash = self._calculate_hash(file_obj)

            # Get storage path
            file_path = self._get_storage_path(document_id, filename)

            # Save file
            with open(file_path, 'wb') as f:
                shutil.copyfileobj(file_obj, f)

            logger.info(
                f"File saved: {file_path} (size: {file_size}, hash: {content_hash})")

            return str(file_path), content_hash, file_size

        except (UnsupportedFileTypeError, FileSizeExceededError):
            raise
        except Exception as e:
            logger.error(f"Failed to save file: {str(e)}")
            raise FileProcessingError(f"File save failed: {str(e)}")

    async def get_file(self, file_path: str) -> BinaryIO:
        """
        Retrieve file from storage.

        Args:
            file_path: File path

        Returns:
            BinaryIO: File object

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"File not found: {file_path}",
                details={"file_path": file_path}
            )

        return open(path, 'rb')

    async def delete_file(self, file_path: str) -> None:
        """
        Delete file from storage.

        Args:
            file_path: File path

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"File not found: {file_path}",
                details={"file_path": file_path}
            )

        path.unlink()
        logger.info(f"File deleted: {file_path}")

        # Clean up empty directories
        try:
            path.parent.rmdir()  # Remove month directory if empty
            path.parent.parent.rmdir()  # Remove year directory if empty
        except OSError:
            pass  # Directory not empty, ignore

    async def file_exists(self, file_path: str) -> bool:
        """
        Check if file exists in storage.

        Args:
            file_path: File path

        Returns:
            bool: True if file exists
        """
        return Path(file_path).exists()

    def get_file_size(self, file_path: str) -> int:
        """
        Get file size.

        Args:
            file_path: File path

        Returns:
            int: File size in bytes

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"File not found: {file_path}",
                details={"file_path": file_path}
            )

        return path.stat().st_size
