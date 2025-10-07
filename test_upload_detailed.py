"""详细上传测试 - 检查完整响应"""
import requests
import json

print("=" * 60)
print("测试文档上传 - 完整响应分析")
print("=" * 60)

try:
    # 上传文件
    with open('论文.pdf', 'rb') as f:
        response = requests.post(
            'http://localhost:8000/api/v1/documents/upload',
            files={'file': ('论文.pdf', f, 'application/pdf')},
            timeout=60
        )

    print(f"\n状态码: {response.status_code}")
    print(f"响应头: {dict(response.headers)}\n")

    if response.status_code == 201:
        print("✓ 上传成功！")
        print("\n原始响应内容:")
        print(response.text)

        try:
            data = response.json()
            print("\n解析后的 JSON:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"\n✗ JSON 解析失败: {e}")
    else:
        print(f"✗ 上传失败")
        print(f"响应内容: {response.text}")

except Exception as e:
    print(f"✗ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
