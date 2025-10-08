#!/usr/bin/env python3
"""
快速测试标注显示功能
"""
import requests
import time

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def test_create_and_list():
    print("=" * 60)
    print("测试标注创建和显示")
    print("=" * 60)
    
    # 1. 获取文档
    print("\n1. 获取文档列表...")
    resp = requests.get(f"{API_BASE}/documents")
    data = resp.json()
    docs = data.get('documents', [])
    if not docs:
        print("❌ 没有文档")
        return
    
    doc_id = docs[0]['id']
    print(f"✅ 使用文档: {docs[0].get('filename', docs[0].get('title', 'Unknown'))}")
    
    # 2. 创建一个矩形
    print("\n2. 创建矩形标注...")
    annotation_data = {
        "document_id": doc_id,
        "user_id": "test_user",
        "user_name": "Test User",
        "annotation_type": "shape",
        "page_number": 1,
        "data": {
            "id": f"test-{int(time.time())}",
            "type": "shape",
            "shapeType": "rectangle",
            "geometry": {
                "x": 50,
                "y": 50,
                "width": 100,
                "height": 80
            },
            "style": {
                "color": "#FF0000",
                "opacity": 0.8,
                "strokeWidth": 2
            }
        },
        "content": "测试矩形",
        "tags": []
    }
    
    create_resp = requests.post(f"{API_BASE}/annotations", json=annotation_data)
    if create_resp.status_code in [200, 201]:
        created = create_resp.json()
        print(f"✅ 创建成功: {created['id']}")
        annotation_id = created['id']
    else:
        print(f"❌ 创建失败: {create_resp.status_code}")
        print(f"   响应: {create_resp.text}")
        return
    
    # 3. 立即获取标注列表
    print("\n3. 获取标注列表（验证立即显示）...")
    time.sleep(0.5)  # 短暂延迟
    
    list_resp = requests.get(f"{API_BASE}/documents/{doc_id}/annotations")
    if list_resp.status_code == 200:
        annotations = list_resp.json()
        print(f"✅ 获取到 {len(annotations)} 个标注")
        
        # 查找刚创建的标注
        found = any(a['id'] == annotation_id for a in annotations)
        if found:
            print("✅ 新创建的标注在列表中")
        else:
            print("❌ 新创建的标注不在列表中")
    else:
        print(f"❌ 获取列表失败: {list_resp.status_code}")
    
    # 4. 清理
    print("\n4. 清理测试数据...")
    delete_resp = requests.delete(f"{API_BASE}/annotations/{annotation_id}")
    if delete_resp.status_code in [200, 204]:
        print("✅ 清理完成")
    
    print("\n" + "=" * 60)
    print("前端测试步骤：")
    print("1. 打开浏览器 http://localhost:5173")
    print("2. 打开一个 PDF 文档")
    print("3. 点击工具栏的「矩形」按钮")
    print("4. 在页面上绘制一个矩形")
    print("5. 检查矩形是否立即显示")
    print("6. 尝试拖拽矩形")
    print("7. 尝试调整矩形大小（拖拽角落的蓝色句柄）")
    print("8. 点击「便笺」按钮")
    print("9. 点击页面放置便笺")
    print("10. 编辑便笺内容并保存")
    print("11. 检查便笺是否显示")
    print("=" * 60)

if __name__ == "__main__":
    test_create_and_list()
