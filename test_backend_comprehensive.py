"""
全面测试后端 API 完整性和状态
"""
import requests
import json
from pathlib import Path

API_BASE = "http://localhost:8000/api/v1"
TEST_PDF = "论文.pdf"


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_section(title):
    print(f"\n{Colors.CYAN}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.END}")
    print(f"{Colors.CYAN}{'='*80}{Colors.END}\n")


def print_success(msg):
    try:
        print(f"{Colors.GREEN}✓ {msg}{Colors.END}")
    except UnicodeEncodeError:
        print(f"{Colors.GREEN}[OK] {msg}{Colors.END}")


def print_error(msg):
    try:
        print(f"{Colors.RED}✗ {msg}{Colors.END}")
    except UnicodeEncodeError:
        print(f"{Colors.RED}[FAIL] {msg}{Colors.END}")


def print_warning(msg):
    try:
        print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")
    except UnicodeEncodeError:
        print(f"{Colors.YELLOW}[WARN] {msg}{Colors.END}")


def test_endpoint(name, method, url, **kwargs):
    """测试单个端点"""
    try:
        response = requests.request(method, url, timeout=10, **kwargs)
        status = response.status_code

        if 200 <= status < 300:
            print_success(f"{name}: {status}")
            return True, response
        else:
            print_error(f"{name}: {status}")
            print(f"  响应: {response.text[:200]}")
            return False, response
    except requests.exceptions.ConnectionError:
        print_error(f"{name}: 连接失败 - 后端服务未启动")
        return False, None
    except requests.exceptions.Timeout:
        print_error(f"{name}: 超时")
        return False, None
    except Exception as e:
        print_error(f"{name}: {str(e)}")
        return False, None


def main():
    print(f"\n{Colors.BOLD}{'='*80}")
    print(f"IntelliPDF 后端 API 完整性测试")
    print(f"{'='*80}{Colors.END}\n")

    results = {}
    doc_id = None

    # ============ 1. 基础健康检查 ============
    print_section("1. 基础服务检查")

    success, resp = test_endpoint(
        "健康检查", "GET", "http://localhost:8000/health"
    )
    results['health'] = success

    success, resp = test_endpoint(
        "API 文档", "GET", "http://localhost:8000/api/docs"
    )
    results['docs'] = success

    success, resp = test_endpoint(
        "OpenAPI Schema", "GET", "http://localhost:8000/openapi.json"
    )
    results['openapi'] = success

    # ============ 2. 文档管理 API ============
    print_section("2. 文档管理 API")

    # 2.1 获取文档列表
    success, resp = test_endpoint(
        "获取文档列表", "GET", f"{API_BASE}/documents",
        params={"skip": 0, "limit": 10}
    )
    results['list_documents'] = success
    if success and resp:
        data = resp.json()
        print(f"  总文档数: {data.get('total', 0)}")
        print(f"  返回数量: {len(data.get('documents', []))}")
        if data.get('documents'):
            doc_id = data['documents'][0]['id']
            print(f"  第一个文档ID: {doc_id}")

    # 2.2 上传文档
    if Path(TEST_PDF).exists():
        success, resp = test_endpoint(
            "上传文档", "POST", f"{API_BASE}/documents/upload",
            files={'file': (TEST_PDF, open(TEST_PDF, 'rb'), 'application/pdf')}
        )
        results['upload_document'] = success
        if success and resp:
            data = resp.json()
            print(f"  上传的文档ID: {data.get('id')}")
            print(f"  处理状态: {data.get('status')}")
            print(f"  错误信息: {data.get('processing_error', 'None')}")
            if not doc_id:
                doc_id = data.get('id')
    else:
        print_warning(f"测试文件不存在: {TEST_PDF}")
        results['upload_document'] = False

    # 2.3 获取单个文档
    if doc_id:
        success, resp = test_endpoint(
            "获取文档详情", "GET", f"{API_BASE}/documents/{doc_id}"
        )
        results['get_document'] = success
        if success and resp:
            data = resp.json()
            print(f"  文件名: {data.get('filename')}")
            print(f"  状态: {data.get('status')}")
            print(f"  块数量: {data.get('chunk_count')}")
    else:
        print_warning("跳过 - 没有可用的文档ID")
        results['get_document'] = False

    # 2.4 获取文档块
    if doc_id:
        success, resp = test_endpoint(
            "获取文档块", "GET", f"{API_BASE}/documents/{doc_id}/chunks",
            params={"skip": 0, "limit": 10}
        )
        results['get_chunks'] = success
        if success and resp:
            data = resp.json()
            print(f"  块总数: {data.get('total', 0)}")
    else:
        print_warning("跳过 - 没有可用的文档ID")
        results['get_chunks'] = False

    # 2.5 文档统计
    success, resp = test_endpoint(
        "文档统计", "GET", f"{API_BASE}/documents/statistics"
    )
    results['statistics'] = success
    if success and resp:
        data = resp.json()
        if isinstance(data, dict) and 'data' in data:
            stats = data['data']
            print(f"  总数: {stats.get('total', 'N/A')}")
            print(f"  按状态: {stats.get('by_status', {})}")

    # 2.6 聊天功能
    if doc_id:
        success, resp = test_endpoint(
            "文档对话", "POST", f"{API_BASE}/documents/{doc_id}/chat",
            json={"question": "这个文档讲了什么？", "stream": False}
        )
        results['chat'] = success
    else:
        print_warning("跳过 - 没有可用的文档ID")
        results['chat'] = False

    # 2.7 删除文档（最后测试，避免影响其他测试）
    # success, resp = test_endpoint(
    #     "删除文档", "DELETE", f"{API_BASE}/documents/{doc_id}"
    # )
    # results['delete_document'] = success

    # ============ 3. 增强文档 API ============
    print_section("3. 增强文档 API (documents-enhanced)")

    # 3.1 高级搜索
    success, resp = test_endpoint(
        "高级搜索", "GET", f"{API_BASE}/documents-enhanced/search/advanced",
        params={"query": "test", "limit": 10}
    )
    results['advanced_search'] = success

    # 3.2 详细统计
    success, resp = test_endpoint(
        "详细统计", "GET", f"{API_BASE}/documents-enhanced/statistics/detailed"
    )
    results['detailed_stats'] = success

    # 3.3 元数据导出
    success, resp = test_endpoint(
        "元数据导出", "GET", f"{API_BASE}/documents-enhanced/export/metadata",
        params={"format": "json"}
    )
    results['export_metadata'] = success

    # 3.4 批量删除（不实际执行）
    # success, resp = test_endpoint(
    #     "批量删除", "POST", f"{API_BASE}/documents-enhanced/batch/delete",
    #     json={"document_ids": []}
    # )
    # results['batch_delete'] = success

    # ============ 4. 知识图谱 API ============
    print_section("4. 知识图谱 API")

    # 4.1 获取图谱数据
    success, resp = test_endpoint(
        "图谱数据", "GET", f"{API_BASE}/knowledge-graph/graph-data",
        params={"limit": 50}
    )
    results['graph_data'] = success

    # 4.2 获取实体
    if doc_id:
        success, resp = test_endpoint(
            "文档实体", "GET", f"{API_BASE}/knowledge-graph/entities",
            params={"document_id": doc_id}
        )
        results['entities'] = success
    else:
        print_warning("跳过 - 没有可用的文档ID")
        results['entities'] = False

    # 4.3 获取关系
    success, resp = test_endpoint(
        "实体关系", "GET", f"{API_BASE}/knowledge-graph/relationships",
        params={"entity_id": "test"}
    )
    results['relationships'] = success

    # 4.4 分析文档
    if doc_id:
        success, resp = test_endpoint(
            "分析文档", "POST", f"{API_BASE}/knowledge-graph/analyze",
            params={"document_id": doc_id}
        )
        results['analyze'] = success
    else:
        print_warning("跳过 - 没有可用的文档ID")
        results['analyze'] = False

    # ============ 5. 文件访问 API ============
    print_section("5. 文件访问 API")

    if doc_id:
        # 5.1 获取文档文件
        success, resp = test_endpoint(
            "获取文档文件", "GET", f"{API_BASE}/documents/{doc_id}/file"
        )
        results['get_file'] = success
        if success and resp:
            print(f"  Content-Type: {resp.headers.get('Content-Type')}")
            print(
                f"  Content-Length: {resp.headers.get('Content-Length')} bytes")

        # 5.2 获取缩略图
        success, resp = test_endpoint(
            "获取缩略图", "GET", f"{API_BASE}/documents/{doc_id}/thumbnail",
            params={"page": 1}
        )
        results['get_thumbnail'] = success
    else:
        print_warning("跳过 - 没有可用的文档ID")
        results['get_file'] = False
        results['get_thumbnail'] = False

    # ============ 总结 ============
    print_section("测试总结")

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed

    print(f"总测试数: {total}")
    print_success(f"通过: {passed}")
    if failed > 0:
        print_error(f"失败: {failed}")

    print(f"\n{Colors.BOLD}失败的端点:{Colors.END}")
    for name, success in results.items():
        if not success:
            print_error(f"  - {name}")

    # ============ 问题诊断 ============
    print_section("问题诊断")

    # 检查文档处理状态
    if results.get('list_documents'):
        print(f"\n{Colors.BOLD}检查文档处理状态...{Colors.END}")
        try:
            resp = requests.get(f"{API_BASE}/documents",
                                params={"skip": 0, "limit": 100})
            docs = resp.json().get('documents', [])

            failed_docs = [d for d in docs if d.get('status') == 'failed']
            processing_docs = [d for d in docs if d.get(
                'status') == 'processing']
            completed_docs = [d for d in docs if d.get(
                'status') == 'completed']

            print(f"  完成: {len(completed_docs)}")
            print(f"  处理中: {len(processing_docs)}")
            print(f"  失败: {len(failed_docs)}")

            if failed_docs:
                print(f"\n{Colors.RED}失败的文档:{Colors.END}")
                for doc in failed_docs[:3]:  # 只显示前3个
                    print(f"  - {doc['filename']}")
                    print(f"    错误: {doc.get('processing_error', 'Unknown')}")
        except Exception as e:
            print_error(f"无法获取文档状态: {e}")

    # 检查是否有文件访问端点
    print(f"\n{Colors.BOLD}文件访问端点状态:{Colors.END}")
    if not results.get('get_file'):
        print_warning("文档文件访问端点不可用 - 前端无法预览 PDF")
        print("  需要实现: GET /api/v1/documents/{id}/file")

    if not results.get('get_thumbnail'):
        print_warning("缩略图端点不可用")
        print("  需要实现: GET /api/v1/documents/{id}/thumbnail")

    print(f"\n{Colors.BOLD}建议:{Colors.END}")
    if failed > 0:
        print("1. 检查后端日志: backend/logs/intellipdf_2025-10-07.log")
        print("2. 确认所有路由都已注册")
        print("3. 检查数据库连接是否正常")
        print("4. 验证文档处理服务是否工作")


if __name__ == "__main__":
    main()
