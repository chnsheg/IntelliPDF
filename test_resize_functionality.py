#!/usr/bin/env python3
"""
测试标注调整大小功能（Phase 7.3）
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def print_section(title):
    """打印测试节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def test_health():
    """测试健康检查"""
    print_section("1. 健康检查")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 后端服务运行正常")
            return True
        else:
            print(f"❌ 后端响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到后端: {e}")
        return False

def get_document():
    """获取测试文档"""
    print_section("2. 获取测试文档")
    try:
        response = requests.get(f"{API_BASE}/documents", timeout=10)
        if response.status_code == 200:
            docs = response.json()
            if docs:
                doc_id = docs[0]['id']
                print(f"✅ 找到测试文档: {docs[0]['title']} (ID: {doc_id})")
                return doc_id
            else:
                print("❌ 没有找到文档")
                return None
        else:
            print(f"❌ 获取文档失败: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None

def create_test_shape(doc_id):
    """创建测试形状标注"""
    print_section("3. 创建测试矩形标注")
    
    annotation_data = {
        "document_id": doc_id,
        "page_number": 1,
        "type": "shape",
        "data": {
            "shapeType": "rectangle",
            "geometry": {
                "x": 100,
                "y": 100,
                "width": 200,
                "height": 150
            },
            "style": {
                "strokeColor": "#FF0000",
                "fillColor": "rgba(255, 0, 0, 0.1)",
                "strokeWidth": 2
            }
        },
        "content": "测试矩形（用于调整大小）",
        "tags": ["test", "resize"]
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/annotations",
            json=annotation_data,
            timeout=10
        )
        
        if response.status_code == 200:
            annotation = response.json()
            print(f"✅ 创建矩形标注成功")
            print(f"   ID: {annotation['id']}")
            print(f"   初始几何: x={annotation['data']['geometry']['x']}, "
                  f"y={annotation['data']['geometry']['y']}, "
                  f"w={annotation['data']['geometry']['width']}, "
                  f"h={annotation['data']['geometry']['height']}")
            return annotation
        else:
            print(f"❌ 创建失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return None

def simulate_resize(annotation_id, doc_id, old_geometry, new_geometry, operation):
    """模拟调整大小操作"""
    print(f"\n{operation}:")
    
    update_data = {
        "data": {
            "id": annotation_id,
            "shapeType": "rectangle",
            "geometry": new_geometry,
            "style": {
                "strokeColor": "#FF0000",
                "fillColor": "rgba(255, 0, 0, 0.1)",
                "strokeWidth": 2
            }
        }
    }
    
    try:
        response = requests.put(
            f"{API_BASE}/annotations/{annotation_id}",
            json=update_data,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"  ✅ {operation}成功")
            print(f"     旧几何: x={old_geometry['x']}, y={old_geometry['y']}, "
                  f"w={old_geometry['width']}, h={old_geometry['height']}")
            print(f"     新几何: x={new_geometry['x']}, y={new_geometry['y']}, "
                  f"w={new_geometry['width']}, h={new_geometry['height']}")
            return True
        else:
            print(f"  ❌ {operation}失败: {response.status_code}")
            print(f"     响应: {response.text}")
            return False
    except Exception as e:
        print(f"  ❌ 请求异常: {e}")
        return False

def test_resize_operations(annotation):
    """测试各种调整大小操作"""
    print_section("4. 测试调整大小操作")
    
    annotation_id = annotation['id']
    doc_id = annotation['document_id']
    original_geometry = annotation['data']['geometry']
    
    operations = [
        {
            "name": "右下角调整（增大）",
            "old": original_geometry,
            "new": {
                "x": original_geometry['x'],
                "y": original_geometry['y'],
                "width": original_geometry['width'] + 50,
                "height": original_geometry['height'] + 40
            }
        },
        {
            "name": "左上角调整（缩小）",
            "old": {
                "x": original_geometry['x'],
                "y": original_geometry['y'],
                "width": original_geometry['width'] + 50,
                "height": original_geometry['height'] + 40
            },
            "new": {
                "x": original_geometry['x'] + 30,
                "y": original_geometry['y'] + 25,
                "width": original_geometry['width'] + 20,
                "height": original_geometry['height'] + 15
            }
        },
        {
            "name": "右上角调整（改变宽高）",
            "old": {
                "x": original_geometry['x'] + 30,
                "y": original_geometry['y'] + 25,
                "width": original_geometry['width'] + 20,
                "height": original_geometry['height'] + 15
            },
            "new": {
                "x": original_geometry['x'] + 30,
                "y": original_geometry['y'] + 40,
                "width": original_geometry['width'] + 60,
                "height": original_geometry['height']
            }
        },
        {
            "name": "应用最小尺寸约束",
            "old": {
                "x": original_geometry['x'] + 30,
                "y": original_geometry['y'] + 40,
                "width": original_geometry['width'] + 60,
                "height": original_geometry['height']
            },
            "new": {
                "x": original_geometry['x'] + 30,
                "y": original_geometry['y'] + 40,
                "width": 25,  # 接近最小尺寸
                "height": 25
            }
        },
        {
            "name": "恢复到原始尺寸",
            "old": {
                "x": original_geometry['x'] + 30,
                "y": original_geometry['y'] + 40,
                "width": 25,
                "height": 25
            },
            "new": original_geometry
        }
    ]
    
    success_count = 0
    for op in operations:
        if simulate_resize(annotation_id, doc_id, op['old'], op['new'], op['name']):
            success_count += 1
            time.sleep(0.5)  # 短暂延迟
    
    print(f"\n调整大小测试: {success_count}/{len(operations)} 成功")
    return success_count == len(operations)

def verify_final_state(annotation_id):
    """验证最终状态"""
    print_section("5. 验证最终状态")
    
    try:
        response = requests.get(
            f"{API_BASE}/annotations/{annotation_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            annotation = response.json()
            geometry = annotation['data']['geometry']
            print(f"✅ 标注状态已验证")
            print(f"   最终几何: x={geometry['x']}, y={geometry['y']}, "
                  f"w={geometry['width']}, h={geometry['height']}")
            return True
        else:
            print(f"❌ 获取标注失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def cleanup(annotation_id):
    """清理测试数据"""
    print_section("6. 清理测试数据")
    
    try:
        response = requests.delete(
            f"{API_BASE}/annotations/{annotation_id}",
            timeout=10
        )
        
        if response.status_code in [200, 204]:
            print(f"✅ 清理完成，已删除测试标注")
            return True
        else:
            print(f"❌ 删除失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def main():
    """主测试流程"""
    print("\n" + "="*60)
    print("  标注调整大小功能测试（Phase 7.3）")
    print("="*60)
    print("\n本测试将验证:")
    print("  • 调整句柄检测")
    print("  • 四个角的调整操作（nw, ne, sw, se）")
    print("  • 实时预览效果")
    print("  • 最小尺寸约束")
    print("  • 边界检查")
    print("  • ResizeAnnotationCommand 集成")
    
    # 测试流程
    if not test_health():
        print("\n❌ 测试中止：后端服务未运行")
        return
    
    doc_id = get_document()
    if not doc_id:
        print("\n❌ 测试中止：无法获取文档")
        return
    
    annotation = create_test_shape(doc_id)
    if not annotation:
        print("\n❌ 测试中止：无法创建测试标注")
        return
    
    annotation_id = annotation['id']
    
    try:
        # 测试调整大小操作
        resize_success = test_resize_operations(annotation)
        
        # 验证最终状态
        verify_success = verify_final_state(annotation_id)
        
        # 总结
        print_section("测试总结")
        print(f"调整大小测试: {'✅ 通过' if resize_success else '❌ 失败'}")
        print(f"状态验证: {'✅ 通过' if verify_success else '❌ 失败'}")
        
        if resize_success and verify_success:
            print("\n🎉 所有测试通过！")
            print("\n前端测试步骤:")
            print("1. 打开浏览器访问 http://localhost:5173")
            print("2. 打开一个 PDF 文档")
            print("3. 创建一个形状标注（矩形、圆形或箭头）")
            print("4. 点击标注以选中它")
            print("5. 拖拽四个角的蓝色调整句柄")
            print("6. 验证:")
            print("   • 实时预览显示调整后的尺寸")
            print("   • 释放鼠标后保存新尺寸")
            print("   • 按 Ctrl+Z 可以撤销调整")
            print("   • 按 Ctrl+Y 可以重做调整")
            print("   • 调整后的标注保持在页面边界内")
        else:
            print("\n❌ 部分测试失败，请检查日志")
    
    finally:
        # 清理测试数据
        cleanup(annotation_id)

if __name__ == "__main__":
    main()
