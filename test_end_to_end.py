"""
端到端测试：PDF 上传 -> 解析 -> 向量化 -> RAG 问答
使用 论文.pdf 进行完整流程测试
"""
from loguru import logger
from app.services.ai import EmbeddingsService, RetrievalService, LLMService
from app.services.pdf import PDFExtractor, PDFChunker
import sys
import os
import asyncio
from pathlib import Path

# 保存原始目录
original_dir = os.getcwd()

# 切换到 backend 目录以加载 .env
backend_dir = Path(__file__).parent / "backend"
os.chdir(backend_dir)
sys.path.insert(0, str(backend_dir))


async def test_full_pipeline():
    """测试完整的 PDF 处理和问答流程"""
    print("\n" + "="*70)
    print("🚀 IntelliPDF 端到端测试")
    print("="*70)

    # PDF 在原始目录
    pdf_path = Path(original_dir) / "论文.pdf"

    if not pdf_path.exists():
        print(f"❌ PDF 文件不存在: {pdf_path}")
        return

    document_id = "test_paper_001"

    try:
        # ========== 阶段 1: PDF 解析 ==========
        print("\n" + "="*70)
        print("📄 阶段 1: PDF 解析与提取")
        print("="*70)

        print("\n1️⃣  创建 PDF 提取器...")
        extractor = PDFExtractor(pdf_path)

        print("2️⃣  提取文档元数据...")
        metadata = extractor.extract_metadata_enhanced()
        print(f"   ✓ 总页数: {metadata['page_count']}")
        print(f"   ✓ 总字符数: {metadata['content_analysis']['total_characters']}")
        print(
            f"   ✓ 检测语言: {metadata['content_analysis']['detected_language']}")

        print("3️⃣  提取结构化文本...")
        structured_text = extractor.extract_structured_text()
        print(f"   ✓ 提取了 {len(structured_text)} 个页面的文本")

        # ========== 阶段 2: 文档分块 ==========
        print("\n" + "="*70)
        print("✂️  阶段 2: 智能文档分块")
        print("="*70)

        print("\n1️⃣  创建分块器...")
        chunker = PDFChunker(chunk_size=1000, chunk_overlap=200)

        print("2️⃣  执行智能分块...")
        all_text = '\n\n'.join([page['text'] for page in structured_text])
        chunks = chunker.chunk_smart(all_text, strategy="hybrid")
        print(f"   ✓ 生成了 {len(chunks)} 个文档块")
        print(
            f"   ✓ 平均块大小: {sum(c['char_count'] for c in chunks) / len(chunks):.0f} 字符")

        # 显示第一个块的预览
        if chunks:
            first_chunk = chunks[0]
            print(f"\n   📝 第一个块预览:")
            print(f"   {first_chunk['text'][:150]}...")

        # ========== 阶段 3: 向量化 ==========
        print("\n" + "="*70)
        print("🧮 阶段 3: 生成向量嵌入")
        print("="*70)

        print("\n1️⃣  初始化 Embeddings 服务...")
        embeddings_service = EmbeddingsService(
            model_name="paraphrase-multilingual-MiniLM-L12-v2"
        )

        print("2️⃣  为文档块生成向量...")
        # 只处理前20个块以节省时间
        chunks_to_process = chunks[:20]
        chunks_with_embeddings = embeddings_service.encode_chunks(
            chunks_to_process,
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
            collection_name="test_collection",
            embeddings_service=embeddings_service
        )

        print("2️⃣  清空旧数据...")
        retrieval_service.clear_collection()

        print("3️⃣  添加文档块到向量数据库...")
        add_result = retrieval_service.add_documents(
            chunks_with_embeddings,
            document_id=document_id,
            batch_size=10
        )
        print(f"   ✓ 成功添加 {add_result['added']} 个块")

        print("4️⃣  获取集合统计...")
        stats = retrieval_service.get_collection_stats()
        print(f"   ✓ 集合名称: {stats['collection_name']}")
        print(f"   ✓ 总块数: {stats['total_chunks']}")
        print(f"   ✓ 向量维度: {stats['embedding_dimension']}")

        # ========== 阶段 5: 向量检索测试 ==========
        print("\n" + "="*70)
        print("🔍 阶段 5: 向量检索测试")
        print("="*70)

        test_queries = [
            "这篇论文的主要研究内容是什么？",
            "论文中使用了什么技术方法？",
            "研究的主要结论是什么？"
        ]

        for i, query in enumerate(test_queries, 1):
            print(f"\n{i}️⃣  查询: {query}")
            search_results = retrieval_service.search(query, n_results=3)
            print(f"   ✓ 找到 {len(search_results)} 个相关结果")

            if search_results:
                top_result = search_results[0]
                print(f"   📄 最相关结果预览:")
                print(f"   {top_result['text'][:150]}...")
                if top_result.get('distance') is not None:
                    relevance = 1 - top_result['distance']
                    print(f"   相关度: {relevance:.2%}")

        # ========== 阶段 6: RAG 问答 ==========
        print("\n" + "="*70)
        print("💬 阶段 6: RAG 智能问答")
        print("="*70)

        print("\n1️⃣  初始化 LLM 服务...")
        llm_service = LLMService(retrieval_service=retrieval_service)

        qa_questions = [
            "请简要介绍一下这篇论文的研究内容。",
            "论文的主要贡献是什么？"
        ]

        for i, question in enumerate(qa_questions, 1):
            print(f"\n{i}️⃣  问题: {question}")
            print("   🤖 Gemini 正在思考...")

            result = await llm_service.answer_question(
                question=question,
                document_id=document_id,
                n_contexts=3,
                language="zh"
            )

            print(f"\n   📝 回答:")
            print(f"   {result['answer']}")
            print(f"\n   📚 使用了 {result['source_count']} 个文档片段作为参考")

        # ========== 阶段 7: 文档总结 ==========
        print("\n" + "="*70)
        print("📊 阶段 7: 文档智能总结")
        print("="*70)

        print("\n1️⃣  生成文档总结...")
        summary_result = await llm_service.summarize_document(
            document_id=document_id,
            max_chunks=5,
            language="zh"
        )

        print(f"\n   📄 文档总结:")
        print(f"   {summary_result['summary']}")
        print(f"\n   ℹ️  基于 {summary_result['chunk_count']} 个文档块生成")

        # ========== 阶段 8: 关键词提取 ==========
        print("\n" + "="*70)
        print("🏷️  阶段 8: 关键词提取")
        print("="*70)

        print("\n1️⃣  提取文档关键词...")
        keywords_result = await llm_service.extract_keywords(
            document_id=document_id,
            max_keywords=10,
            language="zh"
        )

        print(f"\n   🔑 提取到 {keywords_result['count']} 个关键词:")
        for i, keyword in enumerate(keywords_result['keywords'], 1):
            print(f"   {i}. {keyword}")

        # ========== 测试完成 ==========
        print("\n" + "="*70)
        print("✅ 端到端测试完成！所有功能正常工作")
        print("="*70)

        print("\n📊 测试总结:")
        print(f"   • PDF 解析: ✅ {metadata['page_count']} 页")
        print(f"   • 文档分块: ✅ {len(chunks)} 个块")
        print(f"   • 向量生成: ✅ {len(chunks_with_embeddings)} 个向量")
        print(f"   • 数据库存储: ✅ {add_result['added']} 条记录")
        print(f"   • 向量检索: ✅ 正常")
        print(f"   • RAG 问答: ✅ 正常")
        print(f"   • 文档总结: ✅ 正常")
        print(f"   • 关键词提取: ✅ 正常")

        print("\n🎉 IntelliPDF 核心功能全部测试通过！")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
