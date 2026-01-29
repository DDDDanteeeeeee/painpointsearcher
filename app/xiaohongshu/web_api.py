"""
小红书自动化系统 - Web API 服务

提供 Web 界面的后端支持
"""

import asyncio
import json
import uvicorn
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import sys

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.xiaohongshu.xiaohongshu_agent import XiaohongshuAgent
from app.xiaohongshu.config import get_config, ConfigManager, XiaohongshuConfig
from app.logger import logger


# ============ Pydantic 模型 ============

class APIResponse(BaseModel):
    """API 响应"""
    success: bool
    message: str
    data: Optional[dict] = None


class LLMConfigModel(BaseModel):
    """LLM 配置"""
    model: str
    base_url: str
    api_key: str
    max_tokens: int = 4096
    temperature: float = 0.0


class XiaohongshuConfigModel(BaseModel):
    """小红书配置"""
    target_daily_replies: int = 5
    max_daily_replies: int = 10
    working_hours_start: int = 9
    working_hours_end: int = 22
    min_relevance_score: float = 0.7
    min_attractiveness_score: float = 0.6
    require_human_review: bool = True
    enable_safety_limits: bool = True
    random_delay_min: int = 300
    random_delay_max: int = 900
    simulate_human_typing: bool = True
    simulate_reading: bool = True
    random_mouse_movement: bool = True


class TaskRequest(BaseModel):
    """任务请求"""
    mode: str = "full"
    max_topics: int = 20
    max_replies: int = 5
    url: Optional[str] = None
    auto_send: bool = False


# ============ FastAPI 应用 ============

app = FastAPI(title="小红书自动化系统", version="1.0.0")

# 全局变量
agent: Optional[XiaohongshuAgent] = None
task_running = False
task_status = {
    "status": "idle",  # idle, running, paused, error
    "current_step": "",
    "progress": 0,
    "message": "",
    "start_time": None,
    "logs": []
}

# WebSocket 连接管理
active_websockets: List[WebSocket] = []


async def broadcast_log(message: str, level: str = "info"):
    """广播日志到所有 WebSocket 客户端"""
    log_entry = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "level": level,
        "message": message
    }
    task_status["logs"].append(log_entry)

    # 保持最近 100 条日志
    if len(task_status["logs"]) > 100:
        task_status["logs"] = task_status["logs"][-100:]

    # 广播到所有连接的客户端
    for websocket in active_websockets:
        try:
            await websocket.send_json({
                "type": "log",
                "data": log_entry
            })
        except:
            pass


async def broadcast_status():
    """广播状态更新"""
    for websocket in active_websockets:
        try:
            await websocket.send_json({
                "type": "status",
                "data": task_status
            })
        except:
            pass


# ============ 路由：前端页面 ============

@app.get("/", response_class=HTMLResponse)
async def get_web_interface():
    """返回 Web 界面"""
    html_path = Path(__file__).parent.parent.parent / "app" / "xiaohongshu" / "web_interface.html"
    if html_path.exists():
        with open(html_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "<h1>Web 界面未找到，请重新安装</h1>"


# ============ 路由：配置管理 ============

@app.get("/api/config/llm", response_model=APIResponse)
async def get_llm_config():
    """获取 LLM 配置"""
    try:
        config_path = Path("config/config.toml")
        if not config_path.exists():
            return APIResponse(success=False, message="配置文件不存在")

        import toml
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = toml.load(f)

        llm_config = config_data.get('llm', {})

        # 隐藏 API Key 的部分内容
        if 'api_key' in llm_config:
            api_key = llm_config['api_key']
            if len(api_key) > 10:
                llm_config['api_key'] = api_key[:8] + '...' + api_key[-4:]

        return APIResponse(
            success=True,
            message="获取配置成功",
            data=llm_config
        )
    except Exception as e:
        return APIResponse(success=False, message=f"获取配置失败: {str(e)}")


@app.post("/api/config/llm", response_model=APIResponse)
async def save_llm_config(config: LLMConfigModel):
    """保存 LLM 配置"""
    try:
        import toml

        config_path = Path("config/config.toml")
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # 读取现有配置
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = toml.load(f)
        else:
            config_data = {}

        # 更新 LLM 配置
        config_data['llm'] = {
            "model": config.model,
            "base_url": config.base_url,
            "api_key": config.api_key,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature
        }

        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            toml.dump(config_data, f)

        await broadcast_log("LLM 配置已更新", "success")
        return APIResponse(success=True, message="配置保存成功")

    except Exception as e:
        await broadcast_log(f"保存配置失败: {str(e)}", "error")
        return APIResponse(success=False, message=f"保存配置失败: {str(e)}")


@app.get("/api/config/xiaohongshu", response_model=APIResponse)
async def get_xiaohongshu_config():
    """获取小红书配置"""
    try:
        config_manager = get_config()
        config = config_manager.get()

        return APIResponse(
            success=True,
            message="获取配置成功",
            data=config.model_dump()
        )
    except Exception as e:
        return APIResponse(success=False, message=f"获取配置失败: {str(e)}")


@app.post("/api/config/xiaohongshu", response_model=APIResponse)
async def save_xiaohongshu_config(config: XiaohongshuConfigModel):
    """保存小红书配置"""
    try:
        import toml

        config_path = Path("config/xiaohongshu.toml")
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            toml.dump({'xiaohongshu': config.model_dump()}, f)

        # 重新加载配置
        config_manager = get_config()
        config_manager.config = XiaohongshuConfig(**config.model_dump())

        await broadcast_log("小红书配置已更新", "success")
        return APIResponse(success=True, message="配置保存成功")

    except Exception as e:
        await broadcast_log(f"保存配置失败: {str(e)}", "error")
        return APIResponse(success=False, message=f"保存配置失败: {str(e)}")


# ============ 路由：任务管理 ============

@app.get("/api/task/status", response_model=APIResponse)
async def get_task_status():
    """获取任务状态"""
    return APIResponse(
        success=True,
        message="获取状态成功",
        data=task_status
    )


@app.post("/api/task/start", response_model=APIResponse)
async def start_task(request: TaskRequest):
    """启动任务"""
    global agent, task_running

    if task_running:
        return APIResponse(success=False, message="任务正在运行中")

    try:
        # 初始化 Agent
        if agent is None:
            agent = XiaohongshuAgent()
            await agent.initialize()

        task_running = True
        task_status["status"] = "running"
        task_status["start_time"] = datetime.now().isoformat()
        task_status["logs"] = []

        await broadcast_log("任务开始执行", "info")
        await broadcast_status()

        # 在后台运行任务
        asyncio.create_task(run_task_in_background(request))

        return APIResponse(success=True, message="任务已启动")

    except Exception as e:
        task_running = False
        task_status["status"] = "error"
        await broadcast_log(f"任务启动失败: {str(e)}", "error")
        await broadcast_status()
        return APIResponse(success=False, message=f"启动失败: {str(e)}")


@app.post("/api/task/stop", response_model=APIResponse)
async def stop_task():
    """停止任务"""
    global task_running

    if not task_running:
        return APIResponse(success=False, message="没有运行中的任务")

    task_running = False
    task_status["status"] = "idle"
    await broadcast_log("任务已停止", "warning")
    await broadcast_status()

    return APIResponse(success=True, message="任务已停止")


# ============ 后台任务 ============

async def run_task_in_background(request: TaskRequest):
    """在后台运行任务"""
    global task_running, agent

    try:
        await broadcast_log(f"运行模式: {request.mode}", "info")

        if request.mode == "full":
            task_status["current_step"] = "完整工作流"
            await broadcast_log("开始完整工作流...", "info")
            result = await agent.run_full_workflow(
                max_topics=request.max_topics,
                max_replies=request.max_replies
            )

        elif request.mode == "collect":
            task_status["current_step"] = "收集热点"
            await broadcast_log("收集热点中...", "info")
            topics = await agent.collect_only(max_topics=request.max_topics)
            result = type('Result', (), {'success': True, 'topics_collected': len(topics)})()

        elif request.mode == "analyze":
            task_status["current_step"] = "分析需求"
            await broadcast_log("收集并分析热点...", "info")
            topics = await agent.collect_only(max_topics=request.max_topics)
            analyses = await agent.analyze_only(topics)
            result = type('Result', (), {'success': True, 'topics_analyzed': len(analyses)})()

        elif request.mode == "generate":
            task_status["current_step"] = "生成回复"
            await broadcast_log("生成回复内容...", "info")
            topics = await agent.collect_only(max_topics=request.max_topics)
            analyses = await agent.analyze_only(topics)
            reply_sets = await agent.generate_only(analyses, max_replies=request.max_replies)
            result = type('Result', (), {'success': True, 'replies_generated': len(reply_sets)})()

        elif request.mode == "single":
            if not request.url:
                raise Exception("single 模式需要提供 URL")

            task_status["current_step"] = "处理单个帖子"
            await broadcast_log(f"处理帖子: {request.url}", "info")
            success = await agent.reply_one(request.url, auto_send=request.auto_send)
            result = type('Result', (), {'success': success})()

        else:
            raise Exception(f"未知的运行模式: {request.mode}")

        task_status["status"] = "completed"
        task_status["progress"] = 100

        if result.success:
            await broadcast_log("任务执行完成！", "success")
        else:
            await broadcast_log("任务执行失败", "error")

    except Exception as e:
        await broadcast_log(f"任务执行出错: {str(e)}", "error")
        task_status["status"] = "error"

    finally:
        task_running = False
        task_status["current_step"] = ""
        await broadcast_status()


# ============ 路由：数据查看 ============

@app.get("/api/data/hot-topics", response_model=APIResponse)
async def get_hot_topics():
    """获取热点数据"""
    try:
        config = get_config().get()
        date_str = datetime.now().strftime("%Y%m%d")
        file_path = config.hot_topics_dir / f"hot_topics_{date_str}.json"

        if not file_path.exists():
            return APIResponse(success=False, message="今日暂无热点数据")

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return APIResponse(
            success=True,
            message=f"获取到 {len(data)} 个热点",
            data={"topics": data}
        )

    except Exception as e:
        return APIResponse(success=False, message=f"获取数据失败: {str(e)}")


@app.get("/api/data/analysis", response_model=APIResponse)
async def get_analysis():
    """获取分析结果"""
    try:
        config = get_config().get()
        date_str = datetime.now().strftime("%Y%m%d")
        file_path = config.analysis_dir / f"analysis_{date_str}.jsonl"

        if not file_path.exists():
            return APIResponse(success=False, message="今日暂无分析数据")

        analyses = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    analyses.append(json.loads(line))

        return APIResponse(
            success=True,
            message=f"获取到 {len(analyses)} 个分析结果",
            data={"analyses": analyses[:10]}  # 只返回前 10 个
        )

    except Exception as e:
        return APIResponse(success=False, message=f"获取数据失败: {str(e)}")


@app.get("/api/data/replies", response_model=APIResponse)
async def get_replies():
    """获取生成的回复"""
    try:
        config = get_config().get()
        replies_dir = config.content_dir

        if not replies_dir.exists():
            return APIResponse(success=False, message="暂无生成的回复")

        # 获取最新的回复文件
        files = sorted(replies_dir.glob("replies_*.md"), reverse=True)

        if not files:
            return APIResponse(success=False, message="暂无生成的回复")

        # 读取最新的文件
        with open(files[0], 'r', encoding='utf-8') as f:
            content = f.read()

        return APIResponse(
            success=True,
            message=f"获取到回复内容",
            data={"content": content, "file": files[0].name}
        )

    except Exception as e:
        return APIResponse(success=False, message=f"获取数据失败: {str(e)}")


# ============ WebSocket ============

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 端点，用于实时日志"""
    await websocket.accept()
    active_websockets.append(websocket)

    try:
        # 发送当前状态
        await websocket.send_json({
            "type": "status",
            "data": task_status
        })

        # 保持连接
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        active_websockets.remove(websocket)


# ============ 启动服务器 ============

def start_server(host: str = "127.0.0.1", port: int = 8000):
    """启动 Web 服务器"""
    logger.info(f"🚀 启动 Web 界面: http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="小红书自动化系统 - Web 界面")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="监听地址")
    parser.add_argument("--port", type=int, default=8000, help="监听端口")

    args = parser.parse_args()

    start_server(host=args.host, port=args.port)
