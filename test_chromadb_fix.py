"""
测试 AI 聊天功能 - ChromaDB 修复验证
"""
import requests
import time

BASE_URL = "http://localhost:8000/api/v1"


def wait_for_server():
    """等待服务器启动"""
    print("⏳ 等待后端服务启动...")
    for i in range(30):
        try:
            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.status_code == 200:
                print("✅ 后端服务已启动")
                return True
        except:
            pass
        time.sleep(1)
    print("❌ 后端服务启动超时")
    return False


def get_documents():
    """获取文档列表"""
    print("\n📄 获取文档列表...")
    try:
        response = requests.get(f"{BASE_URL}/documents")
        response.raise_for_status()
        docs = response.json().get("items", [])
        print(f"✅ 找到 {len(docs)} 个文档")
        return docs
    except Exception as e:
        print(f"❌ 获取文档失败: {e}")
        return []


def test_chat(document_id):
    """测试 AI 聊天"""
    print(f"\n💬 测试 AI 聊天 (文档: {document_id})...")

    payload = {
        "question": "这个文档讲的是什么？",
        "conversation_history": [],
        "top_k": 3,
        "temperature": 0.7
    }

    try:
        response = requests.post(
            f"{BASE_URL}/documents/{document_id}/chat",
            json=payload,
            timeout=30
        )

        print(f"📊 状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ AI 聊天成功!")
            print(f"📝 回答: {data.get('answer', 'N/A')[:200]}...")
            print(f"🔍 使用的上下文片段数: {len(data.get('context_chunks', []))}")
            return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"错误详情: {response.text}")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("="*60)
    print("🧪 ChromaDB 修复验证测试")
    print("="*60)

    # 等待服务器启动
    if not wait_for_server():
        return

    # 获取文档
    docs = get_documents()
    if not docs:
        print("\n⚠️ 没有找到文档，请先上传 PDF")
        return

    # 测试第一个文档的聊天功能
    doc = docs[0]
    doc_id = doc["id"]
    doc_name = doc.get("original_filename", "未知")

    print(f"\n使用文档: {doc_name} (ID: {doc_id})")

    success = test_chat(doc_id)

    print("\n" + "="*60)
    if success:
        print("✅ ChromaDB 修复成功！AI 聊天功能正常工作")
    else:
        print("❌ ChromaDB 仍有问题")
    print("="*60)


if __name__ == "__main__":
    main()
