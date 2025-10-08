"""
Bookmark service for managing bookmarks with AI-generated summaries.

This service handles bookmark CRUD operations and AI summary generation.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID

from ..core.logging import get_logger
from ..core.exceptions import ValidationError, ProcessingError
from ..models.db import BookmarkModel
from ..repositories.bookmark_repository import BookmarkRepository
from ..infrastructure.ai.gemini_client import GeminiClient

logger = get_logger(__name__)


class BookmarkService:
    """Service for bookmark operations and AI summary generation."""

    def __init__(
        self,
        bookmark_repo: BookmarkRepository,
        ai_client: Optional[GeminiClient] = None
    ):
        """
        Initialize bookmark service.

        Args:
            bookmark_repo: Bookmark repository instance
            ai_client: Optional Gemini AI client
        """
        self.bookmark_repo = bookmark_repo
        self.ai_client = ai_client or GeminiClient()

    async def create_bookmark(
        self,
        user_id: str,
        document_id: str,
        selected_text: str,
        page_number: int,
        position_x: float,
        position_y: float,
        position_width: float,
        position_height: float,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        chunk_id: Optional[str] = None,
        title: Optional[str] = None,
        user_notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
        color: str = "#FCD34D"
    ) -> BookmarkModel:
        """
        Create a new bookmark with AI-generated summary.

        Args:
            user_id: User ID
            document_id: Document ID
            selected_text: Selected text content
            page_number: Page number
            position_x: X coordinate
            position_y: Y coordinate
            position_width: Width
            position_height: Height
            conversation_history: Optional chat history
            chunk_id: Optional associated chunk ID
            title: Optional bookmark title
            user_notes: Optional user notes
            tags: Optional tags
            color: Highlight color

        Returns:
            Created bookmark model

        Raises:
            ValidationError: If input is invalid
            ProcessingError: If AI generation fails
        """
        try:
            # Validate inputs
            if not selected_text or len(selected_text.strip()) == 0:
                raise ValidationError("Selected text cannot be empty")

            if page_number < 0:
                raise ValidationError("Page number must be non-negative")

            # Generate AI summary
            logger.info(
                f"Generating AI summary for bookmark on page {page_number}")
            ai_summary = await self._generate_bookmark_summary(
                selected_text=selected_text,
                conversation_history=conversation_history
            )

            # Create bookmark model
            bookmark = BookmarkModel(
                user_id=user_id,
                document_id=document_id,
                chunk_id=chunk_id,
                selected_text=selected_text,
                page_number=page_number,
                position_x=position_x,
                position_y=position_y,
                position_width=position_width,
                position_height=position_height,
                ai_summary=ai_summary,
                title=title or self._generate_title(selected_text),
                user_notes=user_notes,
                conversation_context=self._format_conversation(
                    conversation_history),
                tags=tags or [],
                color=color
            )

            # Save to database
            created_bookmark = await self.bookmark_repo.create(bookmark)
            await self.bookmark_repo.commit()

            logger.info(
                f"Created bookmark {created_bookmark.id} for user {user_id}")
            return created_bookmark

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error creating bookmark: {e}", exc_info=True)
            raise ProcessingError(f"Failed to create bookmark: {str(e)}")

    async def _generate_bookmark_summary(
        self,
        selected_text: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Generate AI summary for bookmark based on selected text and conversation.

        Args:
            selected_text: The selected text
            conversation_history: Optional conversation history

        Returns:
            AI-generated summary

        Raises:
            ProcessingError: If AI generation fails
        """
        try:
            # Build prompt
            prompt = f"""请基于以下选中的文本内容生成一个简洁的书签摘要。

选中文本：
{selected_text}

"""

            # Add conversation context if available
            if conversation_history and len(conversation_history) > 0:
                prompt += "\n相关对话历史：\n"
                for msg in conversation_history[-5:]:  # Last 5 messages
                    role = "用户" if msg.get('role') == 'user' else "助手"
                    content = msg.get('content', '')
                    prompt += f"{role}: {content}\n"

            prompt += """
要求：
1. 总结核心知识点（50-100字）
2. 如果有对话历史，结合对话内容提炼关键信息
3. 使用清晰、专业的语言
4. 突出重点概念和要点

请生成书签摘要："""

            # Call Gemini API
            summary = await self.ai_client.generate_content(
                prompt=prompt,
                system_instruction="你是一个专业的知识总结助手，擅长提炼文档中的核心要点。"
            )

            if not summary or len(summary.strip()) == 0:
                raise ProcessingError("AI generated empty summary")

            logger.info(f"Generated AI summary: {summary[:100]}...")
            return summary.strip()

        except Exception as e:
            logger.error(f"Error generating AI summary: {e}")
            # Fallback to simple truncation
            fallback_summary = selected_text[:200] + \
                "..." if len(selected_text) > 200 else selected_text
            logger.warning(f"Using fallback summary due to AI error")
            return f"[摘要生成失败，显示原文] {fallback_summary}"

    def _generate_title(self, text: str, max_length: int = 50) -> str:
        """
        Generate a short title from text.

        Args:
            text: Source text
            max_length: Maximum title length

        Returns:
            Generated title
        """
        # Take first sentence or first N characters
        first_sentence = text.split('。')[0].split('.')[0].strip()

        if len(first_sentence) <= max_length:
            return first_sentence

        return first_sentence[:max_length] + "..."

    def _format_conversation(
        self,
        conversation: Optional[List[Dict[str, str]]]
    ) -> Optional[Dict[str, Any]]:
        """
        Format conversation history for storage.

        Args:
            conversation: Conversation messages

        Returns:
            Formatted conversation dict
        """
        if not conversation:
            return None

        return {
            'messages': conversation,
            'count': len(conversation)
        }

    async def update_bookmark(
        self,
        bookmark_id: str,
        user_id: str,
        title: Optional[str] = None,
        user_notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
        color: Optional[str] = None
    ) -> BookmarkModel:
        """
        Update bookmark information.

        Args:
            bookmark_id: Bookmark ID
            user_id: User ID (for authorization)
            title: New title
            user_notes: New notes
            tags: New tags
            color: New color

        Returns:
            Updated bookmark

        Raises:
            ValidationError: If bookmark not found or unauthorized
        """
        try:
            bookmark = await self.bookmark_repo.get_by_id(bookmark_id)

            if not bookmark:
                raise ValidationError("Bookmark not found")

            if bookmark.user_id != user_id:
                raise ValidationError("Unauthorized to update this bookmark")

            # Update fields
            update_data = {}
            if title is not None:
                update_data['title'] = title
            if user_notes is not None:
                update_data['user_notes'] = user_notes
            if tags is not None:
                update_data['tags'] = tags
            if color is not None:
                update_data['color'] = color

            if update_data:
                updated_bookmark = await self.bookmark_repo.update(bookmark_id, update_data)
                await self.bookmark_repo.commit()
                logger.info(f"Updated bookmark {bookmark_id}")
                return updated_bookmark

            return bookmark

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error updating bookmark: {e}")
            raise ProcessingError(f"Failed to update bookmark: {str(e)}")

    async def delete_bookmark(self, bookmark_id: str, user_id: str) -> bool:
        """
        Delete a bookmark.

        Args:
            bookmark_id: Bookmark ID
            user_id: User ID (for authorization)

        Returns:
            True if deleted

        Raises:
            ValidationError: If unauthorized or not found
        """
        try:
            bookmark = await self.bookmark_repo.get_by_id(bookmark_id)

            if not bookmark:
                raise ValidationError("Bookmark not found")

            if bookmark.user_id != user_id:
                raise ValidationError("Unauthorized to delete this bookmark")

            deleted = await self.bookmark_repo.delete(bookmark_id)
            await self.bookmark_repo.commit()

            logger.info(f"Deleted bookmark {bookmark_id}")
            return deleted

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error deleting bookmark: {e}")
            raise ProcessingError(f"Failed to delete bookmark: {str(e)}")

    async def get_user_bookmarks(
        self,
        user_id: str,
        document_id: Optional[str] = None,
        page_number: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[BookmarkModel]:
        """
        Get bookmarks for a user.

        Args:
            user_id: User ID
            document_id: Optional document filter
            page_number: Optional page filter
            limit: Optional limit on number of results

        Returns:
            List of bookmarks
        """
        try:
            if document_id and page_number is not None:
                bookmarks = await self.bookmark_repo.get_by_page(document_id, page_number, user_id)
            elif document_id:
                bookmarks = await self.bookmark_repo.get_by_user_and_document(user_id, document_id)
            else:
                bookmarks = await self.bookmark_repo.get_by_user(user_id)

            # Apply limit if specified
            if limit and len(bookmarks) > limit:
                return bookmarks[:limit]
            return bookmarks
        except Exception as e:
            logger.error(f"Error getting user bookmarks: {e}")
            raise ProcessingError(f"Failed to get bookmarks: {str(e)}")

    async def search_bookmarks(
        self,
        user_id: str,
        search_text: str,
        document_id: Optional[str] = None
    ) -> List[BookmarkModel]:
        """
        Search bookmarks by text.

        Args:
            user_id: User ID
            search_text: Search query
            document_id: Optional document filter

        Returns:
            List of matching bookmarks
        """
        try:
            return await self.bookmark_repo.search_by_text(user_id, search_text, document_id)
        except Exception as e:
            logger.error(f"Error searching bookmarks: {e}")
            raise ProcessingError(f"Failed to search bookmarks: {str(e)}")
