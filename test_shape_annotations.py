"""
快速测试图形标注工具

测试流程:
1. 上传 PDF
2. 创建图形标注
3. 验证后端保存
4. 查询标注列表
"""

import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1"


def test_shape_annotations():
    print("=" * 60)
    print("图形标注工具测试")
    print("=" * 60)

    # 1. 检查健康状态
    print("\n1. 检查后端健康状态...")
    try:
        resp = requests.get("http://localhost:8000/health", timeout=5)
        print(f"   ✅ 后端正常: {resp.json()}")
    except Exception as e:
        print(f"   ❌ 后端连接失败: {e}")
        return

    # 2. 获取或上传文档
    print("\n2. 获取文档列表...")
    try:
        resp = requests.get(f"{BASE_URL}/documents/", timeout=10)
        resp.raise_for_status()
        result = resp.json()
        docs = result.get('documents', [])

        if not docs or len(docs) == 0:
            print("   ⚠️  没有文档，尝试上传测试 PDF...")

            # 查找测试 PDF 文件
            test_pdfs = [
                Path("论文.pdf"),
                Path("Linux教程.pdf"),
            ]

            pdf_file = None
            for pdf in test_pdfs:
                if pdf.exists():
                    pdf_file = pdf
                    break

            if not pdf_file:
                print("   ❌ 未找到测试 PDF 文件")
                return

            print(f"   📤 上传文件: {pdf_file.name}...")
            with open(pdf_file, 'rb') as f:
                files = {'file': (pdf_file.name, f, 'application/pdf')}
                resp = requests.post(
                    f"{BASE_URL}/documents/upload", files=files, timeout=60)
                resp.raise_for_status()
                doc = resp.json()
                doc_id = doc['id']
                print(f"   ✅ 文档上传成功: {doc['filename']} (ID: {doc_id})")
        else:
            doc = docs[0]
            doc_id = doc['id']
            print(f"   ✅ 找到文档: {doc['filename']} (ID: {doc_id})")
    except Exception as e:
        print(f"   ❌ 获取/上传文档失败: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"      响应: {e.response.text}")
        return

    # 3. 创建矩形标注
    print("\n3. 创建矩形标注...")
    try:
        annotation_data = {
            "document_id": doc_id,
            "user_id": "test_user",
            "annotation_type": "shape",
            "page_number": 1,
            "data": {
                "id": "shape-test-rectangle",
                "type": "shape",
                "shapeType": "rectangle",
                "geometry": {
                    "rect": {
                        "x": 100,
                        "y": 200,
                        "width": 150,
                        "height": 80
                    }
                },
                "style": {
                    "color": "#2196F3",
                    "opacity": 0.8,
                    "strokeWidth": 2,
                    "fillColor": "#2196F3",
                    "fillOpacity": 0.2
                }
            },
            "tags": ["test", "rectangle"]
        }

        resp = requests.post(f"{BASE_URL}/annotations/",
                             json=annotation_data, timeout=10)
        resp.raise_for_status()
        annotation = resp.json()
        annotation_id_rect = annotation['id']
        print(f"   ✅ 矩形标注创建成功: {annotation_id_rect}")
        print(f"      类型: {annotation['annotation_type']}")
        print(f"      页码: {annotation['page_number']}")
    except Exception as e:
        print(f"   ❌ 创建矩形标注失败: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"      响应: {e.response.text}")
        return

    # 4. 创建圆形标注
    print("\n4. 创建圆形标注...")
    try:
        annotation_data = {
            "document_id": doc_id,
            "user_id": "test_user",
            "annotation_type": "shape",
            "page_number": 1,
            "data": {
                "id": "shape-test-circle",
                "type": "shape",
                "shapeType": "circle",
                "geometry": {
                    "rect": {
                        "x": 300,
                        "y": 200,
                        "width": 100,
                        "height": 100
                    }
                },
                "style": {
                    "color": "#4CAF50",
                    "opacity": 0.8,
                    "strokeWidth": 2,
                    "fillColor": "#4CAF50",
                    "fillOpacity": 0.2
                }
            },
            "tags": ["test", "circle"]
        }

        resp = requests.post(f"{BASE_URL}/annotations/",
                             json=annotation_data, timeout=10)
        resp.raise_for_status()
        annotation = resp.json()
        annotation_id_circle = annotation['id']
        print(f"   ✅ 圆形标注创建成功: {annotation_id_circle}")
    except Exception as e:
        print(f"   ❌ 创建圆形标注失败: {e}")

    # 5. 创建箭头标注
    print("\n5. 创建箭头标注...")
    try:
        annotation_data = {
            "document_id": doc_id,
            "user_id": "test_user",
            "annotation_type": "shape",
            "page_number": 1,
            "data": {
                "id": "shape-test-arrow",
                "type": "shape",
                "shapeType": "arrow",
                "geometry": {
                    "points": [
                        {"x": 100, "y": 400},
                        {"x": 300, "y": 450}
                    ]
                },
                "style": {
                    "color": "#F44336",
                    "opacity": 0.8,
                    "strokeWidth": 3
                }
            },
            "tags": ["test", "arrow"]
        }

        resp = requests.post(f"{BASE_URL}/annotations/",
                             json=annotation_data, timeout=10)
        resp.raise_for_status()
        annotation = resp.json()
        annotation_id_arrow = annotation['id']
        print(f"   ✅ 箭头标注创建成功: {annotation_id_arrow}")
    except Exception as e:
        print(f"   ❌ 创建箭头标注失败: {e}")

    # 6. 查询文档的所有标注
    print("\n6. 查询文档的所有标注...")
    try:
        resp = requests.get(
            f"{BASE_URL}/annotations/?document_id={doc_id}", timeout=10)
        resp.raise_for_status()
        annotations = resp.json()
        print(f"   ✅ 共有 {len(annotations)} 个标注")

        shape_annotations = [
            a for a in annotations if a['annotation_type'] == 'shape']
        print(f"   📊 其中图形标注: {len(shape_annotations)} 个")

        for ann in shape_annotations:
            data = json.loads(ann['data'])
            shape_type = data.get('shapeType', 'unknown')
            print(
                f"      - {shape_type.capitalize()}: {ann['id'][:20]}... (页码 {ann['page_number']})")
    except Exception as e:
        print(f"   ❌ 查询标注失败: {e}")

    # 7. 按类型过滤
    print("\n7. 按类型过滤图形标注...")
    try:
        resp = requests.get(
            f"{BASE_URL}/annotations/?document_id={doc_id}&annotation_type=shape",
            timeout=10
        )
        resp.raise_for_status()
        shape_annotations = resp.json()
        print(f"   ✅ 筛选出 {len(shape_annotations)} 个图形标注")
    except Exception as e:
        print(f"   ❌ 筛选失败: {e}")

    # 8. 测试删除功能（可选）
    print("\n8. 测试删除功能...")
    try:
        # 删除测试创建的标注
        resp = requests.delete(
            f"{BASE_URL}/annotations/{annotation_id_rect}", timeout=10)
        resp.raise_for_status()
        print(f"   ✅ 删除矩形标注成功")

        resp = requests.delete(
            f"{BASE_URL}/annotations/{annotation_id_circle}", timeout=10)
        resp.raise_for_status()
        print(f"   ✅ 删除圆形标注成功")

        resp = requests.delete(
            f"{BASE_URL}/annotations/{annotation_id_arrow}", timeout=10)
        resp.raise_for_status()
        print(f"   ✅ 删除箭头标注成功")
    except Exception as e:
        print(f"   ⚠️  删除失败: {e}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    print("\n前端测试步骤:")
    print("1. 打开浏览器访问 http://localhost:5174")
    print("2. 打开一个 PDF 文档")
    print("3. 点击左侧工具栏的'矩形'按钮")
    print("4. 在 PDF 页面上拖拽绘制矩形")
    print("5. 检查控制台和网络请求")
    print("6. 尝试'圆形'和'箭头'工具")


if __name__ == "__main__":
    test_shape_annotations()
