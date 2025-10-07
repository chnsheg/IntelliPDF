#!/usr/bin/env python
"""快速API测试 - 测试关键修复"""
import requests
import time

BASE_URL = "http://localhost:8000"


def test_api():
    print("="*60)
    print("IntelliPDF 关键 API 快速测试")
    print("="*60)

    # 等待服务器启动
    print("\n等待服务器启动...")
    time.sleep(20)

    # 1. 测试健康检查
    print("\n1. 测试健康检查 /health")
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"   状态码: {r.status_code}")
        if r.status_code == 200:
            print(f"   响应: {r.json()}")
            print("   ✓ 健康检查修复成功！")
        else:
            print(f"   ✗ 失败: {r.text}")
    except Exception as e:
        print(f"   ✗ 错误: {e}")

    # 2. 测试文档获取by ID
    print("\n2. 测试文档获取 /api/v1/documents/{id}")
    doc_id = "4e637fab-bcd1-44af-ba7b-37f0db6e01e6"
    try:
        r = requests.get(f"{BASE_URL}/api/v1/documents/{doc_id}", timeout=5)
        print(f"   状态码: {r.status_code}")
        if r.status_code == 200:
            doc = r.json()
            print(f"   文档: {doc['filename']}")
            print(f"   状态: {doc['status']}")
            print("   ✓ UUID转换修复成功！")
        else:
            print(f"   ✗ 失败: {r.text[:200]}")
    except Exception as e:
        print(f"   ✗ 错误: {e}")

    # 3. 测试文档块获取
    print("\n3. 测试文档块获取 /api/v1/documents/{id}/chunks")
    try:
        r = requests.get(
            f"{BASE_URL}/api/v1/documents/{doc_id}/chunks", timeout=5)
        print(f"   状态码: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"   块数量: {data.get('total', 0)}")
            print("   ✓ 块查询修复成功！")
        else:
            print(f"   ✗ 失败: {r.text[:200]}")
    except Exception as e:
        print(f"   ✗ 错误: {e}")

    # 4. 测试文件访问
    print("\n4. 测试文件访问 /api/v1/documents/{id}/file")
    try:
        r = requests.get(
            f"{BASE_URL}/api/v1/documents/{doc_id}/file", timeout=5)
        print(f"   状态码: {r.status_code}")
        if r.status_code == 200:
            print(f"   Content-Type: {r.headers.get('Content-Type')}")
            print(f"   文件大小: {len(r.content)} bytes")
            print("   ✓ 文件服务端点工作正常！")
        else:
            print(f"   ✗ 失败: {r.text[:200]}")
    except Exception as e:
        print(f"   ✗ 错误: {e}")

    # 5. 测试文档上传（检查处理是否修复）
    print("\n5. 测试文档上传（检查'content'错误修复）")
    print("   跳过上传测试（避免重复文档）")
    print("   检查现有失败文档...")
    try:
        r = requests.get(f"{BASE_URL}/api/v1/documents/statistics", timeout=5)
        if r.status_code == 200:
            stats = r.json()
            print(f"   总文档: {stats.get('total', 0)}")
            print(f"   状态分布: {stats.get('by_status', {})}")
    except Exception as e:
        print(f"   ✗ 错误: {e}")

    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)


if __name__ == "__main__":
    test_api()
