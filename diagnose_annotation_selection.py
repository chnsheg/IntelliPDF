#!/usr/bin/env python3
"""
标注选择问题诊断工具
"""
import requests
import json

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def diagnose():
    print("=" * 60)
    print("标注选择问题诊断")
    print("=" * 60)
    
    # 1. 检查后端
    print("\n1. 检查后端连接...")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        if resp.status_code == 200:
            print("✅ 后端正常运行")
        else:
            print(f"❌ 后端响应异常: {resp.status_code}")
            return
    except Exception as e:
        print(f"❌ 无法连接后端: {e}")
        return
    
    # 2. 获取文档
    print("\n2. 获取文档...")
    resp = requests.get(f"{API_BASE}/documents")
    data = resp.json()
    docs = data.get('documents', [])
    
    if not docs:
        print("❌ 没有文档")
        return
    
    doc_id = docs[0]['id']
    print(f"✅ 文档ID: {doc_id}")
    
    # 3. 获取标注
    print("\n3. 检查标注数据...")
    try:
        # 使用正确的端点
        resp = requests.get(f"{API_BASE}/annotations", params={"document_id": doc_id})
        
        if resp.status_code == 200:
            annotations = resp.json()
            print(f"✅ 找到 {len(annotations)} 个标注")
            
            if len(annotations) == 0:
                print("\n⚠️  问题：没有标注！")
                print("   原因：可能标注创建后未保存到后端")
                print("   解决：在前端创建标注后检查网络请求")
                return
            
            # 分析标注结构
            print("\n4. 分析标注结构...")
            for i, ann in enumerate(annotations[:5]):  # 只看前5个
                print(f"\n标注 {i+1}:")
                print(f"  ID: {ann.get('id', 'N/A')}")
                print(f"  类型: {ann.get('annotation_type', ann.get('type', 'N/A'))}")
                print(f"  页码: {ann.get('page_number', 'N/A')}")
                
                # 检查 data 字段
                data_field = ann.get('data')
                if isinstance(data_field, str):
                    try:
                        data_field = json.loads(data_field)
                    except:
                        pass
                
                if data_field:
                    print(f"  Data 类型: {type(data_field).__name__}")
                    if isinstance(data_field, dict):
                        print(f"  Data 键: {list(data_field.keys())}")
                        
                        # 检查 geometry
                        geometry = data_field.get('geometry')
                        if geometry:
                            print(f"  ✅ 有 geometry: {geometry}")
                        else:
                            print(f"  ❌ 缺少 geometry（便笺类型正常）")
                        
                        # 检查 position (便笺)
                        position = data_field.get('position')
                        if position:
                            print(f"  ✅ 有 position: {position}")
                else:
                    print(f"  ❌ 缺少 data 字段")
            
            # 给出诊断结果
            print("\n" + "=" * 60)
            print("诊断结果")
            print("=" * 60)
            
            shape_count = sum(1 for a in annotations if a.get('annotation_type') == 'shape')
            note_count = sum(1 for a in annotations if a.get('annotation_type') == 'note')
            
            print(f"\n图形标注: {shape_count} 个")
            print(f"便笺标注: {note_count} 个")
            
            if shape_count > 0:
                print("\n✅ 有图形标注，应该可以选中和拖拽")
                print("\n前端检查项：")
                print("1. 打开浏览器控制台 (F12)")
                print("2. 点击标注")
                print("3. 查看是否输出:")
                print("   - 'DraggableAnnotation: mouseDown event'")
                print("   - 'annotationsCount: N' (N > 0)")
                print("   - 'hasGeometry: N' (N > 0)")
                print("4. 如果 hasGeometry = 0:")
                print("   - 检查 transformBackendAnnotation 函数")
                print("   - 确认 geometry 字段正确转换")
                print("5. 如果看到 'Annotation selected: null':")
                print("   - 检查碰撞检测逻辑")
                print("   - 验证坐标转换是否正确")
            
            if note_count > 0:
                print("\n✅ 有便笺标注")
                print("注意：便笺不应该被 DraggableAnnotation 处理")
                print("      它们应该在 AnnotationCanvas 中渲染")
            
        else:
            print(f"❌ 获取标注失败: {resp.status_code}")
            print(f"   URL: {resp.url}")
    
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    print("\n" + "=" * 60)
    print("下一步操作")
    print("=" * 60)
    print("\n1. 如果后端有标注但前端看不到：")
    print("   → 检查 PDFViewerEnhanced 是否正确加载标注")
    print("   → 检查 AnnotationCanvas 是否正确渲染")
    print("\n2. 如果前端创建但后端没有：")
    print("   → 检查网络请求是否成功 (Network 标签页)")
    print("   → 检查 handleShapeComplete 是否调用了保存")
    print("\n3. 如果标注显示但无法选中：")
    print("   → 运行前端并查看控制台调试输出")
    print("   → 参考 FRONTEND_TESTING_GUIDE.md")
    print("\n详细测试指南: FRONTEND_TESTING_GUIDE.md")

if __name__ == "__main__":
    diagnose()
