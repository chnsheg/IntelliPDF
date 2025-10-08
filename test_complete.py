"""
完整的后端 API 测试套件
包含所有功能测试，包括 Gemini API 集成
"""

import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"


def print_header(title):
    print("\n" + "=" * 70)
    print(f"🧪 {title}")
    print("=" * 70)


def print_success(message):
    print(f"✅ {message}")


def print_error(message):
    print(f"❌ {message}")


def print_info(message):
    print(f"ℹ️  {message}")


def test_health():
    """测试健康检查端点"""
    print_header("[1/8] 测试健康检查")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"健康检查通过: {data}")
            return True
        else:
            print_error(f"健康检查失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print_error(f"健康检查异常: {e}")
        return False


def test_openapi_schema():
    """测试 OpenAPI schema 生成"""
    print_header("[2/8] 测试 OpenAPI Schema 生成")
    try:
        response = requests.get(f"{BASE_URL}/openapi.json", timeout=5)
        if response.status_code == 200:
            schema = response.json()
            print_success(f"OpenAPI Schema 生成成功")

            # 检查关键路径
            paths = schema.get('paths', {})
            if '/api/v1/documents/{document_id}/chat' in paths:
                print_success("Chat 端点存在于 schema 中")

                # 检查 ChatRequest schema
                chat_path = paths['/api/v1/documents/{document_id}/chat']
                if 'post' in chat_path:
                    print_success("Chat POST 方法定义正确")

                    # 检查请求体 schema
                    request_body = chat_path['post'].get('requestBody', {})
                    if request_body:
                        print_info("ChatRequest schema 定义:")
                        content = request_body.get(
                            'content', {}).get('application/json', {})
                        schema_ref = content.get('schema', {})
                        print(json.dumps(schema_ref, indent=2))
                        return True

            print_error("Chat 端点未在 schema 中找到")
            return False
        else:
            print_error(f"OpenAPI Schema 获取失败: HTTP {response.status_code}")
            print_error(f"响应: {response.text[:500]}")
            return False
    except Exception as e:
        print_error(f"OpenAPI Schema 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_get_documents():
    """测试获取文档列表"""
    print_header("[3/8] 测试获取文档列表")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/documents?skip=0&limit=10", timeout=5)
        if response.status_code == 200:
            data = response.json()
            count = len(data.get('items', []))
            print_success(f"成功获取文档列表: {count} 个文档")
            if count > 0:
                # 返回第一个文档 ID 用于后续测试
                first_doc = data['items'][0]
                doc_id = first_doc.get('id')
                doc_name = first_doc.get('filename', 'Unknown')
                print_info(f"第一个文档: {doc_name} (ID: {doc_id})")
                return doc_id
            else:
                print_info("没有文档，跳过聊天测试")
                return None
        else:
            print_error(f"获取文档列表失败: HTTP {response.status_code}")
            return None
    except Exception as e:
        print_error(f"获取文档列表异常: {e}")
        return None


def test_gemini_connection():
    """测试 Gemini API 连接"""
    print_header("[4/8] 测试 Gemini API 连接")
    try:
        # 直接测试 Gemini 端点
        gemini_url = "http://152.32.207.237:8132/v1beta/models"
        print_info(f"测试 Gemini API: {gemini_url}")

        response = requests.get(gemini_url, timeout=10)
        if response.status_code == 200:
            print_success("Gemini API 连接成功")
            return True
        else:
            print_error(f"Gemini API 连接失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Gemini API 连接异常: {e}")
        return False


def test_upload_pdf():
    """测试上传 PDF"""
    print_header("[5/8] 测试上传 PDF")

    # 查找项目中的 PDF 文件
    pdf_files = list(Path("D:/IntelliPDF").glob("*.pdf"))
    if not pdf_files:
        print_error("未找到 PDF 文件，跳过上传测试")
        return None

    pdf_file = pdf_files[0]
    print_info(f"使用 PDF: {pdf_file.name}")

    try:
        with open(pdf_file, 'rb') as f:
            files = {'file': (pdf_file.name, f, 'application/pdf')}
            response = requests.post(
                f"{BASE_URL}/api/v1/documents/upload",
                files=files,
                timeout=120
            )

        if response.status_code == 200:
            data = response.json()
            doc_id = data.get('id')
            print_success(f"PDF 上传成功: {pdf_file.name}")
            print_info(f"文档 ID: {doc_id}")
            return doc_id
        else:
            print_error(f"PDF 上传失败: HTTP {response.status_code}")
            print_error(f"响应: {response.text[:500]}")
            return None
    except Exception as e:
        print_error(f"PDF 上传异常: {e}")
        return None


def test_chat_simple(document_id):
    """测试简单聊天（只有问题）"""
    print_header("[6/8] 测试简单聊天请求")

    if not document_id:
        print_info("没有可用的文档，跳过测试")
        return False

    try:
        payload = {
            "question": "这个文档的主要内容是什么？"
        }

        print_info(f"发送请求到: {BASE_URL}/api/v1/documents/{document_id}/chat")
        print_info(f"请求数据: {json.dumps(payload, ensure_ascii=False)}")

        response = requests.post(
            f"{BASE_URL}/api/v1/documents/{document_id}/chat",
            json=payload,
            timeout=30
        )

        print_info(f"响应状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            answer = data.get('answer', '')
            print_success("简单聊天请求成功")
            print_info(f"AI 回答: {answer[:200]}...")
            return True
        else:
            print_error(f"简单聊天请求失败: HTTP {response.status_code}")
            print_error(f"响应: {response.text[:500]}")
            return False
    except Exception as e:
        print_error(f"简单聊天请求异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_chat_full(document_id):
    """测试完整聊天（带所有参数）"""
    print_header("[7/8] 测试完整聊天请求（带所有参数）")

    if not document_id:
        print_info("没有可用的文档，跳过测试")
        return False

    try:
        payload = {
            "question": "请总结一下文档的核心观点",
            "conversation_history": [
                {
                    "role": "user",
                    "content": "你好",
                    "timestamp": "2025-10-08T10:00:00"
                },
                {
                    "role": "assistant",
                    "content": "你好！我可以帮你分析这个文档。",
                    "timestamp": "2025-10-08T10:00:01"
                }
            ],
            "top_k": 5,
            "temperature": 0.7
        }

        print_info(f"发送请求到: {BASE_URL}/api/v1/documents/{document_id}/chat")
        print_info(
            f"请求数据: {json.dumps(payload, ensure_ascii=False, indent=2)}")

        response = requests.post(
            f"{BASE_URL}/api/v1/documents/{document_id}/chat",
            json=payload,
            timeout=30
        )

        print_info(f"响应状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            answer = data.get('answer', '')
            print_success("完整聊天请求成功")
            print_info(f"AI 回答: {answer[:200]}...")

            # 检查相关上下文
            contexts = data.get('relevant_contexts', [])
            print_info(f"找到 {len(contexts)} 个相关上下文")

            return True
        else:
            print_error(f"完整聊天请求失败: HTTP {response.status_code}")
            print_error(f"响应: {response.text[:500]}")
            return False
    except Exception as e:
        print_error(f"完整聊天请求异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_bookmarks(document_id):
    """测试书签功能"""
    print_header("[8/8] 测试书签功能")

    if not document_id:
        print_info("没有可用的文档，跳过测试")
        return False

    try:
        # 获取书签列表
        response = requests.get(
            f"{BASE_URL}/api/v1/bookmarks/",
            params={"document_id": document_id, "limit": 100},
            timeout=5
        )

        if response.status_code == 200:
            bookmarks = response.json()
            count = len(bookmarks)
            print_success(f"成功获取书签列表: {count} 个书签")

            if count > 0:
                first_bookmark = bookmarks[0]
                print_info(
                    f"第一个书签: {first_bookmark.get('title', 'Untitled')} (页面 {first_bookmark.get('page_number')})")

            return True
        else:
            print_error(f"获取书签失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print_error(f"书签测试异常: {e}")
        return False


def main():
    print_header("IntelliPDF 完整后端 API 测试套件")
    print_info(f"基础 URL: {BASE_URL}")
    print_info(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    results = {}

    # 1. 健康检查
    results['health'] = test_health()

    if not results['health']:
        print_error("\n⚠️ 后端服务未运行，请先启动后端服务！")
        return

    # 2. OpenAPI Schema
    results['openapi'] = test_openapi_schema()

    # 3. 获取文档列表
    document_id = test_get_documents()

    # 4. Gemini 连接
    results['gemini'] = test_gemini_connection()

    # 5. 上传 PDF（如果没有文档）
    if not document_id:
        document_id = test_upload_pdf()
        time.sleep(3)  # 等待处理完成

    # 6. 简单聊天
    results['chat_simple'] = test_chat_simple(document_id)

    # 7. 完整聊天
    results['chat_full'] = test_chat_full(document_id)

    # 8. 书签
    results['bookmarks'] = test_bookmarks(document_id)

    # 汇总结果
    print_header("测试结果汇总")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {test_name}")

    print("\n" + "=" * 70)
    print(f"📊 总计: {passed}/{total} 测试通过 ({passed/total*100:.1f}%)")
    print("=" * 70)

    if passed == total:
        print_success("\n🎉 所有测试通过！后端 API 和 Gemini 集成工作正常。")
        print_info("下一步：重启前端服务并在浏览器中测试")
    else:
        print_error(f"\n⚠️ {total - passed} 个测试失败，请检查上面的详细信息")


if __name__ == "__main__":
    main()
    input("\n按 Enter 键关闭...")
