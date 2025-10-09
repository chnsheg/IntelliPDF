"""
PDF.js 原生标注系统 - 后端 API 测试

测试批量创建和删除标注的后端接口
"""

import requests
import json
from datetime import datetime
import uuid

BASE_URL = "http://localhost:8000/api/v1"

# 测试用的 token（需要先登录获取）
# 如果没有 token，先运行 test_api_complete.py 获取
TOKEN = None


def get_auth_headers():
    """获取认证头"""
    if TOKEN:
        return {"Authorization": f"Bearer {TOKEN}"}
    return {}


def test_batch_create_annotations():
    """测试批量创建标注"""
    print("\n=== 测试批量创建标注 ===")
    
    # 准备测试数据
    test_doc_id = str(uuid.uuid4())
    test_user_id = str(uuid.uuid4())
    
    annotations_data = [
        {
            "document_id": test_doc_id,
            "user_id": test_user_id,
            "annotation_type": "pdfjs",
            "page_number": 1,
            "data": {
                "pdfjs_data": {
                    "annotationType": 15,  # INK
                    "pageIndex": 0,
                    "paths": [
                        [
                            {"x": 100, "y": 200},
                            {"x": 150, "y": 250},
                            {"x": 200, "y": 200}
                        ]
                    ],
                    "color": [1, 0, 0],
                    "thickness": 2
                }
            }
        },
        {
            "document_id": test_doc_id,
            "user_id": test_user_id,
            "annotation_type": "pdfjs",
            "page_number": 1,
            "data": {
                "pdfjs_data": {
                    "annotationType": 3,  # FREETEXT
                    "pageIndex": 0,
                    "rect": [100, 100, 300, 130],
                    "contents": "测试文本标注",
                    "color": [0, 0, 1]
                }
            }
        },
        {
            "document_id": test_doc_id,
            "user_id": test_user_id,
            "annotation_type": "pdfjs",
            "page_number": 2,
            "data": {
                "pdfjs_data": {
                    "annotationType": 15,  # INK
                    "pageIndex": 1,
                    "paths": [
                        [
                            {"x": 50, "y": 50},
                            {"x": 100, "y": 100}
                        ]
                    ],
                    "color": [0, 1, 0],
                    "thickness": 3
                }
            }
        }
    ]
    
    try:
        # 发送批量创建请求
        response = requests.post(
            f"{BASE_URL}/annotations/batch",
            json={"annotations": annotations_data},
            headers=get_auth_headers(),
            timeout=10
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 成功创建 {result.get('created', 0)} 条标注")
            return test_doc_id
        else:
            print(f"❌ 创建失败: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return None


def test_get_annotations_by_document(document_id: str):
    """测试获取文档的所有标注"""
    print(f"\n=== 测试获取文档标注 (document_id={document_id}) ===")
    
    try:
        response = requests.get(
            f"{BASE_URL}/annotations/documents/{document_id}/annotations",
            headers=get_auth_headers(),
            timeout=10
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            annotations = response.json()
            print(f"✅ 找到 {len(annotations)} 条标注")
            for i, ann in enumerate(annotations, 1):
                print(f"  [{i}] 类型={ann.get('annotation_type')}, 页码={ann.get('page_number')}")
            return len(annotations)
        else:
            print(f"❌ 获取失败: {response.text}")
            return 0
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return 0


def test_delete_annotations_by_document(document_id: str):
    """测试删除文档的所有标注"""
    print(f"\n=== 测试删除文档标注 (document_id={document_id}) ===")
    
    try:
        response = requests.delete(
            f"{BASE_URL}/annotations/documents/{document_id}",
            headers=get_auth_headers(),
            timeout=10
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 204:
            print(f"✅ 成功删除文档的所有标注")
            return True
        else:
            print(f"❌ 删除失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False


def test_endpoint_validation():
    """测试端点验证（无效数据）"""
    print("\n=== 测试端点验证 ===")
    
    # 测试1: 空数组
    try:
        response = requests.post(
            f"{BASE_URL}/annotations/batch",
            json={"annotations": []},
            headers=get_auth_headers(),
            timeout=10
        )
        print(f"空数组测试 - 状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"  结果: {response.json()}")
    except Exception as e:
        print(f"  异常: {e}")
    
    # 测试2: 缺少必需字段
    try:
        response = requests.post(
            f"{BASE_URL}/annotations/batch",
            json={"annotations": [{"page_number": 1}]},
            headers=get_auth_headers(),
            timeout=10
        )
        print(f"缺少字段测试 - 状态码: {response.status_code}")
        if response.status_code != 200:
            print(f"  错误: {response.text}")
    except Exception as e:
        print(f"  异常: {e}")
    
    # 测试3: 无效的 document_id
    try:
        response = requests.delete(
            f"{BASE_URL}/annotations/documents/invalid-uuid",
            headers=get_auth_headers(),
            timeout=10
        )
        print(f"无效 UUID 测试 - 状态码: {response.status_code}")
    except Exception as e:
        print(f"  异常: {e}")


def main():
    """主测试流程"""
    print("PDF.js 原生标注系统 - 后端 API 测试")
    print("=" * 60)
    
    # 测试1: 批量创建
    test_doc_id = test_batch_create_annotations()
    
    if test_doc_id:
        # 测试2: 获取标注
        count = test_get_annotations_by_document(test_doc_id)
        
        # 测试3: 删除标注
        if count > 0:
            test_delete_annotations_by_document(test_doc_id)
            
            # 验证删除
            count_after = test_get_annotations_by_document(test_doc_id)
            if count_after == 0:
                print("\n✅ 删除验证成功：标注已全部删除")
            else:
                print(f"\n⚠️  删除验证失败：仍有 {count_after} 条标注")
    
    # 测试4: 端点验证
    test_endpoint_validation()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    
    print("\n提示:")
    print("  - 如果遇到 401 错误，请先运行 test_api_complete.py 获取 token")
    print("  - 如果遇到 422 错误，检查请求数据格式是否正确")
    print("  - 查看 backend 日志了解详细错误信息")


if __name__ == "__main__":
    main()
