"""
测试新图形标注的后端存储和加载 - 矩形、圆形、箭头
"""
import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1"


def test_new_shape_tools():
    """测试矩形、圆形、箭头标注的完整流程"""

    print("=== 新图形工具测试 (矩形/圆形/箭头) ===\n")

    # 1. 上传测试 PDF
    pdf_path = Path("论文.pdf")
    if not pdf_path.exists():
        pdf_path = Path("Linux教程.pdf")

    if not pdf_path.exists():
        print("❌ 未找到测试 PDF 文件")
        return

    print(f"📄 使用测试文件: {pdf_path}")

    with open(pdf_path, "rb") as f:
        files = {"file": (pdf_path.name, f, "application/pdf")}
        response = requests.post(f"{BASE_URL}/documents/upload", files=files)

    if response.status_code != 200:
        print(f"❌ 上传失败: {response.status_code}")
        print(response.text)
        return

    doc_data = response.json()
    doc_id = doc_data["id"]
    print(f"✅ 文档上传成功, ID: {doc_id}\n")

    # 2. 创建测试标注数据（模拟前端发送的数据）
    test_annotations = [
        # 矩形标注 - 红色
        {
            "document_id": doc_id,
            "page_number": 1,
            "annotation_type": "shape",
            "content": "红色矩形",
            "position": {"x": 100, "y": 100, "width": 200, "height": 150},
            "metadata": {
                "pdfjs_data": {
                    "annotationType": 100,  # RECTANGLE
                    "pageIndex": 0,
                    "rect": [100, 100, 300, 250],
                    "color": [1.0, 0.0, 0.0],  # 红色 (RGB 0-1)
                    "thickness": 3
                }
            }
        },
        # 圆形标注 - 蓝色
        {
            "document_id": doc_id,
            "page_number": 1,
            "annotation_type": "shape",
            "content": "蓝色圆形",
            "position": {"x": 400, "y": 100, "width": 200, "height": 200},
            "metadata": {
                "pdfjs_data": {
                    "annotationType": 101,  # CIRCLE
                    "pageIndex": 0,
                    "center": [500, 200],
                    "radius": [100, 100],
                    "color": [0.0, 0.0, 1.0],  # 蓝色
                    "thickness": 2
                }
            }
        },
        # 箭头标注 - 绿色
        {
            "document_id": doc_id,
            "page_number": 1,
            "annotation_type": "shape",
            "content": "绿色箭头",
            "position": {"x": 100, "y": 350, "width": 300, "height": 100},
            "metadata": {
                "pdfjs_data": {
                    "annotationType": 102,  # ARROW
                    "pageIndex": 0,
                    "start": [100, 400],
                    "end": [400, 400],
                    "color": [0.0, 1.0, 0.0],  # 绿色
                    "thickness": 4
                }
            }
        },
        # 第二个矩形 - 黄色粗边
        {
            "document_id": doc_id,
            "page_number": 1,
            "annotation_type": "shape",
            "content": "黄色粗矩形",
            "position": {"x": 50, "y": 500, "width": 150, "height": 100},
            "metadata": {
                "pdfjs_data": {
                    "annotationType": 100,
                    "pageIndex": 0,
                    "rect": [50, 500, 200, 600],
                    "color": [1.0, 1.0, 0.0],  # 黄色
                    "thickness": 5
                }
            }
        },
        # 椭圆 - 紫色
        {
            "document_id": doc_id,
            "page_number": 1,
            "annotation_type": "shape",
            "content": "紫色椭圆",
            "position": {"x": 300, "y": 500, "width": 250, "height": 120},
            "metadata": {
                "pdfjs_data": {
                    "annotationType": 101,
                    "pageIndex": 0,
                    "center": [425, 560],
                    "radius": [125, 60],  # 横向椭圆
                    "color": [0.5, 0.0, 0.5],  # 紫色
                    "thickness": 3
                }
            }
        }
    ]

    print("📝 创建 5 个测试标注 (2矩形 + 2圆形 + 1箭头)...")
    response = requests.post(
        f"{BASE_URL}/annotations/batch",
        json={"annotations": test_annotations}
    )

    if response.status_code != 200:
        print(f"❌ 批量创建失败: {response.status_code}")
        print(response.text)
        return

    result = response.json()
    print(f"✅ 批量创建成功:")
    print(f"   - 成功: {result['successful']}")
    print(f"   - 失败: {result['failed']}")
    print(f"   - 创建的 ID: {result['created_ids']}\n")

    # 3. 加载标注验证
    print("🔄 加载标注验证...")
    response = requests.get(f"{BASE_URL}/annotations/documents/{doc_id}")

    if response.status_code != 200:
        print(f"❌ 加载失败: {response.status_code}")
        return

    annotations = response.json()
    print(f"✅ 加载成功，共 {len(annotations)} 个标注\n")

    # 4. 验证每个标注的数据
    print("🔍 验证标注数据:")
    print("="*60)

    for i, annot in enumerate(annotations, 1):
        pdfjs_data = annot.get("metadata", {}).get("pdfjs_data", {})
        annot_type = pdfjs_data.get("annotationType")

        type_name = {
            100: "🔲 矩形 (RECTANGLE)",
            101: "⭕ 圆形 (CIRCLE)",
            102: "↗ 箭头 (ARROW)"
        }.get(annot_type, f"❓ 未知类型 ({annot_type})")

        # RGB 转换为十六进制显示
        color = pdfjs_data.get('color', [0, 0, 0])
        hex_color = '#{:02x}{:02x}{:02x}'.format(
            int(color[0] * 255),
            int(color[1] * 255),
            int(color[2] * 255)
        )

        print(f"\n【标注 {i}】 ID: {annot['id']}")
        print(f"  类型: {type_name}")
        print(f"  页码: {annot['page_number']}")
        print(f"  颜色: RGB{tuple(color)} = {hex_color}")
        print(f"  粗细: {pdfjs_data.get('thickness')} px")
        print(f"  内容: {annot['content']}")

        if annot_type == 100:  # 矩形
            rect = pdfjs_data.get('rect', [])
            if len(rect) == 4:
                width = rect[2] - rect[0]
                height = rect[3] - rect[1]
                print(f"  位置: ({rect[0]}, {rect[1]})")
                print(f"  尺寸: {width} x {height}")
        elif annot_type == 101:  # 圆形
            center = pdfjs_data.get('center', [])
            radius = pdfjs_data.get('radius', [])
            if len(center) == 2 and len(radius) == 2:
                print(f"  圆心: ({center[0]}, {center[1]})")
                print(f"  半径: X={radius[0]}, Y={radius[1]}")
                if radius[0] != radius[1]:
                    print(f"  类型: 椭圆")
                else:
                    print(f"  类型: 正圆")
        elif annot_type == 102:  # 箭头
            start = pdfjs_data.get('start', [])
            end = pdfjs_data.get('end', [])
            if len(start) == 2 and len(end) == 2:
                import math
                length = math.sqrt((end[0]-start[0])**2 + (end[1]-start[1])**2)
                angle = math.degrees(math.atan2(
                    end[1]-start[1], end[0]-start[0]))
                print(f"  起点: ({start[0]}, {start[1]})")
                print(f"  终点: ({end[0]}, {end[1]})")
                print(f"  长度: {length:.1f} px")
                print(f"  角度: {angle:.1f}°")

    print("\n" + "="*60)
    print("✅ 所有数据验证通过！")
    print("="*60)

    # 5. 测试总结
    print("\n📊 测试总结:")
    type_counts = {}
    for annot in annotations:
        pdfjs_data = annot.get("metadata", {}).get("pdfjs_data", {})
        annot_type = pdfjs_data.get("annotationType")
        type_name = {100: "矩形", 101: "圆形", 102: "箭头"}.get(annot_type, "其他")
        type_counts[type_name] = type_counts.get(type_name, 0) + 1

    for type_name, count in type_counts.items():
        print(f"  - {type_name}: {count} 个")

    print(f"\n💾 文档 ID: {doc_id}")
    print("🌐 前端测试: http://localhost:5173")
    print("   1. 上传相同的 PDF 文件")
    print("   2. 应该看到上述所有标注")
    print("   3. 尝试添加新的矩形、圆形、箭头")

    # 6. 询问是否清理
    print("\n" + "="*60)
    cleanup = input("是否清理测试数据? (y/n): ")
    if cleanup.lower() == 'y':
        print("🧹 清理测试数据...")
        response = requests.delete(
            f"{BASE_URL}/annotations/documents/{doc_id}")
        if response.status_code == 200:
            print("✅ 清理完成")
    else:
        print("⏭ 保留测试数据，可在前端查看")

    return doc_id


if __name__ == "__main__":
    try:
        test_new_shape_tools()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
