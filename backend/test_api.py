"""
API 测试脚本
"""
import asyncio
import httpx


async def test_health():
    """测试健康检查端点"""
    async with httpx.AsyncClient(trust_env=False) as client:
        print("\n" + "="*60)
        print("🏥 测试健康检查端点")
        print("="*60)

        response = await client.get("http://127.0.0.1:8000/api/v1/health")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        else:
            print(f"Error: {response.text}")


async def test_gemini_simple():
    """测试 Gemini 简单生成"""
    async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
        print("\n" + "="*60)
        print("🤖 测试 Gemini 简单生成")
        print("="*60)

        data = {
            "prompt": "你好！请用一句话介绍你自己。"
        }

        response = await client.post(
            "http://127.0.0.1:8000/api/v1/test/gemini",
            json=data
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {result.get('response', 'N/A')}")
        else:
            print(f"Error: {response.text}")


async def test_gemini_chat():
    """测试 Gemini 对话"""
    async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
        print("\n" + "="*60)
        print("💬 测试 Gemini 对话功能")
        print("="*60)

        data = {
            "messages": [
                {"role": "user", "content": "你好"},
                {"role": "assistant", "content": "你好！有什么可以帮助你的吗？"},
                {"role": "user", "content": "什么是Python？"}
            ]
        }

        response = await client.post(
            "http://127.0.0.1:8000/api/v1/test/gemini/chat",
            json=data
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            response_text = result.get('response', 'N/A')
            print(f"Response: {response_text[:200]}..." if len(
                response_text) > 200 else f"Response: {response_text}")
        else:
            print(f"Error: {response.text}")


async def main():
    """运行所有测试"""
    try:
        await test_health()
        await test_gemini_simple()
        await test_gemini_chat()

        print("\n" + "="*60)
        print("✅ 所有测试完成！")
        print("="*60)
        print("\n📝 你可以访问以下地址：")
        print("   - API 文档: http://127.0.0.1:8000/api/docs")
        print("   - 健康检查: http://127.0.0.1:8000/api/v1/health")
        print("   - 测试端点: http://127.0.0.1:8000/api/v1/test/ping")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
