"""
Gemini API Client for IntelliPDF.

This module provides a client for interacting with Google's Gemini API
using the correct v1beta API format.
"""

import httpx
from typing import Optional, Dict, Any, List

from ...core.config import get_settings
from ...core.logging import get_logger
from ...core.exceptions import AIServiceError

logger = get_logger(__name__)
settings = get_settings()


class GeminiClient:
    """Client for Google Gemini API operations."""

    def __init__(self):
        """Initialize Gemini client."""
        self.api_key = settings.gemini_api_key
        self.base_url = settings.gemini_base_url.rstrip('/')
        self.model = settings.gemini_model
        self.temperature = settings.gemini_temperature
        self.max_tokens = settings.gemini_max_tokens

        self.client = httpx.AsyncClient(
            timeout=60.0,
            headers={
                "Content-Type": "application/json",
            }
        )

        logger.info(
            f"Initialized Gemini client with base URL: {self.base_url}")
        logger.info(f"Using model: {self.model}")

    async def generate_content(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_instruction: Optional[str] = None,
    ) -> str:
        """
        Generate content using Gemini API.

        Args:
            prompt: The user prompt
            temperature: Temperature for generation (overrides default)
            max_tokens: Max tokens for generation (overrides default)
            system_instruction: System instruction for the model

        Returns:
            Generated text content

        Raises:
            AIServiceError: If API request fails
        """
        try:
            # Construct API URL: /v1beta/models/{model}:generateContent?key={key}
            url = f"{self.base_url}/v1beta/models/{self.model}:generateContent?key={self.api_key}"

            # Prepare request payload
            contents = []

            # Add system instruction if provided
            if system_instruction:
                contents.append({
                    "role": "user",
                    "parts": [{"text": f"[System Instruction] {system_instruction}\n\n"}]
                })

            # Add user prompt
            contents.append({
                "role": "user",
                "parts": [{"text": prompt}]
            })

            payload = {
                "contents": contents,
                "generationConfig": {
                    "temperature": temperature or self.temperature,
                    "maxOutputTokens": max_tokens or self.max_tokens,
                }
            }

            logger.debug(f"Sending request to: {url[:50]}...")
            logger.debug(f"Payload: {payload}")

            response = await self.client.post(url, json=payload)

            response.raise_for_status()
            result = response.json()

            logger.debug(f"Received response: {result}")

            # Extract content from response
            if "candidates" in result and len(result["candidates"]) > 0:
                candidate = result["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    parts = candidate["content"]["parts"]
                    if len(parts) > 0 and "text" in parts[0]:
                        content = parts[0]["text"]
                        logger.info(
                            f"Successfully generated content ({len(content)} chars)")
                        return content

            logger.warning("No content in response")
            return ""

        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            logger.error(
                f"HTTP error from Gemini API: {e.response.status_code} - {error_detail}")
            raise AIServiceError(
                f"Gemini API HTTP error: {e.response.status_code} - {error_detail}")
        except httpx.RequestError as e:
            logger.error(f"Request error to Gemini API: {e}")
            raise AIServiceError(f"Gemini API request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error calling Gemini API: {e}")
            raise AIServiceError(f"Gemini API error: {str(e)}")

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Chat with Gemini using conversation history.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Temperature for generation
            max_tokens: Max tokens for generation

        Returns:
            Generated response text
        """
        try:
            url = f"{self.base_url}/v1beta/models/{self.model}:generateContent?key={self.api_key}"

            # Convert messages to Gemini format
            contents = []
            for msg in messages:
                role = "model" if msg["role"] == "assistant" else "user"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg["content"]}]
                })

            payload = {
                "contents": contents,
                "generationConfig": {
                    "temperature": temperature or self.temperature,
                    "maxOutputTokens": max_tokens or self.max_tokens,
                }
            }

            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()

            if "candidates" in result and len(result["candidates"]) > 0:
                candidate = result["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    parts = candidate["content"]["parts"]
                    if len(parts) > 0 and "text" in parts[0]:
                        return parts[0]["text"]

            return ""

        except Exception as e:
            logger.error(f"Error in chat: {e}")
            raise AIServiceError(f"Chat failed: {str(e)}")

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
        logger.info("Gemini client closed")


# Singleton instance
_gemini_client: Optional[GeminiClient] = None


async def get_gemini_client() -> GeminiClient:
    """Get or create Gemini client instance."""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client


async def close_gemini_client() -> None:
    """Close Gemini client instance."""
    global _gemini_client
    if _gemini_client is not None:
        await _gemini_client.close()
        _gemini_client = None
