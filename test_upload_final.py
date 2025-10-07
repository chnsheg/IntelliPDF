"""最终上传测试 - 清除缓存后重新测试"""
import requests
import time

print("=" * 50)
print("开始测试文档上传...")
print("=" * 50)

# 等待后端完全启动
print("\n等待后端启动...")
time.sleep(5)

try:
    # 测试上传
    print("\n上传文件: 论文.pdf")
    with open('论文.pdf', 'rb') as f:
        response = requests.post(
            'http://localhost:8000/api/v1/documents/upload',
            files={'file': ('论文.pdf', f, 'application/pdf')},
            timeout=60
        )

    print(f"\n状态码: {response.status_code}")

    if response.status_code == 201:
        data = response.json()
        print(f"✓ 上传成功!")
        print(f"  成功标志: {data.get('success')}")
        print(f"  消息: {data.get('message')}")
        doc_data = data.get('data', {})
        print(f"  文档ID: {doc_data.get('id')}")
        print(f"  文件名: {doc_data.get('filename')}")
        print(f"  状态: {doc_data.get('processing_status')}")
        print(f"  元数据类型: {type(doc_data.get('metadata'))}")
        print(f"  元数据: {doc_data.get('metadata')}")
    else:
        print(f"✗ 上传失败")
        print(f"响应内容: {response.text[:500]}")

except Exception as e:
    print(f"✗ 测试失败: {e}")

print("\n" + "=" * 50)
