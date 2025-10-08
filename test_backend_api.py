"""
测试后端 API - 不会打断后端服务
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"


def test_health():
    """测试健康检查"""
    print("\n" + "="*70)
    print("🏥 [1/5] 测试健康检查")
    print("="*70)
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def test_get_documents():
    """测试获取文档列表"""
    print("\n" + "="*70)
    print("📄 [2/5] 测试获取文档列表")
    print("="*70)
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/documents?skip=0&limit=10", timeout=5)
        print(f"状态码: {response.status_code}")
        data = response.json()
        docs = data.get("items", [])
        print(f"找到 {len(docs)} 个文档")
        if docs:
            doc = docs[0]
            print(
                f"第一个文档: {doc.get('original_filename', doc.get('filename'))}")
            print(f"文档 ID: {doc['id']}")
            return doc['id']
        return None
    except Exception as e:
        print(f"❌ 错误: {e}")
        return None


def test_openapi_schema():
    """测试 OpenAPI Schema 生成"""
    print("\n" + "="*70)
    print("📋 [3/5] 测试 OpenAPI Schema")
    print("="*70)
    try:
        response = requests.get(f"{BASE_URL}/openapi.json", timeout=5)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            schema = response.json()
            print(f"✅ OpenAPI schema 生成成功")
            print(f"标题: {schema.get('info', {}).get('title')}")
            print(f"版本: {schema.get('info', {}).get('version')}")

            # 检查 ChatRequest schema
            schemas = schema.get('components', {}).get('schemas', {})
            if 'ChatRequest' in schemas:
                print(f"\n✅ 找到 ChatRequest schema:")
                chat_schema = schemas['ChatRequest']
                props = chat_schema.get('properties', {})
                required = chat_schema.get('required', [])
                print(f"  - 字段: {list(props.keys())}")
                print(f"  - 必需字段: {required}")
            else:
                print("⚠️ 未找到 ChatRequest schema")
            return True
        else:
            print(f"❌ OpenAPI schema 生成失败")
            print(f"错误: {response.text[:500]}")
            return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_chat_simple(doc_id):
    """测试简单的聊天请求"""
    print("\n" + "="*70)
    print("💬 [4/5] 测试简单聊天请求")
    print("="*70)

    if not doc_id:
        print("⚠️ 跳过：没有可用的文档")
        return False

    payload = {
        "question": "这个文档讲的是什么？"
    }

    print(f"文档 ID: {doc_id}")
    print(f"请求体: {json.dumps(payload, ensure_ascii=False)}")

    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/documents/{doc_id}/chat",
            json=payload,
            timeout=30
        )
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            print(f"✅ 聊天成功！")
            data = response.json()
            answer = data.get('answer', '')
            print(f"回答: {answer[:100]}...")
            return True
        else:
            print(f"❌ 聊天失败")
            print(f"响应: {response.text[:500]}")
            return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_chat_full(doc_id):
    """测试完整参数的聊天请求"""
    print("\n" + "="*70)
    print("💬 [5/5] 测试完整聊天请求（带所有参数）")
    print("="*70)

    if not doc_id:
        print("⚠️ 跳过：没有可用的文档")
        return False

    payload = {
        "question": "总结一下主要内容",
        "conversation_history": [],
        "top_k": 5,
        "temperature": 0.7
    }

    print(f"文档 ID: {doc_id}")
    print(f"请求体: {json.dumps(payload, ensure_ascii=False, indent=2)}")

    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/documents/{doc_id}/chat",
            json=payload,
            timeout=30
        )
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            print(f"✅ 聊天成功！")
            data = response.json()
            answer = data.get('answer', '')
            sources = data.get('sources', [])
            print(f"回答: {answer[:100]}...")
            print(f"来源数量: {len(sources)}")
            return True
        else:
            print(f"❌ 聊天失败")
            print(f"响应: {response.text[:500]}")
            return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("="*70)
    print("🧪 IntelliPDF 后端 API 测试")
    print("="*70)
    print(f"基础 URL: {BASE_URL}")

    results = []

    # 测试 1: 健康检查
    results.append(("健康检查", test_health()))

    # 测试 2: 获取文档
    doc_id = test_get_documents()
    results.append(("获取文档列表", doc_id is not None))

    # 测试 3: OpenAPI Schema
    results.append(("OpenAPI Schema", test_openapi_schema()))

    # 测试 4: 简单聊天
    results.append(("简单聊天", test_chat_simple(doc_id)))

    # 测试 5: 完整聊天
    results.append(("完整聊天", test_chat_full(doc_id)))

    # 总结
    print("\n" + "="*70)
    print("📊 测试结果汇总")
    print("="*70)

    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} - {name}")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    print("\n" + "="*70)
    print(f"总计: {passed}/{total} 测试通过")
    print("="*70)

    if passed == total:
        print("\n🎉 所有测试通过！后端 API 工作正常")
        print("\n💡 下一步:")
        print("1. 前端可能需要重启 (cd frontend; npm run dev)")
        print("2. 在浏览器测试 AI 聊天功能")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请查看上面的详细信息")
        return 1


if __name__ == "__main__":
    sys.exit(main())
