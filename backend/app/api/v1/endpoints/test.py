"""
Test endpoints for IntelliPDF API.

This module provides test endpoints for validating system functionality.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict

from ....core.logging import get_logger
from ....infrastructure.ai.gemini_client import get_gemini_client
from ....core.exceptions import AIServiceError

logger = get_logger(__name__)
router = APIRouter()


class TestPromptRequest(BaseModel):
    """Request model for test prompt."""
    prompt: str
    system_instruction: Optional[str] = None
    temperature: Optional[float] = None


class TestChatRequest(BaseModel):
    """Request model for test chat."""
    messages: List[Dict[str, str]]
    temperature: Optional[float] = None


class TestPromptResponse(BaseModel):
    """Response model for test prompt."""
    success: bool
    response: str
    error: Optional[str] = None


@router.post("/gemini", response_model=TestPromptResponse)
async def test_gemini_api(request: TestPromptRequest):
    """
    Test Gemini API connection and generation.

    Args:
        request: Test prompt request

    Returns:
        Generated response from Gemini
    """
    try:
        logger.info(
            f"Testing Gemini API with prompt: {request.prompt[:50]}...")

        client = await get_gemini_client()
        response = await client.generate_content(
            prompt=request.prompt,
            system_instruction=request.system_instruction,
            temperature=request.temperature
        )

        logger.info("Gemini API test successful")
        return TestPromptResponse(
            success=True,
            response=response
        )

    except AIServiceError as e:
        logger.error(f"Gemini API test failed: {e}")
        return TestPromptResponse(
            success=False,
            response="",
            error=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in Gemini test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/gemini/chat", response_model=TestPromptResponse)
async def test_gemini_chat(request: TestChatRequest):
    """
    Test Gemini chat API.

    Args:
        request: Test chat request

    Returns:
        Generated response from Gemini
    """
    try:
        logger.info(
            f"Testing Gemini Chat API with {len(request.messages)} messages...")

        client = await get_gemini_client()
        response = await client.chat(
            messages=request.messages,
            temperature=request.temperature
        )

        logger.info("Gemini Chat API test successful")
        return TestPromptResponse(
            success=True,
            response=response
        )

    except AIServiceError as e:
        logger.error(f"Gemini Chat API test failed: {e}")
        return TestPromptResponse(
            success=False,
            response="",
            error=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in Gemini chat test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ping")
async def ping():
    """Simple ping endpoint."""
    return {"status": "ok", "message": "pong"}
