"""
测试 AI 聊天功能 - 验证 422 错误
"""
import requests
import json

BASE_URL = "http://localhost:8000"

# 假设你有一个文档 ID (从上传或列表中获取)
# 替换为实际的文档 ID
DOCUMENT_ID = "your-document-id-here"


def test_chat():
    print("=" * 60)
    print("测试 AI 聊天功能")
    print("=" * 60)

    # 测试 1: 最简单的请求
    print("\n[测试 1] 发送最简单的聊天请求...")
    payload = {
        "question": "这个文档讲了什么？"
    }

    print(f"请求 URL: {BASE_URL}/api/v1/documents/{DOCUMENT_ID}/chat")
    print(f"请求数据: {json.dumps(payload, ensure_ascii=False, indent=2)}")

    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/documents/{DOCUMENT_ID}/chat",
            json=payload,
            timeout=30
        )

        print(f"\n状态码: {response.status_code}")

        if response.status_code == 422:
            print("\n❌ 422 验证错误!")
            print("错误详情:")
            print(json.dumps(response.json(), ensure_ascii=False, indent=2))
        elif response.status_code == 200:
            print("\n✅ 请求成功!")
            result = response.json()
            print(f"回答: {result.get('answer', 'N/A')[:200]}...")
        else:
            print(f"\n⚠️  意外状态码: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"\n❌ 请求失败: {e}")

    # 测试 2: 完整参数
    print("\n\n[测试 2] 发送完整参数的请求...")
    payload2 = {
        "question": "Linux 有哪些常用命令？",
        "conversation_history": [],
        "top_k": 5,
        "temperature": 0.7
    }

    print(f"请求数据: {json.dumps(payload2, ensure_ascii=False, indent=2)}")

    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/documents/{DOCUMENT_ID}/chat",
            json=payload2,
            timeout=30
        )

        print(f"\n状态码: {response.status_code}")

        if response.status_code == 422:
            print("\n❌ 422 验证错误!")
            print("错误详情:")
            print(json.dumps(response.json(), ensure_ascii=False, indent=2))
        elif response.status_code == 200:
            print("\n✅ 请求成功!")
            result = response.json()
            print(f"回答: {result.get('answer', 'N/A')[:200]}...")
        else:
            print(f"\n⚠️  意外状态码: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"\n❌ 请求失败: {e}")


if __name__ == "__main__":
    print("提示: 请先将 DOCUMENT_ID 替换为实际的文档 ID")
    print("可以通过访问 http://localhost:8000/api/docs 查看现有文档")
    print()

    # 如果没有设置 document_id，提供获取方法
    if DOCUMENT_ID == "your-document-id-here":
        print("正在获取文档列表...")
        try:
            response = requests.get(f"{BASE_URL}/api/v1/documents")
            if response.status_code == 200:
                docs_data = response.json()
                # 处理可能的响应格式
                if isinstance(docs_data, dict):
                    docs = docs_data.get(
                        'documents', []) or docs_data.get('items', [])
                elif isinstance(docs_data, list):
                    docs = docs_data
                else:
                    docs = []

                if docs and len(docs) > 0:
                    print(f"\n找到 {len(docs)} 个文档:")
                    for i in range(min(5, len(docs))):
                        doc = docs[i]
                        doc_id = doc.get('id', 'N/A')
                        filename = doc.get('filename', 'N/A')
                        print(f"  {i+1}. ID: {doc_id}")
                        print(f"     文件名: {filename}")

                    DOCUMENT_ID = docs[0]['id']
                    print(f"\n使用第一个文档进行测试: {DOCUMENT_ID}")
                else:
                    print("没有找到文档，请先上传一个 PDF")
                    exit(1)
        except Exception as e:
            print(f"获取文档列表失败: {e}")
            exit(1)

    test_chat()
