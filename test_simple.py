import httpx
import asyncio


async def main():
    # 禁用所有代理和环境变量
    async with httpx.AsyncClient(trust_env=False) as client:
        try:
            response = await client.get("http://127.0.0.1:8000/api/v1/health")
            print(f"Status: {response.status_code}")
            print(f"Headers: {response.headers}")
            print(f"Content: {response.text}")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
