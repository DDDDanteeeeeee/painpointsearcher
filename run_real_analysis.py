"""
快速分析真实小红书链接
"""
import asyncio
import sys
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from manual_real_system import ManualRealAgent

async def main():
    # 真实的小红书链接
    url = "https://www.xiaohongshu.com/discovery/item/697a9077000000000e00e7fc?source=webshare&xhsshare=pc_web&xsec_token=ABUpvzIENTEt6z7mntxNiFy-qm6FfB910ihzYSZ-qGq8Q=&xsec_source=pc_share"

    print()
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 12 + "小红书真实数据分析系统" + " " * 26 + "║")
    print("║" + " " * 10 + "🔗 分析真实链接数据" + " " * 27 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    print(f"📍 目标URL: {url[:80]}...")
    print()

    # 创建 Agent
    agent = ManualRealAgent()

    try:
        # 运行工作流
        result = await agent.run_single_url_workflow(url)

        if result.get("success"):
            print()
            print("🎉 分析完成！")
            print()
            print("📁 查看结果:")
            print("   - 报告: workspace/xiaohongshu/generated_content/")
            print("   - 数据: workspace/xiaohongshu/analysis/")
            print()

    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
