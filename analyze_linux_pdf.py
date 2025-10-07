"""
分析 Linux教程.pdf 的结构
识别章节、代码块等元素
"""
from app.services.pdf import PDFParser, PDFExtractor
import sys
import os
import re
from pathlib import Path

os.chdir("backend")
sys.path.insert(0, ".")


def analyze_linux_tutorial():
    """分析 Linux 教程的文档结构"""
    print("=" * 70)
    print("📚 Linux 教程 PDF 结构分析")
    print("=" * 70)

    pdf_path = Path("../Linux教程.pdf")

    if not pdf_path.exists():
        print(f"❌ 文件不存在: {pdf_path}")
        return

    # 1. 基本信息
    print("\n1️⃣ 基本信息:")
    parser = PDFParser(pdf_path)
    metadata = parser.get_metadata()
    print(f"   页数: {metadata['page_count']}")
    print(f"   作者: {metadata.get('author', 'N/A')}")
    print(f"   标题: {metadata.get('title', 'N/A')}")

    # 2. 提取文本
    print("\n2️⃣ 提取文本内容...")
    extractor = PDFExtractor(pdf_path)
    structured_text = extractor.extract_structured_text()

    total_chars = sum(len(page['text']) for page in structured_text)
    print(f"   总字符数: {total_chars:,}")
    print(f"   有效页数: {len(structured_text)}")

    # 3. 分析章节结构
    print("\n3️⃣ 章节结构分析:")
    chapter_pattern = re.compile(
        r'^(第[一二三四五六七八九十\d]+章|Chapter\s+\d+|[0-9]+\.?\s*[^\n]{1,50})\s*$',
        re.MULTILINE | re.IGNORECASE
    )
    section_pattern = re.compile(
        r'^([0-9]+\.[0-9]+\.?\s+[^\n]{1,80}|[一二三四五六七八九十]+[、\.]\s*[^\n]{1,80})\s*$',
        re.MULTILINE
    )

    all_text = '\n\n'.join([page['text'] for page in structured_text[:10]])

    chapters = chapter_pattern.findall(all_text)
    sections = section_pattern.findall(all_text[:5000])

    print(f"   检测到章节标题: {len(chapters)} 个")
    if chapters:
        print(f"   前3个章节:")
        for i, ch in enumerate(chapters[:3], 1):
            print(f"      {i}. {ch.strip()}")

    print(f"\n   检测到小节标题: {len(sections)} 个")
    if sections:
        print(f"   前5个小节:")
        for i, sec in enumerate(sections[:5], 1):
            print(f"      {i}. {sec.strip()}")

    # 4. 分析代码块
    print("\n4️⃣ 代码块分析:")
    code_patterns = [
        r'```[\s\S]*?```',  # Markdown 代码块
        r'`[^`]+`',  # 行内代码
        r'^\s*[$#]\s+\w+',  # Shell 命令
        r'^\s{4,}\w+',  # 缩进代码
    ]

    sample_text = '\n'.join([page['text'] for page in structured_text[:5]])

    for i, pattern in enumerate(code_patterns, 1):
        matches = re.findall(pattern, sample_text, re.MULTILINE)
        print(f"   模式 {i}: 找到 {len(matches)} 个匹配")
        if matches and i <= 2:
            print(f"      示例: {matches[0][:60]}...")

    # 5. 显示前几页内容示例
    print("\n5️⃣ 内容示例 (第1-2页):")
    for i, page in enumerate(structured_text[:2], 1):
        print(f"\n   --- 第 {i} 页 ---")
        text_preview = page['text'][:300]
        print(f"   {text_preview}...")
        print(f"   字符数: {len(page['text'])}")

    # 6. 识别文档类型特征
    print("\n6️⃣ 文档特征识别:")
    features = {
        '包含代码': bool(re.search(r'[$#]\s+\w+|```', all_text[:5000])),
        '包含命令': bool(re.search(r'(sudo|apt|yum|cd|ls|mkdir|chmod)', all_text[:5000], re.IGNORECASE)),
        '包含章节编号': bool(re.search(r'^[0-9]+\.[0-9]+', all_text[:5000], re.MULTILINE)),
        '包含中文': bool(re.search(r'[\u4e00-\u9fff]', all_text[:1000])),
        '包含英文': bool(re.search(r'[a-zA-Z]{3,}', all_text[:1000])),
    }

    for feature, exists in features.items():
        status = "✅" if exists else "❌"
        print(f"   {status} {feature}")

    print("\n" + "=" * 70)
    print("✅ 分析完成！")
    print("=" * 70)


if __name__ == "__main__":
    analyze_linux_tutorial()
