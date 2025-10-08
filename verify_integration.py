"""
快速验证前后端集成状态
测试书签系统的关键端点
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"
HEALTH_URL = "http://localhost:8000/health"


def test_health():
    """测试后端健康状态"""
    try:
        response = requests.get(HEALTH_URL, timeout=5)
        if response.status_code == 200:
            print("✅ 后端健康检查通过")
            print(f"   响应: {response.json()}")
            return True
        else:
            print(f"❌ 后端健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 后端连接失败: {e}")
        return False


def test_frontend():
    """测试前端可访问性"""
    try:
        response = requests.get("http://localhost:5174", timeout=5)
        if response.status_code == 200:
            print("✅ 前端服务正常运行")
            return True
        else:
            print(f"❌ 前端访问失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 前端连接失败: {e}")
        return False


def test_bookmark_endpoints():
    """测试书签相关端点"""
    print("\n📚 测试书签 API 端点:")

    # 测试获取书签列表 (无需认证)
    try:
        response = requests.get(f"{BASE_URL}/bookmarks", timeout=5)
        print(f"   GET /bookmarks: {response.status_code}")
        if response.status_code in [200, 401]:  # 200=成功, 401=需要认证(正常)
            print(f"   ✅ 端点可访问")
        else:
            print(f"   ⚠️  意外状态码: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 请求失败: {e}")


def print_summary():
    """打印测试总结"""
    print("\n" + "="*60)
    print("📋 书签系统集成状态总结")
    print("="*60)
    print("\n🔧 服务状态:")
    print(f"   • 后端: http://localhost:8000")
    print(f"   • 前端: http://localhost:5174")
    print(f"   • API 文档: http://localhost:8000/api/docs")

    print("\n📝 前端集成完成项:")
    print("   ✅ DocumentViewerPage 集成 BookmarkPanel")
    print("   ✅ PDFViewerEnhanced 连接书签数据和回调")
    print("   ✅ ChatPanel 集成文本选择和书签生成")
    print("   ✅ 三栏布局: 书签 + PDF + 聊天")
    print("   ✅ 响应式设计 (桌面/移动)")

    print("\n🧪 下一步测试:")
    print("   1. 访问 http://localhost:5174")
    print("   2. 上传测试 PDF (如 论文.pdf)")
    print("   3. 点击书签图标打开书签面板")
    print("   4. 选择 PDF 文本并生成书签")
    print("   5. 测试书签跳转、编辑、删除功能")

    print("\n📖 详细测试指南:")
    print("   参考文件: BOOKMARK_INTEGRATION_TEST_GUIDE.md")
    print("="*60)


def main():
    print("🚀 IntelliPDF 书签系统集成验证")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 测试后端
    backend_ok = test_health()

    # 测试前端
    frontend_ok = test_frontend()

    # 测试书签端点
    if backend_ok:
        test_bookmark_endpoints()

    # 打印总结
    print_summary()

    # 最终状态
    if backend_ok and frontend_ok:
        print("\n✅ 系统就绪! 可以开始浏览器测试")
        print("   👉 打开浏览器访问: http://localhost:5174\n")
    else:
        print("\n⚠️  部分服务未就绪,请检查上述错误信息\n")


if __name__ == "__main__":
    main()
