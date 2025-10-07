"""
Quick test script for Gemini API.

Run this script to verify Gemini API connectivity.
"""

from app.infrastructure.ai.gemini_client import GeminiClient
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


async def test_gemini():
    """Test Gemini API."""
    print("🚀 Testing Gemini API Connection...")
    print("=" * 60)

    client = GeminiClient()

    try:
        # Test 1: Simple generation
        print("\n📝 Test 1: Simple content generation")
        print("-" * 60)
        prompt = "你好！请用一句话介绍你自己。"
        print(f"Prompt: {prompt}")

        response = await client.generate_content(prompt)
        print(f"\n✅ Response:\n{response}")

        # Test 2: With system instruction
        print("\n\n📝 Test 2: Content generation with system instruction")
        print("-" * 60)
        prompt = "什么是人工智能？"
        system = "你是一个专业的AI助手，请用简洁的语言回答问题。"
        print(f"System: {system}")
        print(f"Prompt: {prompt}")

        response = await client.generate_content(
            prompt=prompt,
            system_instruction=system,
            temperature=0.5
        )
        print(f"\n✅ Response:\n{response}")

        # Test 3: Chat conversation
        print("\n\n📝 Test 3: Chat conversation")
        print("-" * 60)
        messages = [
            {"role": "user", "content": "你好，我想了解Python编程。"},
            {"role": "assistant", "content": "你好！我很乐意帮助你学习Python。Python是一门非常适合初学者的编程语言。"},
            {"role": "user", "content": "请给我一个简单的Python代码例子。"}
        ]

        for msg in messages:
            print(f"{msg['role']}: {msg['content']}")

        response = await client.chat(messages)
        print(f"\n✅ Assistant: {response}")

        print("\n\n" + "=" * 60)
        print("✅ All tests passed! Gemini API is working correctly.")

    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_gemini())
