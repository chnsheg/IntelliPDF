"""完整 API 测试 - 测试所有文档端点"""
import requests
import json

API_BASE = "http://localhost:8000/api/v1/documents"

print("=" * 70)
print("IntelliPDF 文档 API 完整测试")
print("=" * 70)

# 测试 1: 上传文档
print("\n[测试 1] 上传文档")
print("-" * 70)
try:
    with open('论文.pdf', 'rb') as f:
        r = requests.post(
            f"{API_BASE}/upload", files={'file': ('test.pdf', f, 'application/pdf')}, timeout=60)

    if r.status_code == 201:
        data = r.json()
        doc_id = data['id']
        print(f"✓ 上传成功 (201)")
        print(f"  文档 ID: {doc_id}")
        print(f"  文件名: {data['filename']}")
        print(f"  状态: {data['status']}")
        print(f"  元数据类型: {type(data['metadata'])}")
        print(
            f"  元数据键: {list(data['metadata'].keys()) if isinstance(data['metadata'], dict) else 'N/A'}")
    else:
        print(f"✗ 上传失败 ({r.status_code})")
        print(f"  响应: {r.text[:200]}")
except Exception as e:
    print(f"✗ 测试失败: {e}")
    doc_id = None

# 测试 2: 获取文档列表
print("\n[测试 2] 获取文档列表")
print("-" * 70)
try:
    r = requests.get(
        f"{API_BASE}/", params={'skip': 0, 'limit': 5}, timeout=10)

    if r.status_code == 200:
        data = r.json()
        print(f"✓ 获取成功 (200)")
        print(f"  总数: {data['total']}")
        print(f"  返回: {len(data['documents'])} 个文档")
        if data['documents']:
            first_doc = data['documents'][0]
            print(f"  第一个文档:")
            print(f"    ID: {first_doc.get('id')}")
            print(f"    文件名: {first_doc.get('filename')}")
            print(f"    元数据类型: {type(first_doc.get('metadata'))}")
    else:
        print(f"✗ 获取失败 ({r.status_code}): {r.text[:200]}")
except Exception as e:
    print(f"✗ 测试失败: {e}")

# 测试 3: 获取单个文档
if doc_id:
    print("\n[测试 3] 获取单个文档")
    print("-" * 70)
    try:
        r = requests.get(f"{API_BASE}/{doc_id}", timeout=10)

        if r.status_code == 200:
            data = r.json()
            print(f"✓ 获取成功 (200)")
            print(f"  文档 ID: {data['id']}")
            print(f"  文件名: {data['filename']}")
            print(f"  文件大小: {data['file_size']} 字节")
            print(f"  状态: {data['status']}")
            print(f"  块数量: {data['chunk_count']}")
            print(f"  元数据类型: {type(data['metadata'])}")
            print(
                f"  元数据: {json.dumps(data['metadata'], ensure_ascii=False, indent=4)}")
        else:
            print(f"✗ 获取失败 ({r.status_code}): {r.text[:200]}")
    except Exception as e:
        print(f"✗ 测试失败: {e}")

print("\n" + "=" * 70)
print("测试完成！")
print("=" * 70)
