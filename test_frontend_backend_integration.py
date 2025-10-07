#!/usr/bin/env python3
"""
前后端集成测试脚本
验证后端 API 和前端服务是否正常运行
"""

import requests
import time
from pathlib import Path

BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5174"


def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def test_backend():
    """测试后端服务"""
    print_section("后端服务测试")

    # 1. Health check
    print("\n1. 测试健康检查端点...")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        assert response.status_code == 200, "健康检查失败"
        print("   ✅ 健康检查通过")
    except Exception as e:
        print(f"   ❌ 健康检查失败: {e}")
        return False

    # 2. Get documents
    print("\n2. 测试获取文档列表...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/documents", timeout=5)
        print(f"   状态码: {response.status_code}")
        data = response.json()
        print(f"   文档数: {data.get('total', 0)}")
        if data.get('documents'):
            latest_doc = data['documents'][0]
            print(f"   最新文档: {latest_doc['filename']}")
            print(f"   文档 ID: {latest_doc['id']}")
            print(f"   状态: {latest_doc['status']}")
            print(f"   块数: {latest_doc.get('num_chunks', 0)}")
            print("   ✅ 文档列表获取成功")
            return latest_doc['id']
        else:
            print("   ⚠️ 没有文档")
            return None
    except Exception as e:
        print(f"   ❌ 获取文档列表失败: {e}")
        return False


def test_document_access(doc_id):
    """测试文档访问"""
    if not doc_id:
        print("\n跳过文档访问测试（没有文档）")
        return

    print_section("文档访问测试")

    # 1. Get document by ID
    print(f"\n1. 测试获取文档详情 (ID: {doc_id})...")
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/v1/documents/{doc_id}", timeout=5)
        print(f"   状态码: {response.status_code}")
        data = response.json()
        print(f"   文件名: {data['filename']}")
        print(f"   状态: {data['status']}")
        print(f"   大小: {data['file_size']} bytes")
        print("   ✅ 文档详情获取成功")
    except Exception as e:
        print(f"   ❌ 获取文档详情失败: {e}")

    # 2. Get document file
    print(f"\n2. 测试文件下载端点...")
    try:
        response = requests.head(
            f"{BACKEND_URL}/api/v1/documents/{doc_id}/file", timeout=5)
        print(f"   状态码: {response.status_code}")
        content_length = response.headers.get('content-length', 'unknown')
        print(f"   文件大小: {content_length} bytes")
        print("   ✅ 文件下载端点可访问")
    except Exception as e:
        print(f"   ❌ 文件下载端点失败: {e}")

    # 3. Get document chunks
    print(f"\n3. 测试获取文档块...")
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/v1/documents/{doc_id}/chunks",
            params={"skip": 0, "limit": 5},
            timeout=5
        )
        print(f"   状态码: {response.status_code}")
        data = response.json()
        print(f"   总块数: {data.get('total', 0)}")
        print(f"   返回块数: {len(data.get('chunks', []))}")
        if data.get('chunks'):
            chunk = data['chunks'][0]
            print(f"   第一个块:")
            print(f"     - ID: {chunk['id']}")
            print(f"     - 类型: {chunk['chunk_type']}")
            print(f"     - 页码: {chunk.get('start_page', 'N/A')}")
            print(f"     - 内容长度: {len(chunk.get('content', ''))} 字符")
        print("   ✅ 文档块获取成功")
    except Exception as e:
        print(f"   ❌ 获取文档块失败: {e}")


def test_frontend():
    """测试前端服务"""
    print_section("前端服务测试")

    print("\n测试前端页面访问...")
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        print(f"   状态码: {response.status_code}")
        print(f"   内容长度: {len(response.text)} bytes")

        # 检查是否是有效的 HTML
        if '<html' in response.text.lower() or '<!doctype' in response.text.lower():
            print("   ✅ 前端页面正常")
            return True
        else:
            print("   ⚠️ 响应不是有效的 HTML")
            return False
    except Exception as e:
        print(f"   ❌ 前端服务无法访问: {e}")
        return False


def test_statistics():
    """测试统计端点"""
    print_section("统计数据测试")

    print("\n测试文档统计...")
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/v1/documents/statistics", timeout=5)
        print(f"   状态码: {response.status_code}")
        data = response.json()
        print(f"   总文档数: {data.get('total', 0)}")
        print(f"   按状态分布: {data.get('by_status', {})}")
        print(f"   总大小: {data.get('total_size', 0)} bytes")
        print("   ✅ 统计数据获取成功")
    except Exception as e:
        print(f"   ❌ 获取统计数据失败: {e}")


def main():
    print("="*60)
    print("  IntelliPDF 前后端集成测试")
    print("="*60)
    print(f"\n后端 URL: {BACKEND_URL}")
    print(f"前端 URL: {FRONTEND_URL}")
    print("\n开始测试...")

    # 测试后端
    doc_id = test_backend()

    # 测试文档访问
    if doc_id:
        test_document_access(doc_id)

    # 测试统计
    test_statistics()

    # 测试前端
    test_frontend()

    # 总结
    print_section("测试总结")
    print("\n✅ 测试完成！")
    print("\n前端访问地址: http://localhost:5174")
    print("后端 API 文档: http://localhost:8000/api/docs")
    print("\n现在可以通过浏览器访问前端进行测试：")
    print("  1. 首页: http://localhost:5174")
    print("  2. 文档管理: http://localhost:5174/documents")
    print("  3. 上传文档: http://localhost:5174/upload")
    if doc_id:
        print(f"  4. 文档详情: http://localhost:5174/document/{doc_id}")


if __name__ == "__main__":
    main()
