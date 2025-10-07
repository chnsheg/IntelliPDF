"""简单测试 Gemini API 连接"""
from app.infrastructure.ai.gemini_client import get_gemini_client
import sys
import os
import asyncio

# 设置工作目录为 backend
os.chdir("backend")
sys.path.insert(0, ".")


async def test_gemini():
    print("🔧 测试 Gemini API 连接...")
    print(f"  当前工作目录: {os.getcwd()}")
    print(f"  .env 文件存在: {os.path.exists('.env')}")

    client = await get_gemini_client()
    print(f"✓ Gemini 客户端已初始化")
    print(f"  Base URL: {client.base_url}")
    print(f"  Model: {client.model}")

    print("\n📤 发送测试请求...")
    try:
        response = await client.generate_content(
            prompt="你好，请回复'收到'",
            temperature=0.5
        )
        print(f"✓ 收到响应: {response}")
        return True
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


if __name__ == "__main__":
    result = asyncio.run(test_gemini())
    sys.exit(0 if result else 1)
