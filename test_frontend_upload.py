"""测试前端上传 - 模拟浏览器请求"""
import requests

print("=" * 70)
print("测试前端上传功能")
print("=" * 70)

# 模拟前端发送的请求
url = "http://localhost:8000/api/v1/documents/upload"
headers = {
    'Origin': 'http://localhost:5174',  # 前端来源
}

try:
    print(f"\n上传 PDF 到: {url}")
    print(f"Origin: {headers['Origin']}")

    with open('论文.pdf', 'rb') as f:
        files = {'file': ('test.pdf', f, 'application/pdf')}
        response = requests.post(url, files=files, headers=headers, timeout=60)

    print(f"\n状态码: {response.status_code}")
    print(
        f"响应头 Access-Control-Allow-Origin: {response.headers.get('Access-Control-Allow-Origin', 'Not Set')}")

    if response.status_code == 201:
        data = response.json()
        print(f"\n✓ 上传成功！")
        print(f"  文档 ID: {data.get('id')}")
        print(f"  文件名: {data.get('filename')}")
        print(f"  状态: {data.get('status')}")
    else:
        print(f"\n✗ 上传失败")
        print(f"响应内容: {response.text[:500]}")

except Exception as e:
    print(f"\n✗ 请求失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)

# 测试 CORS 预检请求
print("\n测试 CORS 预检请求 (OPTIONS):")
print("=" * 70)
try:
    headers_preflight = {
        'Origin': 'http://localhost:5174',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'content-type',
    }

    response = requests.options(url, headers=headers_preflight, timeout=5)
    print(f"状态码: {response.status_code}")
    print(
        f"Access-Control-Allow-Origin: {response.headers.get('Access-Control-Allow-Origin', 'Not Set')}")
    print(
        f"Access-Control-Allow-Methods: {response.headers.get('Access-Control-Allow-Methods', 'Not Set')}")
    print(
        f"Access-Control-Allow-Headers: {response.headers.get('Access-Control-Allow-Headers', 'Not Set')}")

    if response.status_code in [200, 204]:
        print("\n✓ CORS 预检通过")
    else:
        print(f"\n✗ CORS 预检失败")

except Exception as e:
    print(f"✗ 预检请求失败: {e}")

print("\n" + "=" * 70)
