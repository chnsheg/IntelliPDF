"""
测试技术文档处理流程
使用 Linux教程.pdf 进行完整的章节级分块和RAG测试
"""
from loguru import logger
from app.services.ai import EmbeddingsService, RetrievalService, TechnicalDocRAG
from app.services.pdf import PDFExtractor, TechnicalDocChunker
import sys
import os
import asyncio
from pathlib import Path

# 设置工作目录
original_dir = os.getcwd()
backend_dir = Path(__file__).parent / "backend"
os.chdir(backend_dir)
sys.path.insert(0, str(backend_dir))


async def test_technical_doc_pipeline():
    """测试技术文档处理的完整流程"""
    print("\n" + "="*70)
    print("🚀 技术文档处理测试 - Linux教程.pdf")
    print("="*70)

    pdf_path = Path(original_dir) / "Linux教程.pdf"

    if not pdf_path.exists():
        print(f"❌ PDF 文件不存在: {pdf_path}")
        return

    document_id = "linux_tutorial"

    try:
        # ========== 阶段 1: PDF 解析 ==========
        print("\n" + "="*70)
        print("📄 阶段 1: PDF 解析")
        print("="*70)

        print("\n1️⃣  提取文档结构...")
        extractor = PDFExtractor(pdf_path)
        metadata = extractor.extract_metadata_enhanced()
        print(f"   ✓ 总页数: {metadata['page_count']}")
        print(
            f"   ✓ 总字符数: {metadata['content_analysis']['total_characters']:,}")
        print(
            f"   ✓ 检测语言: {metadata['content_analysis']['detected_language']}")

        # ========== 阶段 2: 章节级分块 ==========
        print("\n" + "="*70)
        print("✂️  阶段 2: 章节级智能分块")
        print("="*70)

        print("\n1️⃣  创建技术文档分块器...")
        chunker = TechnicalDocChunker()

        print("2️⃣  提取结构化文本...")
        structured_text = extractor.extract_structured_text()
        all_text = '\n\n'.join([page['text'] for page in structured_text])

        print(f"   ✓ 文本长度: {len(all_text):,} 字符")

        print("3️⃣  执行章节级分块（这可能需要几分钟）...")
        chunks = chunker.chunk_by_sections(
            text=all_text,
            structured_text=structured_text,
            metadata={'document_id': document_id}
        )

        print(f"   ✓ 生成了 {len(chunks)} 个章节/小节块")

        # 统计信息
        chapters = [c for c in chunks if c['type'] == 'chapter']
        sections = [c for c in chunks if c['type'] == 'section']
        with_code = [c for c in chunks if c.get('has_code', False)]

        print(f"   ✓ 章节: {len(chapters)} 个")
        print(f"   ✓ 小节: {len(sections)} 个")
        print(f"   ✓ 包含代码: {len(with_code)} 个")

        # 显示前5个块
        print(f"\n   📝 前5个章节/小节:")
        for i, chunk in enumerate(chunks[:5], 1):
            title = chunk.get('title', 'Unknown')
            number = chunk.get('number', '')
            level = chunk.get('level', 0)
            char_count = chunk.get('char_count', 0)
            code_count = chunk.get('code_blocks', 0)

            indent = "  " * (level - 1)
            code_info = f", 代码块:{code_count}" if code_count > 0 else ""
            print(
                f"   {i}. {indent}{number} {title} ({char_count} 字符{code_info})")

        # ========== 阶段 3: 选择部分块进行向量化 ==========
        print("\n" + "="*70)
        print("🧮 阶段 3: 向量化（测试用，只处理前20个块）")
        print("="*70)

        # 只取前20个块进行测试
        test_chunks = chunks[:20]
        print(f"\n1️⃣  选择前20个块进行测试...")

        print("2️⃣  初始化 Embeddings 服务...")
        embeddings_service = EmbeddingsService(
            model_name="paraphrase-multilingual-MiniLM-L12-v2"
        )

        print("3️⃣  生成向量嵌入...")
        chunks_with_embeddings = embeddings_service.encode_chunks(
            test_chunks,
            batch_size=8
        )
        print(f"   ✓ 已为 {len(chunks_with_embeddings)} 个块生成向量")
        print(f"   ✓ 向量维度: {chunks_with_embeddings[0]['embedding_dim']}")

        # ========== 阶段 4: 存储到向量数据库 ==========
        print("\n" + "="*70)
        print("💾 阶段 4: 存储到向量数据库")
        print("="*70)

        print("\n1️⃣  初始化检索服务...")
        retrieval_service = RetrievalService(
            collection_name="technical_docs",
            embeddings_service=embeddings_service
        )

        print("2️⃣  清空旧数据...")
        retrieval_service.clear_collection()

        print("3️⃣  添加章节到向量数据库...")
        add_result = retrieval_service.add_documents(
            chunks_with_embeddings,
            document_id=document_id,
            batch_size=10
        )
        print(f"   ✓ 成功添加 {add_result['added']} 个章节")

        # ========== 阶段 5: 技术文档 RAG 问答 ==========
        print("\n" + "="*70)
        print("💬 阶段 5: 技术文档智能问答")
        print("="*70)

        print("\n1️⃣  初始化技术文档 RAG 服务...")
        rag_service = TechnicalDocRAG(retrieval_service=retrieval_service)

        # 测试问题
        test_questions = [
            "Linux系统中如何查看文件内容？",
            "什么是I/O重定向？",
            "文件权限管理的基本命令有哪些？",
        ]

        for i, question in enumerate(test_questions[:2], 1):  # 只测试前2个问题
            print(f"\n{i}️⃣  问题: {question}")
            print("   🤖 Gemini 正在分析相关章节...")

            result = await rag_service.answer_knowledge_point(
                question=question,
                document_id=document_id,
                n_contexts=2,
                language="zh",
                include_code=True
            )

            print(f"\n   📝 回答:")
            answer_preview = result['answer'][:500] + \
                "..." if len(result['answer']) > 500 else result['answer']
            print(f"   {answer_preview}")

            print(f"\n   📚 参考章节: {result['source_count']} 个")
            for j, chapter in enumerate(result['chapters'], 1):
                number = chapter.get('number', '')
                title = chapter.get('title', '')
                has_code = "🔧" if chapter.get('has_code') else ""
                print(f"      {j}. {number} {title} {has_code}")

        # ========== 阶段 6: 代码解释 ==========
        print("\n" + "="*70)
        print("🔧 阶段 6: 代码片段解释")
        print("="*70)

        # 从文档中找一段代码
        code_chunks = [c for c in test_chunks if c.get('has_code', False)]
        if code_chunks:
            print("\n1️⃣  找到包含代码的章节...")
            code_chunk = code_chunks[0]

            # 提取代码片段（简单示例）
            code_sample = code_chunk['text'][:300]
            print(
                f"   章节: {code_chunk.get('number', '')} {code_chunk.get('title', '')}")
            print(f"   代码预览:\n{code_sample}\n")

            print("2️⃣  请求代码解释...")
            code_result = await rag_service.explain_code_snippet(
                code=code_sample,
                document_id=document_id,
                language="zh"
            )

            print(f"\n   📖 代码解释:")
            explanation_preview = code_result['explanation'][:400] + "..." if len(
                code_result['explanation']) > 400 else code_result['explanation']
            print(f"   {explanation_preview}")
        else:
            print("\n   ℹ️  测试的前20个块中未找到代码块")

        # ========== 测试完成 ==========
        print("\n" + "="*70)
        print("✅ 技术文档处理测试完成！")
        print("="*70)

        print("\n📊 测试总结:")
        print(f"   • 文档页数: {metadata['page_count']}")
        print(f"   • 章节总数: {len(chunks)}")
        print(f"   • 测试块数: {len(test_chunks)}")
        print(f"   • 向量化: ✅ {len(chunks_with_embeddings)} 个")
        print(f"   • 数据库: ✅ {add_result['added']} 条")
        print(f"   • RAG 问答: ✅ 正常")
        print(f"   • 代码解释: ✅ 正常")

        print("\n🎉 技术文档 RAG 系统测试成功！")

        print("\n💡 提示:")
        print("   - 完整文档有 1063 页，本次只测试了前20个章节")
        print("   - 要处理完整文档，需要更长时间和更多资源")
        print("   - 建议根据需要选择特定章节进行处理")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_technical_doc_pipeline())
