"""
测试 PDF 解析功能
使用项目根目录的 论文.pdf 进行测试
"""
from loguru import logger
from app.services.pdf import PDFParser, PDFExtractor, PDFChunker
import sys
import asyncio
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "backend"))


def test_pdf_parser():
    """测试 PDF 解析器"""
    print("\n" + "="*60)
    print("📄 测试 PDF 解析器")
    print("="*60)

    pdf_path = Path(__file__).parent / "论文.pdf"

    if not pdf_path.exists():
        print(f"❌ PDF 文件不存在: {pdf_path}")
        return

    try:
        # 创建解析器
        parser = PDFParser(pdf_path)

        # 1. 提取元数据
        print("\n1️⃣  提取元数据...")
        metadata = parser.get_metadata()
        print(f"   页数: {metadata['page_count']}")
        print(f"   标题: {metadata.get('title', 'N/A')}")
        print(f"   作者: {metadata.get('author', 'N/A')}")

        # 2. 提取文本（前3页）
        print("\n2️⃣  提取文本（前3页）...")
        text_by_page = parser.extract_text(
            engine="pymupdf", page_numbers=[0, 1, 2])
        for page_num, text in text_by_page.items():
            print(f"   第 {page_num + 1} 页: {len(text)} 字符")
            print(f"   预览: {text[:100]}...")

        # 3. 提取表格
        print("\n3️⃣  提取表格...")
        tables = parser.extract_tables()
        print(f"   找到 {len(tables)} 个页面包含表格")
        for page_num, page_tables in tables.items():
            print(f"   第 {page_num + 1} 页: {len(page_tables)} 个表格")

        # 4. 提取图片信息
        print("\n4️⃣  提取图片...")
        images = parser.extract_images()
        total_images = sum(len(imgs) for imgs in images.values())
        print(f"   找到 {total_images} 张图片")

        print("\n✅ PDF 解析器测试完成！")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_pdf_extractor():
    """测试 PDF 提取器"""
    print("\n" + "="*60)
    print("📝 测试 PDF 提取器")
    print("="*60)

    pdf_path = Path(__file__).parent / "论文.pdf"

    if not pdf_path.exists():
        print(f"❌ PDF 文件不存在: {pdf_path}")
        return

    try:
        # 创建提取器
        extractor = PDFExtractor(pdf_path)

        # 1. 提取结构化文本
        print("\n1️⃣  提取结构化文本...")
        structured_text = extractor.extract_structured_text()
        print(f"   共 {len(structured_text)} 个页面有内容")
        if structured_text:
            first_page = structured_text[0]
            print(f"   第一页字符数: {first_page['char_count']}")
            print(f"   第一页单词数: {first_page['word_count']}")
            print(f"   首行: {first_page.get('first_line', 'N/A')[:50]}...")

        # 2. 提取章节
        print("\n2️⃣  提取文档章节...")
        sections = extractor.extract_sections()
        print(f"   找到 {len(sections)} 个章节")
        for i, section in enumerate(sections[:5]):  # 只显示前5个
            print(
                f"   {i+1}. {section['title'][:40]}... (第 {section['start_page']} 页)")

        # 3. 提取增强元数据
        print("\n3️⃣  提取增强元数据...")
        enhanced_meta = extractor.extract_metadata_enhanced()
        content_analysis = enhanced_meta['content_analysis']
        print(f"   总字符数: {content_analysis['total_characters']}")
        print(f"   中文字符: {content_analysis['chinese_characters']}")
        print(f"   英文字符: {content_analysis['english_characters']}")
        print(f"   检测语言: {content_analysis['detected_language']}")
        print(f"   语言置信度: {content_analysis['language_confidence']:.2%}")

        print("\n✅ PDF 提取器测试完成！")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_pdf_chunker():
    """测试 PDF 分块器"""
    print("\n" + "="*60)
    print("✂️  测试 PDF 分块器")
    print("="*60)

    pdf_path = Path(__file__).parent / "论文.pdf"

    if not pdf_path.exists():
        print(f"❌ PDF 文件不存在: {pdf_path}")
        return

    try:
        # 创建提取器获取文本
        extractor = PDFExtractor(pdf_path)
        structured_text = extractor.extract_structured_text()

        if not structured_text:
            print("❌ 没有找到文本内容")
            return

        # 合并所有页面文本
        all_text = '\n\n'.join([page['text'] for page in structured_text])

        # 创建分块器
        chunker = PDFChunker(chunk_size=1000, chunk_overlap=200)

        # 1. 固定大小分块
        print("\n1️⃣  固定大小分块...")
        fixed_chunks = chunker.chunk_by_fixed_size(all_text)
        print(f"   生成 {len(fixed_chunks)} 个块")
        if fixed_chunks:
            print(f"   第一块: {fixed_chunks[0]['char_count']} 字符")
            print(f"   预览: {fixed_chunks[0]['text'][:100]}...")

        # 2. 段落分块
        print("\n2️⃣  段落分块...")
        para_chunks = chunker.chunk_by_paragraph(all_text)
        print(f"   生成 {len(para_chunks)} 个块")
        if para_chunks:
            print(
                f"   平均块大小: {sum(c['char_count'] for c in para_chunks) / len(para_chunks):.0f} 字符")

        # 3. 页面分块
        print("\n3️⃣  页面分块...")
        page_chunks = chunker.chunk_by_page(structured_text)
        print(f"   生成 {len(page_chunks)} 个块")
        if page_chunks:
            print(f"   第一块页码: {page_chunks[0]['page_numbers']}")

        # 4. 智能混合分块
        print("\n4️⃣  智能混合分块...")
        smart_chunks = chunker.chunk_smart(all_text, strategy="hybrid")
        print(f"   生成 {len(smart_chunks)} 个块")

        print("\n✅ PDF 分块器测试完成！")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_comprehensive():
    """综合测试"""
    print("\n" + "="*60)
    print("🚀 综合测试：完整提取流程")
    print("="*60)

    pdf_path = Path(__file__).parent / "论文.pdf"

    if not pdf_path.exists():
        print(f"❌ PDF 文件不存在: {pdf_path}")
        return

    try:
        # 创建提取器
        extractor = PDFExtractor(pdf_path)

        # 执行完整提取
        print("\n📊 执行完整提取...")
        result = extractor.extract_all()

        # 显示摘要
        summary = result['summary']
        print(f"\n📈 提取摘要:")
        print(f"   总页数: {summary['total_pages']}")
        print(f"   有文本的页面: {summary['pages_with_text']}")
        print(f"   章节数: {summary['total_sections']}")
        print(f"   表格数: {summary['total_tables']}")
        print(f"   总字符数: {summary['total_characters']}")
        print(f"   检测语言: {summary['detected_language']}")

        # 显示部分章节
        if result['sections']:
            print(f"\n📑 文档章节（前5个）:")
            for i, section in enumerate(result['sections'][:5]):
                print(f"   {i+1}. {section['title'][:50]}...")

        # 执行分块
        print(f"\n✂️  对文档进行分块...")
        chunker = PDFChunker(chunk_size=1000, chunk_overlap=200)
        all_text = '\n\n'.join([page['text']
                               for page in result['structured_text']])
        chunks = chunker.chunk_smart(all_text, strategy="hybrid")
        print(f"   生成 {len(chunks)} 个文档块")

        print("\n✅ 综合测试完成！PDF 解析流程工作正常。")

    except Exception as e:
        print(f"\n❌ 综合测试失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("🧪 IntelliPDF - PDF 处理模块测试")
    print("="*60)

    test_pdf_parser()
    test_pdf_extractor()
    test_pdf_chunker()
    test_comprehensive()

    print("\n" + "="*60)
    print("🎉 所有测试完成！")
    print("="*60)


if __name__ == "__main__":
    main()
