#!/usr/bin/env python
"""测试文档上传和处理流程"""
import requests
import time
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1"


def delete_all_documents():
    """删除所有现有文档"""
    print("1. 清理现有文档...")
    r = requests.get(f"{BASE_URL}/documents")
    if r.status_code == 200:
        docs = r.json().get('documents', [])
        print(f"   找到 {len(docs)} 个文档")
        for doc in docs:
            doc_id = doc['id']
            r = requests.delete(f"{BASE_URL}/documents/{doc_id}")
            print(f"   - 删除 {doc['filename']}: {r.status_code}")
    print()


def upload_test_document():
    """上传测试文档"""
    print("2. 上传新文档...")

    # 使用项目中的现有PDF
    pdf_path = Path("D:/IntelliPDF/Linux教程.pdf")

    if not pdf_path.exists():
        print(f"   ✗ 文件不存在: {pdf_path}")
        return None

    with open(pdf_path, 'rb') as f:
        files = {'file': (pdf_path.name, f, 'application/pdf')}
        r = requests.post(f"{BASE_URL}/documents/upload",
                          files=files, timeout=60)

    print(f"   状态码: {r.status_code}")

    if r.status_code == 201:
        doc = r.json()
        print(f"   ✓ 上传成功!")
        print(f"   文档ID: {doc['id']}")
        print(f"   文件名: {doc['filename']}")
        print(f"   处理状态: {doc['status']}")
        print(f"   块数量: {doc.get('chunk_count', 0)}")
        if doc.get('processing_error'):
            print(f"   ⚠ 错误: {doc['processing_error']}")
        print()
        return doc
    else:
        print(f"   ✗ 上传失败: {r.text[:200]}")
        print()
        return None


def check_document(doc_id):
    """检查文档详情"""
    print(f"3. 检查文档详情...")
    r = requests.get(f"{BASE_URL}/documents/{doc_id}")

    if r.status_code == 200:
        doc = r.json()
        print(f"   文档: {doc['filename']}")
        print(f"   状态: {doc['status']}")
        print(f"   块数量: {doc.get('chunk_count', 0)}")

        if doc['status'] == 'completed':
            print("   ✓ 文档处理成功！")
        elif doc['status'] == 'failed':
            print(f"   ✗ 处理失败: {doc.get('processing_error', 'Unknown')}")
        else:
            print(f"   ⏳ 处理中...")
        print()
        return doc
    else:
        print(f"   ✗ 获取失败: {r.text[:200]}")
        print()
        return None


def check_chunks(doc_id):
    """检查文档块"""
    print(f"4. 检查文档块...")
    r = requests.get(f"{BASE_URL}/documents/{doc_id}/chunks")

    if r.status_code == 200:
        data = r.json()
        chunk_count = data.get('total', 0)
        print(f"   块数量: {chunk_count}")

        if chunk_count > 0:
            print("   ✓ 块生成成功！")
            chunks = data.get('chunks', [])
            if chunks:
                print(f"   第一个块预览: {chunks[0]['content'][:100]}...")
        else:
            print("   ⚠ 没有生成块")
        print()
    else:
        print(f"   ✗ 获取失败: {r.text[:200]}")
        print()


def main():
    print("="*60)
    print("文档处理流程完整测试")
    print("="*60)
    print()

    # 步骤1: 清理
    delete_all_documents()

    # 步骤2: 上传
    doc = upload_test_document()

    if doc:
        doc_id = doc['id']

        # 步骤3: 检查
        time.sleep(2)  # 等待处理
        check_document(doc_id)

        # 步骤4: 检查块
        check_chunks(doc_id)

        print("="*60)
        print("测试完成！")
        print("="*60)

        # 最终结果
        doc_final = check_document(doc_id)
        if doc_final and doc_final['status'] == 'completed':
            print("\n✓✓✓ 所有修复验证成功！文档处理流程正常工作！")
        elif doc_final and doc_final['status'] == 'failed':
            print(
                f"\n✗✗✗ 文档处理仍然失败: {doc_final.get('processing_error', 'Unknown')}")
        else:
            print("\n⏳⏳⏳ 文档仍在处理中...")


if __name__ == "__main__":
    main()
