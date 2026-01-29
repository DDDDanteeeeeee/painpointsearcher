"""
小红书自动化系统启动脚本
"""

import asyncio
import argparse
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.xiaohongshu.xiaohongshu_agent import XiaohongshuAgent
from app.logger import logger


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="小红书热点挖掘与智能回复系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 运行完整工作流（收集 + 分析 + 生成 + 回复）
  python run_xiaohongshu.py

  # 仅收集热点
  python run_xiaohongshu.py --mode collect

  # 收集并分析
  python run_xiaohongshu.py --mode analyze

  # 生成回复（不发送）
  python run_xiaohongshu.py --mode generate

  # 处理单个帖子
  python run_xiaohongshu.py --mode single --url "https://www.xiaohongshu.com/..."

  # 完整流程，自定义数量
  python run_xiaohongshu.py --topics 30 --replies 8
        """
    )

    parser.add_argument(
        "--mode",
        type=str,
        choices=["full", "collect", "analyze", "generate", "single"],
        default="full",
        help="运行模式：full(完整流程) | collect(仅收集) | analyze(收集+分析) | generate(生成回复) | single(单个帖子)"
    )

    parser.add_argument(
        "--topics",
        type=int,
        default=20,
        help="最大收集热点数（默认: 20）"
    )

    parser.add_argument(
        "--replies",
        type=int,
        default=5,
        help="最大回复数（默认: 5）"
    )

    parser.add_argument(
        "--url",
        type=str,
        help="单个帖子链接（仅 single 模式）"
    )

    parser.add_argument(
        "--auto-send",
        action="store_true",
        help="自动发送回复（Level 3，慎用）"
    )

    args = parser.parse_args()

    # 创建 Agent
    agent = XiaohongshuAgent()

    try:
        if args.mode == "full":
            # 完整工作流
            logger.info(f"🚀 启动完整工作流（目标: 收集 {args.topics} 个热点，回复 {args.replies} 条）")
            result = await agent.run_full_workflow(
                max_topics=args.topics,
                max_replies=args.replies
            )

            if result.success:
                logger.info("\n✅ 工作流完成！")
                logger.info(f"📁 结果保存在: workspace/xiaohongshu/")
            else:
                logger.error("\n❌ 工作流失败")
                sys.exit(1)

        elif args.mode == "collect":
            # 仅收集
            logger.info(f"📍 模式: 仅收集热点（{args.topics} 个）")
            topics = await agent.collect_only(max_topics=args.topics)
            logger.info(f"✅ 收集完成: {len(topics)} 个热点")

        elif args.mode == "analyze":
            # 收集 + 分析
            logger.info(f"📍 模式: 收集并分析（{args.topics} 个）")
            topics = await agent.collect_only(max_topics=args.topics)
            analyses = await agent.analyze_only(topics)
            logger.info(f"✅ 分析完成: {len(analyses)} 个话题")
            logger.info("\n🏆 TOP 5 高价值话题:")
            for i, analysis in enumerate(analyses[:5], 1):
                logger.info(f"  {i}. {analysis.topic.title} (优先级: {analysis.priority:.2f})")

        elif args.mode == "generate":
            # 收集 + 分析 + 生成
            logger.info(f"📍 模式: 生成回复内容（{args.topics} 个热点，{args.replies} 个回复）")
            topics = await agent.collect_only(max_topics=args.topics)
            analyses = await agent.analyze_only(topics)
            reply_sets = await agent.generate_only(analyses, max_replies=args.replies)
            logger.info(f"✅ 生成完成: {len(reply_sets)} 组回复")
            logger.info(f"📁 查看生成的内容: workspace/xiaohongshu/generated_content/")

        elif args.mode == "single":
            # 单个帖子
            if not args.url:
                logger.error("--single 模式需要 --url 参数")
                sys.exit(1)

            logger.info(f"📍 模式: 单个帖子")
            logger.info(f"URL: {args.url}")
            logger.info(f"自动发送: {'是 ⚠️' if args.auto_send else '否（需手动确认）'}")

            success = await agent.reply_one(args.url, auto_send=args.auto_send)

            if success:
                logger.info("✅ 处理完成")
            else:
                logger.error("❌ 处理失败")
                sys.exit(1)

    except KeyboardInterrupt:
        logger.warning("\n⚠️  用户中断")
        sys.exit(0)

    except Exception as e:
        logger.error(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        # 清理资源
        await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
