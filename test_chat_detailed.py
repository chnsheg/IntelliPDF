"""
详细测试 AI 聊天 422 错误 - 带请求体日志
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

print("="*70)
print("🧪 AI 聊天 422 错误详细测试")
print("="*70)

# 1. 获取文档列表
print("\n[1/5] 获取文档列表...")
try:
    response = requests.get(f"{BASE_URL}/documents?skip=0&limit=10", timeout=5)
    response.raise_for_status()
    body = response.json()
    # Support two possible response shapes used across the codebase:
    # - {"items": [...]} (older tests)
    # - {"documents": [...], "total": n} (current API)
    docs = body.get("items") or body.get("documents") or []
    print(f"✅ 找到 {len(docs)} 个文档")

    if not docs:
        print("❌ 没有文档可供测试")
        exit(1)

    # 使用第一个文档
    doc = docs[0]
    doc_id = doc["id"]
    doc_name = doc.get("original_filename", doc.get("filename", "未知"))
    print(f"📄 测试文档: {doc_name}")
    print(f"🔑 文档 ID: {doc_id}")

except Exception as e:
    print(f"❌ 获取文档失败: {e}")
    exit(1)

# 2. 测试最简单的请求（只有 question）
print(f"\n[2/5] 测试最简单请求 (只有question)...")
payload1 = {
    "question": "这个文档讲的是什么？"
}
print(f"📤 请求体: {json.dumps(payload1, ensure_ascii=False, indent=2)}")

try:
    response = requests.post(
        f"{BASE_URL}/documents/{doc_id}/chat",
        json=payload1,
        timeout=30
    )
    print(f"📊 响应状态码: {response.status_code}")

    if response.status_code == 200:
        print("✅ 测试1成功！")
        data = response.json()
        print(f"📝 回答: {data.get('answer', '')[:100]}...")
    elif response.status_code == 422:
        print(f"❌ 测试1失败 (422)")
        print(f"错误详情: {response.text}")
    else:
        print(f"⚠️ 其他错误: {response.status_code}")
        print(f"响应: {response.text}")
except Exception as e:
    print(f"❌ 请求异常: {e}")

time.sleep(1)

# 3. 测试带完整参数的请求
print(f"\n[3/5] 测试完整请求 (所有参数)...")
payload2 = {
    "question": "总结一下文档的主要内容",
    "conversation_history": [],
    "top_k": 5,
    "temperature": 0.7
}
print(f"📤 请求体: {json.dumps(payload2, ensure_ascii=False, indent=2)}")

try:
    response = requests.post(
        f"{BASE_URL}/documents/{doc_id}/chat",
        json=payload2,
        timeout=30
    )
    print(f"📊 响应状态码: {response.status_code}")

    if response.status_code == 200:
        print("✅ 测试2成功！")
        data = response.json()
        print(f"📝 回答: {data.get('answer', '')[:100]}...")
    elif response.status_code == 422:
        print(f"❌ 测试2失败 (422)")
        print(f"错误详情: {response.text}")
    else:
        print(f"⚠️ 其他错误: {response.status_code}")
        print(f"响应: {response.text}")
except Exception as e:
    print(f"❌ 请求异常: {e}")

time.sleep(1)

# 4. 测试带对话历史的请求
print(f"\n[4/5] 测试带对话历史...")
payload3 = {
    "question": "更详细地解释一下",
    "conversation_history": [
        {
            "role": "user",
            "content": "这个文档讲什么？",
            "timestamp": "2025-10-08T10:00:00Z"
        },
        {
            "role": "assistant",
            "content": "这是一个技术文档",
            "timestamp": "2025-10-08T10:00:05Z"
        }
    ],
    "top_k": 5,
    "temperature": 0.7
}
print(f"📤 请求体: {json.dumps(payload3, ensure_ascii=False, indent=2)}")

try:
    response = requests.post(
        f"{BASE_URL}/documents/{doc_id}/chat",
        json=payload3,
        timeout=30
    )
    print(f"📊 响应状态码: {response.status_code}")

    if response.status_code == 200:
        print("✅ 测试3成功！")
        data = response.json()
        print(f"📝 回答: {data.get('answer', '')[:100]}...")
    elif response.status_code == 422:
        print(f"❌ 测试3失败 (422)")
        print(f"错误详情: {response.text}")
    else:
        print(f"⚠️ 其他错误: {response.status_code}")
        print(f"响应: {response.text}")
except Exception as e:
    print(f"❌ 请求异常: {e}")

time.sleep(1)

# 5. 测试 schema 验证 - 直接检查后端 schema
print(f"\n[5/5] 获取 API schema...")
try:
    response = requests.get("http://localhost:8000/openapi.json", timeout=5)
    if response.status_code == 200:
        openapi = response.json()
        # 查找 ChatRequest schema
        schemas = openapi.get("components", {}).get("schemas", {})
        if "ChatRequest" in schemas:
            print("✅ 找到 ChatRequest schema:")
            chat_schema = schemas["ChatRequest"]
            print(json.dumps(chat_schema, indent=2, ensure_ascii=False))
        else:
            print("⚠️ 未找到 ChatRequest schema")
    else:
        print(f"⚠️ 无法获取 OpenAPI schema: {response.status_code}")
except Exception as e:
    print(f"⚠️ 获取 schema 失败: {e}")

print("\n" + "="*70)
print("🏁 测试完成")
print("="*70)
print("\n💡 提示:")
print("1. 如果所有测试都是 422，检查后端日志中的 'Chat request received' 日志")
print("2. 检查后端是否重新加载了最新代码")
print("3. 检查前端是否发送了额外的字段")
