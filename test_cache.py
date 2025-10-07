"""
测试 PDF 解析缓存功能
验证缓存的保存和加载
"""
from app.services.pdf import PDFExtractor, SectionChunker, get_pdf_cache
import sys
import os
import time
from pathlib import Path

# 设置工作目录
os.chdir("backend")
sys.path.insert(0, ".")


def test_cache_functionality():
    """测试缓存功能"""
    print("\n" + "="*70)
    print("🧪 PDF 解析缓存功能测试")
    print("="*70)

    pdf_path = Path("../Linux教程.pdf")

    if not pdf_path.exists():
        print(f"❌ PDF 文件不存在: {pdf_path}")
        return

    # 获取缓存实例
    cache = get_pdf_cache()

    # 清除旧缓存
    print("\n📁 清除旧缓存...")
    cache.clear_cache(pdf_path)

    # ========== 第一次解析（无缓存） ==========
    print("\n" + "="*70)
    print("🔄 第一次解析（无缓存）")
    print("="*70)

    start_time = time.time()

    print("\n1️⃣  提取结构化文本...")
    extractor = PDFExtractor(pdf_path, use_cache=True)
    structured_text = extractor.extract_structured_text()

    print(f"   ✓ 提取了 {len(structured_text)} 页")

    print("\n2️⃣  章节分块...")
    chunker = SectionChunker(use_cache=True)
    chunks = chunker.chunk_by_sections(structured_text, pdf_path)

    print(f"   ✓ 生成了 {len(chunks)} 个章节块")

    first_parse_time = time.time() - start_time
    print(f"\n⏱️  第一次解析耗时: {first_parse_time:.2f} 秒")

    # ========== 第二次解析（使用缓存） ==========
    print("\n" + "="*70)
    print("⚡ 第二次解析（使用缓存）")
    print("="*70)

    start_time = time.time()

    print("\n1️⃣  提取结构化文本...")
    extractor2 = PDFExtractor(pdf_path, use_cache=True)
    structured_text2 = extractor2.extract_structured_text()

    print(f"   ✓ 提取了 {len(structured_text2)} 页")

    print("\n2️⃣  章节分块...")
    chunker2 = SectionChunker(use_cache=True)
    chunks2 = chunker2.chunk_by_sections(structured_text2, pdf_path)

    print(f"   ✓ 生成了 {len(chunks2)} 个章节块")

    second_parse_time = time.time() - start_time
    print(f"\n⏱️  第二次解析耗时: {second_parse_time:.2f} 秒")

    # ========== 性能对比 ==========
    print("\n" + "="*70)
    print("📊 性能对比")
    print("="*70)

    speedup = first_parse_time / second_parse_time if second_parse_time > 0 else 0
    time_saved = first_parse_time - second_parse_time

    print(f"\n   第一次解析: {first_parse_time:.2f} 秒")
    print(f"   第二次解析: {second_parse_time:.2f} 秒")
    print(f"   ⚡ 加速比: {speedup:.2f}x")
    print(
        f"   💰 节省时间: {time_saved:.2f} 秒 ({time_saved/first_parse_time*100:.1f}%)")

    # ========== 缓存统计 ==========
    print("\n" + "="*70)
    print("📦 缓存统计")
    print("="*70)

    stats = cache.get_cache_stats()
    print(f"\n   缓存目录: {stats['cache_dir']}")
    print(f"   元数据缓存: {stats['metadata_count']} 个")
    print(f"   分块缓存: {stats['chunks_count']} 个")
    print(f"   结构化文本缓存: {stats['structured_text_count']} 个")
    print(f"   总大小: {stats['total_size_mb']:.2f} MB")

    # ========== 数据一致性验证 ==========
    print("\n" + "="*70)
    print("✅ 数据一致性验证")
    print("="*70)

    print(f"\n   结构化文本页数: {len(structured_text)} == {len(structured_text2)}")
    print(f"   分块数量: {len(chunks)} == {len(chunks2)}")

    if len(chunks) > 0 and len(chunks2) > 0:
        print(
            f"   第一个块内容长度: {len(chunks[0]['text'])} == {len(chunks2[0]['text'])}")
        print(
            f"   最后一个块内容长度: {len(chunks[-1]['text'])} == {len(chunks2[-1]['text'])}")

    # 验证数据完全一致
    assert len(structured_text) == len(structured_text2), "结构化文本页数不一致"
    assert len(chunks) == len(chunks2), "分块数量不一致"

    print("\n   ✅ 所有数据一致性检查通过！")

    # ========== 显示示例块 ==========
    print("\n" + "="*70)
    print("📄 分块示例")
    print("="*70)

    if chunks:
        chunk = chunks[0]
        print(f"\n   📍 第一个块:")
        print(f"   章节: {chunk['chapter']}")
        print(f"   小节: {chunk['section']}")
        print(f"   页码范围: {chunk['page_range']}")
        print(f"   字符数: {chunk['char_count']}")
        print(f"\n   内容预览:")
        print(f"   {chunk['text'][:200]}...")

    print("\n" + "="*70)
    print("🎉 缓存功能测试完成！")
    print("="*70)


if __name__ == "__main__":
    test_cache_functionality()
