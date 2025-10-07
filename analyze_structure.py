"""
深度分析 Linux教程.pdf 的章节结构
提取目录、章节、小节信息
"""
from app.services.pdf import PDFParser, PDFExtractor
import sys
import os
import re
from pathlib import Path
from collections import defaultdict

os.chdir("backend")
sys.path.insert(0, ".")


def extract_toc_and_structure():
    """提取目录和文档结构"""
    print("=" * 70)
    print("📖 提取 Linux 教程目录结构")
    print("=" * 70)

    pdf_path = Path("../Linux教程.pdf")
    extractor = PDFExtractor(pdf_path)
    structured_text = extractor.extract_structured_text()

    # 提取前30页（通常包含目录）
    toc_pages = structured_text[:30]
    toc_text = '\n'.join([page['text'] for page in toc_pages])

    print("\n1️⃣ 分析目录结构...")

    # 多种章节模式
    patterns = {
        'chapter_num': re.compile(r'^第\s*([一二三四五六七八九十百\d]+)\s*章\s+([^\n]{3,50})', re.MULTILINE),
        'section_dot': re.compile(r'^(\d+\.?\d*\.?\d*)\s+([^\n]{3,80})$', re.MULTILINE),
        'section_chinese': re.compile(r'^([一二三四五六七八九十]+)[、.]\s*([^\n]{3,60})$', re.MULTILINE),
        'subsection': re.compile(r'^(\d+\.\d+\.\d+)\s+([^\n]{3,80})$', re.MULTILINE),
    }

    all_headings = []

    for pattern_name, pattern in patterns.items():
        matches = pattern.findall(toc_text)
        for match in matches:
            all_headings.append({
                'type': pattern_name,
                'number': match[0],
                'title': match[1].strip()
            })

    # 去重并排序
    seen = set()
    unique_headings = []
    for h in all_headings:
        key = (h['number'], h['title'])
        if key not in seen:
            seen.add(key)
            unique_headings.append(h)

    print(f"   找到 {len(unique_headings)} 个标题")

    # 按类型分组
    by_type = defaultdict(list)
    for h in unique_headings:
        by_type[h['type']].append(h)

    for typ, headings in by_type.items():
        print(f"\n   {typ}: {len(headings)} 个")
        for h in headings[:5]:
            print(f"      {h['number']} - {h['title']}")

    # 2. 分析实际内容页
    print("\n\n2️⃣ 分析实际内容页 (第31-60页)...")
    content_pages = structured_text[30:60]

    for i, page in enumerate(content_pages[:10], 31):
        text = page['text']
        if len(text) > 100:
            print(f"\n   --- 第 {i} 页 ({len(text)} 字符) ---")

            # 查找章节标题
            chapter_match = re.search(
                r'^(第.{1,10}章\s+.{3,50}|^\d+\.?\d*\s+[^\n]{5,60})',
                text,
                re.MULTILINE
            )
            if chapter_match:
                print(f"   📌 标题: {chapter_match.group(0).strip()}")

            # 显示内容预览
            lines = text.split('\n')
            non_empty = [l.strip() for l in lines if l.strip()]
            if non_empty:
                print(f"   内容: {' / '.join(non_empty[:3])}")

    # 3. 查找代码块特征
    print("\n\n3️⃣ 代码块特征分析...")
    sample_pages = structured_text[40:60]
    sample_text = '\n'.join([p['text'] for p in sample_pages])

    code_indicators = {
        'shell命令': r'[\$#]\s*(sudo|apt|cd|ls|mkdir|chmod|cat|echo)\s',
        'C语言': r'(int|void|char|return|printf|include)\s*[\(\{]',
        '配置文件': r'^\s*[A-Za-z_]+\s*=\s*.+$',
        '代码缩进': r'^\s{4,}\w+',
    }

    for indicator, pattern in code_indicators.items():
        matches = re.findall(pattern, sample_text,
                             re.MULTILINE | re.IGNORECASE)
        if matches:
            print(f"   ✅ {indicator}: 找到 {len(matches)} 处")
            if matches[:2]:
                print(f"      示例: {matches[0][:50]}")

    # 4. 章节长度统计
    print("\n\n4️⃣ 估算章节长度...")
    print(f"   总页数: {len(structured_text)}")
    print(
        f"   平均每页字符: {sum(len(p['text']) for p in structured_text) / len(structured_text):.0f}")

    # 假设有10-20个章节
    estimated_chapters = 15
    avg_chapter_pages = len(structured_text) / estimated_chapters
    print(f"   估算章节数: ~{estimated_chapters}")
    print(f"   平均每章页数: ~{avg_chapter_pages:.0f}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    extract_toc_and_structure()
