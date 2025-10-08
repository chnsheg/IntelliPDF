"""
安全的服务状态检查 - 只查询进程和端口,不发送 HTTP 请求
避免中断正在运行的服务器
"""
import subprocess
import sys
from datetime import datetime


def check_process(process_name, filter_path=None):
    """检查进程是否运行"""
    try:
        if sys.platform == 'win32':
            cmd = f'powershell -Command "Get-Process {process_name} -ErrorAction SilentlyContinue'
            if filter_path:
                cmd += f' | Where-Object {{$_.Path -like \\"{filter_path}\\"}}'
            cmd += ' | Select-Object -First 1"'

            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=5)
            return bool(result.stdout.strip())
    except Exception as e:
        print(f"检查进程出错: {e}")
    return False


def check_port(port):
    """检查端口是否被监听"""
    try:
        if sys.platform == 'win32':
            cmd = f'netstat -ano | findstr ":{port}" | findstr "LISTENING"'
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=5)
            return bool(result.stdout.strip())
    except Exception as e:
        print(f"检查端口出错: {e}")
    return False


def main():
    print("=" * 60)
    print("IntelliPDF 服务状态检查 (安全模式 - 不发送请求)")
    print("=" * 60)
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 检查后端进程
    print("[1/4] 检查后端进程...")
    backend_running = check_process("python", "*IntelliPDF*backend*")
    if backend_running:
        print("  ✅ 后端 Python 进程运行中")
    else:
        print("  ❌ 后端进程未找到")
    print()

    # 检查前端进程
    print("[2/4] 检查前端进程...")
    frontend_running = check_process("node")
    if frontend_running:
        print("  ✅ 前端 Node 进程运行中")
    else:
        print("  ⚠️  前端进程未找到 (需要启动)")
    print()

    # 检查后端端口
    print("[3/4] 检查后端端口...")
    backend_port = check_port(8000)
    if backend_port:
        print("  ✅ 端口 8000 已监听 (后端)")
        print("     URL: http://localhost:8000")
    else:
        print("  ❌ 端口 8000 未监听")
    print()

    # 检查前端端口
    print("[4/4] 检查前端端口...")
    frontend_port = check_port(5174)
    if frontend_port:
        print("  ✅ 端口 5174 已监听 (前端)")
        print("     URL: http://localhost:5174")
    else:
        print("  ⚠️  端口 5174 未监听 (需要启动前端)")
    print()

    # 总结
    print("=" * 60)
    print("状态总结")
    print("=" * 60)

    if backend_running and backend_port:
        print("✅ 后端: 正常运行")
    else:
        print("❌ 后端: 未运行或未就绪")

    if frontend_running and frontend_port:
        print("✅ 前端: 正常运行")
    else:
        print("⚠️  前端: 需要启动")

    print()

    # 建议操作
    if not (frontend_running and frontend_port):
        print("📍 下一步操作:")
        print("   运行脚本启动前端 (不会中断后端):")
        print("   .\\START_FRONTEND_NEW_WINDOW.bat")
        print()

    if backend_running and frontend_running:
        print("🎉 系统就绪!")
        print()
        print("📍 访问地址:")
        print("   前端: http://localhost:5174")
        print("   后端: http://localhost:8000")
        print("   API 文档: http://localhost:8000/api/docs")
        print()
        print("🧪 测试步骤:")
        print("   1. 打开浏览器访问前端")
        print("   2. 按 F12 查看 Console")
        print("   3. 上传 PDF 并查看详情")
        print("   4. 验证页面不再空白")


if __name__ == "__main__":
    main()
