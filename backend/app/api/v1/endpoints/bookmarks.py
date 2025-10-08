"""
Bookmark API endpoints.

Handles bookmark CRUD operations, AI generation, and search functionality.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.dependencies import get_db
from ....core.logging import get_logger
from ....core.exceptions import BookmarkNotFoundError, UnauthorizedError
from ....schemas.bookmark import (
    BookmarkCreate,
    BookmarkUpdate,
    BookmarkResponse,
    BookmarkListResponse,
    BookmarkSearchRequest,
    BookmarkGenerateRequest,
)
from ....schemas.user import UserResponse
from ....services.bookmark_service import BookmarkService
from ....repositories.bookmark_repository import BookmarkRepository
from ....infrastructure.ai.gemini_client import GeminiClient
from ...dependencies.auth import get_current_active_user

logger = get_logger(__name__)
router = APIRouter()


# ==================== Dependency Injection ====================

async def get_bookmark_service(
    db: AsyncSession = Depends(get_db),
) -> BookmarkService:
    """Get bookmark service instance."""
    bookmark_repo = BookmarkRepository(db)
    ai_client = GeminiClient()
    return BookmarkService(bookmark_repo=bookmark_repo, ai_client=ai_client)


# ==================== Endpoints ====================

@router.post(
    "/",
    response_model=BookmarkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a bookmark",
    description="Create a new bookmark with AI-generated summary"
)
async def create_bookmark(
    bookmark_data: BookmarkCreate,
    current_user: UserResponse = Depends(get_current_active_user),
    service: BookmarkService = Depends(get_bookmark_service),
):
    """
    Create a new bookmark.

    - **document_id**: Document to bookmark
    - **selected_text**: Text content to bookmark
    - **page_number**: Page number
    - **position**: Bounding box position
    - **conversation_history**: Optional conversation context for AI summary
    - **chunk_id**: Optional associated chunk
    - **title**: Optional custom title
    - **user_notes**: Optional user notes
    - **tags**: Optional tags
    - **color**: Highlight color (default: #FCD34D)
    """
    try:
        logger.info(
            f"Creating bookmark for user {current_user.id} on document {bookmark_data.document_id}"
        )

        bookmark = await service.create_bookmark(
            user_id=current_user.id,
            document_id=bookmark_data.document_id,
            selected_text=bookmark_data.selected_text,
            page_number=bookmark_data.page_number,
            position_x=bookmark_data.position.x,
            position_y=bookmark_data.position.y,
            position_width=bookmark_data.position.width,
            position_height=bookmark_data.position.height,
            conversation_history=bookmark_data.conversation_history,
            chunk_id=bookmark_data.chunk_id,
            title=bookmark_data.title,
            user_notes=bookmark_data.user_notes,
            tags=bookmark_data.tags or [],
            color=bookmark_data.color,
        )

        logger.info(f"Bookmark created: {bookmark.id}")
        return bookmark

    except Exception as e:
        logger.error(f"Failed to create bookmark: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create bookmark: {str(e)}"
        )


@router.post(
    "/generate",
    response_model=BookmarkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate bookmark with AI",
    description="Generate a bookmark with AI-powered summary from conversation"
)
async def generate_bookmark(
    request: BookmarkGenerateRequest,
    current_user: UserResponse = Depends(get_current_active_user),
    service: BookmarkService = Depends(get_bookmark_service),
):
    """
    Generate a bookmark with AI summary.

    This endpoint is optimized for the conversation flow:
    1. User selects text in PDF
    2. Has conversation with AI about the text
    3. Generates bookmark with conversation-aware summary

    The AI will analyze both the selected text and conversation history
    to generate a concise 50-100 word summary.
    """
    try:
        logger.info(
            f"Generating AI bookmark for user {current_user.id} on document {request.document_id}"
        )

        bookmark = await service.create_bookmark(
            user_id=current_user.id,
            document_id=request.document_id,
            selected_text=request.selected_text,
            page_number=request.page_number,
            position_x=request.position.x,
            position_y=request.position.y,
            position_width=request.position.width,
            position_height=request.position.height,
            conversation_history=request.conversation_history or [],
            chunk_id=request.chunk_id,
            color=request.color,
        )

        logger.info(f"AI bookmark generated: {bookmark.id}")
        return bookmark

    except Exception as e:
        logger.error(f"Failed to generate bookmark: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate bookmark: {str(e)}"
        )


@router.get(
    "/",
    response_model=BookmarkListResponse,
    summary="Get bookmarks",
    description="Get bookmarks with optional filters"
)
async def get_bookmarks(
    document_id: Optional[str] = Query(None, description="Filter by document"),
    page_number: Optional[int] = Query(
        None, ge=0, description="Filter by page"),
    limit: int = Query(100, ge=1, le=500, description="Max results"),
    current_user: UserResponse = Depends(get_current_active_user),
    service: BookmarkService = Depends(get_bookmark_service),
):
    """
    Get bookmarks for current user.

    Supports filtering by:
    - **document_id**: Get bookmarks for specific document
    - **page_number**: Get bookmarks on specific page (requires document_id)
    - **limit**: Maximum number of results
    """
    try:
        logger.info(
            f"Getting bookmarks for user {current_user.id} "
            f"(document={document_id}, page={page_number})"
        )

        bookmarks = await service.get_user_bookmarks(
            user_id=current_user.id,
            document_id=document_id,
            page_number=page_number,
            limit=limit,
        )

        return BookmarkListResponse(
            bookmarks=bookmarks,
            total=len(bookmarks)
        )

    except Exception as e:
        logger.error(f"Failed to get bookmarks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get bookmarks: {str(e)}"
        )


@router.get(
    "/{bookmark_id}",
    response_model=BookmarkResponse,
    summary="Get bookmark by ID",
    description="Get a specific bookmark"
)
async def get_bookmark(
    bookmark_id: str,
    current_user: UserResponse = Depends(get_current_active_user),
    service: BookmarkService = Depends(get_bookmark_service),
):
    """Get a specific bookmark by ID."""
    try:
        bookmark = await service.bookmark_repo.get_by_id(bookmark_id)

        if not bookmark:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bookmark not found: {bookmark_id}"
            )

        # Authorization check
        if bookmark.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this bookmark"
            )

        return bookmark

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get bookmark: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get bookmark: {str(e)}"
        )


@router.put(
    "/{bookmark_id}",
    response_model=BookmarkResponse,
    summary="Update bookmark",
    description="Update bookmark title, notes, tags, or color"
)
async def update_bookmark(
    bookmark_id: str,
    update_data: BookmarkUpdate,
    current_user: UserResponse = Depends(get_current_active_user),
    service: BookmarkService = Depends(get_bookmark_service),
):
    """
    Update a bookmark.

    Only the following fields can be updated:
    - **title**: Custom title
    - **user_notes**: User notes
    - **tags**: Tag list
    - **color**: Highlight color

    AI summary and position cannot be changed after creation.
    """
    try:
        logger.info(
            f"Updating bookmark {bookmark_id} for user {current_user.id}")

        bookmark = await service.update_bookmark(
            bookmark_id=bookmark_id,
            user_id=current_user.id,
            title=update_data.title,
            user_notes=update_data.user_notes,
            tags=update_data.tags,
            color=update_data.color,
        )

        logger.info(f"Bookmark updated: {bookmark_id}")
        return bookmark

    except BookmarkNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except UnauthorizedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to update bookmark: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update bookmark: {str(e)}"
        )


@router.delete(
    "/{bookmark_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete bookmark",
    description="Delete a bookmark"
)
async def delete_bookmark(
    bookmark_id: str,
    current_user: UserResponse = Depends(get_current_active_user),
    service: BookmarkService = Depends(get_bookmark_service),
):
    """Delete a bookmark."""
    try:
        logger.info(
            f"Deleting bookmark {bookmark_id} for user {current_user.id}")

        await service.delete_bookmark(
            bookmark_id=bookmark_id,
            user_id=current_user.id,
        )

        logger.info(f"Bookmark deleted: {bookmark_id}")
        return None

    except BookmarkNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except UnauthorizedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to delete bookmark: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete bookmark: {str(e)}"
        )


@router.post(
    "/search",
    response_model=BookmarkListResponse,
    summary="Search bookmarks",
    description="Search bookmarks by text content"
)
async def search_bookmarks(
    search_request: BookmarkSearchRequest,
    current_user: UserResponse = Depends(get_current_active_user),
    service: BookmarkService = Depends(get_bookmark_service),
):
    """
    Search bookmarks by text content.

    Searches in:
    - Selected text
    - AI summary
    - Title
    - User notes

    Optionally filter by document_id.
    """
    try:
        logger.info(
            f"Searching bookmarks for user {current_user.id} "
            f"with query: {search_request.query}"
        )

        bookmarks = await service.search_bookmarks(
            user_id=current_user.id,
            search_text=search_request.query,
            document_id=search_request.document_id,
        )

        return BookmarkListResponse(
            bookmarks=bookmarks,
            total=len(bookmarks)
        )

    except Exception as e:
        logger.error(f"Failed to search bookmarks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search bookmarks: {str(e)}"
        )
