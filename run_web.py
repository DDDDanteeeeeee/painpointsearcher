"""
小红书自动化系统 - Web 界面启动脚本

双击运行或在命令行执行：python run_web.py
"""

import sys
import subprocess
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 小红书自动化系统 - Web 界面")
    print("=" * 60)
    print()
    print("正在启动 Web 服务...")
    print()

    # 导入并启动
    from app.xiaohongshu.web_api import start_server

    try:
        # 默认监听本地地址，端口 8000
        start_server(host="127.0.0.1", port=8000)

    except KeyboardInterrupt:
        print()
        print("=" * 60)
        print("⚠️  Web 服务已停止")
        print("=" * 60)
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ 启动失败: {e}")
        print("=" * 60)
        print()
        print("可能的原因：")
        print("1. 端口 8000 已被占用，请尝试修改端口")
        print("2. 缺少依赖，请运行: pip install -r requirements.txt")
        print()
        input("按回车键退出...")
