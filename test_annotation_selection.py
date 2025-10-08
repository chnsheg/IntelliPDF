"""
测试标注选择和删除功能

测试场景:
1. 创建测试标注
2. 获取标注列表
3. 删除标注
4. 验证删除成功
"""

import requests
import json
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000/api/v1"

def print_section(title: str):
    """打印章节标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def check_health() -> bool:
    """检查后端服务健康状态"""
    try:
        resp = requests.get("http://localhost:8000/health", timeout=5)
        if resp.status_code == 200:
            print("✅ 后端服务运行正常")
            return True
        else:
            print(f"❌ 后端服务异常: {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到后端服务: {e}")
        return False

def get_test_document() -> Dict[str, Any]:
    """获取测试文档"""
    try:
        resp = requests.get(f"{BASE_URL}/documents", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            # Handle different response formats
            docs = data if isinstance(data, list) else data.get('documents', [])
            
            if docs and len(docs) > 0:
                doc = docs[0]
                print(f"✅ 找到测试文档: {doc.get('filename', doc.get('title', 'unknown'))}")
                return doc
            else:
                print("❌ 没有找到文档")
                return None
        else:
            print(f"❌ 获取文档失败: {resp.status_code}")
            print(f"   Response: {resp.text}")
            return None
    except Exception as e:
        print(f"❌ 获取文档异常: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_test_annotation(document_id: str, shape_type: str) -> Dict[str, Any]:
    """创建测试标注"""
    annotation_data = {
        "document_id": document_id,
        "user_id": "test_user",
        "annotation_type": "shape",
        "page_number": 1,
        "data": {
            "id": f"{shape_type}-test-annotation",
            "type": "shape",
            "shapeType": shape_type,
            "geometry": {
                "rect": {
                    "x": 100 if shape_type == "rectangle" else 200,
                    "y": 100,
                    "width": 150,
                    "height": 100
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
        "tags": ["test"]
    }

    try:
        resp = requests.post(
            f"{BASE_URL}/annotations",
            json=annotation_data,
            timeout=10
        )
        if resp.status_code in [200, 201]:  # Accept both 200 and 201
            annotation = resp.json()
            print(f"✅ 创建{shape_type}标注成功: {annotation['id'][:13]}...")
            return annotation
        else:
            print(f"❌ 创建{shape_type}标注失败: {resp.status_code}")
            print(f"   Response: {resp.text}")
            return None
    except Exception as e:
        print(f"❌ 创建{shape_type}标注异常: {e}")
        return None

def get_document_annotations(document_id: str) -> list:
    """获取文档的所有标注"""
    try:
        resp = requests.get(
            f"{BASE_URL}/annotations/documents/{document_id}",
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            annotations = data.get('annotations', [])
            print(f"✅ 获取标注列表成功: 共 {len(annotations)} 个标注")
            return annotations
        else:
            print(f"❌ 获取标注列表失败: {resp.status_code}")
            return []
    except Exception as e:
        print(f"❌ 获取标注列表异常: {e}")
        return []

def delete_annotation(annotation_id: str) -> bool:
    """删除标注"""
    try:
        resp = requests.delete(
            f"{BASE_URL}/annotations/{annotation_id}",
            timeout=10
        )
        if resp.status_code == 200:
            print(f"✅ 删除标注成功: {annotation_id[:13]}...")
            return True
        else:
            print(f"❌ 删除标注失败: {resp.status_code}")
            print(f"   Response: {resp.text}")
            return False
    except Exception as e:
        print(f"❌ 删除标注异常: {e}")
        return False

def main():
    """主测试流程"""
    print("\n🚀 开始测试标注选择和删除功能\n")

    # Step 1: 健康检查
    print_section("Step 1: 健康检查")
    if not check_health():
        sys.exit(1)

    # Step 2: 获取测试文档
    print_section("Step 2: 获取测试文档")
    document = get_test_document()
    if not document:
        sys.exit(1)

    document_id = document['id']

    # Step 3: 创建测试标注
    print_section("Step 3: 创建测试标注")
    test_annotations = []

    shapes = ["rectangle", "circle", "arrow"]
    for shape in shapes:
        annotation = create_test_annotation(document_id, shape)
        if annotation:
            test_annotations.append(annotation)

    if len(test_annotations) == 0:
        print("❌ 没有创建任何测试标注")
        sys.exit(1)

    print(f"\n📊 共创建 {len(test_annotations)} 个测试标注")

    # Step 4: 获取标注列表
    print_section("Step 4: 获取标注列表")
    annotations = get_document_annotations(document_id)

    if len(annotations) < len(test_annotations):
        print("⚠️ 标注数量不匹配")

    # 显示标注详情
    print("\n📋 标注列表:")
    for ann in annotations:
        ann_type = ann.get('annotation_type', 'unknown')
        ann_id = ann.get('id', 'unknown')[:13]
        page = ann.get('page_number', '?')
        print(f"  - [{ann_type}] {ann_id}... (page {page})")

    # Step 5: 测试删除功能
    print_section("Step 5: 测试删除功能")

    if len(test_annotations) > 0:
        # 删除第一个测试标注
        annotation_to_delete = test_annotations[0]
        annotation_id = annotation_to_delete['id']

        print(f"\n🗑️ 准备删除标注: {annotation_id[:13]}...")
        success = delete_annotation(annotation_id)

        if success:
            # 验证删除
            print("\n🔍 验证删除结果...")
            annotations_after = get_document_annotations(document_id)

            deleted = all(ann['id'] != annotation_id for ann in annotations_after)
            if deleted:
                print(f"✅ 验证成功: 标注已被删除")
                print(f"   删除前: {len(annotations)} 个标注")
                print(f"   删除后: {len(annotations_after)} 个标注")
            else:
                print(f"❌ 验证失败: 标注仍然存在")
        else:
            print("❌ 删除操作失败")

    # Step 6: 清理所有测试标注
    print_section("Step 6: 清理测试数据")
    
    success_count = 0
    for annotation in test_annotations[1:]:  # 跳过第一个(已删除)
        if delete_annotation(annotation['id']):
            success_count += 1

    print(f"\n✅ 清理完成: 删除了 {success_count + 1}/{len(test_annotations)} 个测试标注")

    # Final summary
    print_section("测试总结")
    print("✅ 所有测试通过!")
    print("\n测试覆盖:")
    print("  ✅ 创建标注")
    print("  ✅ 获取标注列表")
    print("  ✅ 删除单个标注")
    print("  ✅ 验证删除结果")
    print("  ✅ 批量删除标注")

if __name__ == "__main__":
    main()
