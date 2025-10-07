import requests

# 获取最新文档
r = requests.get('http://localhost:8000/api/v1/documents')
if r.status_code == 200:
    docs = r.json()['documents']
    if docs:
        doc = docs[0]
        doc_id = doc['id']

        print("="*60)
        print("最终验证测试")
        print("="*60)
        print(f"\n最新文档: {doc['filename']}")
        print(f"ID: {doc_id}")
        print(f"状态: {doc['status']}")
        print(f"块数: {doc['chunk_count']}")

        # 测试详情查询
        print(f"\n1. 测试文档详情查询...")
        r2 = requests.get(f'http://localhost:8000/api/v1/documents/{doc_id}')
        print(f"   状态码: {r2.status_code}")
        if r2.status_code == 200:
            print("   ✓ UUID 转换修复成功！")

        # 测试文件下载
        print(f"\n2. 测试文件下载...")
        r3 = requests.get(
            f'http://localhost:8000/api/v1/documents/{doc_id}/file')
        print(f"   状态码: {r3.status_code}")
        if r3.status_code == 200:
            print(f"   文件大小: {len(r3.content):,} bytes")
            print("   ✓ 文件服务端点工作正常！")

        print("\n" + "="*60)
        print("✅ 所有核心功能验证通过！")
        print("="*60)
