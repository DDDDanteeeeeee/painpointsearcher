"""
小红书自动化系统 - 简化版Web界面
单页面任务调度器
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from threading import Thread
import time

# 导入完整系统
from run_full_system import XiaohongshuAgent

app = Flask(__name__)

# 存储任务结果
task_results = {}
task_counter = 0

# ============ 后端任务执行 ============
def run_background_task(task_id, task_config):
    """后台执行任务"""
    try:
        print(f"[任务 {task_id}] 开始执行...")

        # 创建Agent
        agent = XiaohongshuAgent()

        # 运行工作流
        result = asyncio.run(agent.run_full_workflow(
            max_topics=task_config.get('max_topics', 5),
            max_replies=task_config.get('max_replies', 3)
        ))

        # 更新任务状态
        task_results[task_id]['status'] = 'completed'
        task_results[task_id]['result'] = result
        task_results[task_id]['completed_at'] = datetime.now().isoformat()

        print(f"[任务 {task_id}] 执行完成")

    except Exception as e:
        print(f"[任务 {task_id}] 执行失败: {e}")
        task_results[task_id]['status'] = 'failed'
        task_results[task_id]['error'] = str(e)
        task_results[task_id]['completed_at'] = datetime.now().isoformat()

# ============ 路由 ============
@app.route('/')
def index():
    """主页 - 任务输入页面"""
    return '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>小红书自动化系统</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
        }

        .header {
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }

        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }

        .card {
            background: white;
            border-radius: 16px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            margin-bottom: 20px;
        }

        .form-group {
            margin-bottom: 25px;
        }

        .form-group label {
            display: block;
            font-weight: 600;
            margin-bottom: 8px;
            color: #333;
            font-size: 1.05em;
        }

        .form-group input[type="text"],
        .form-group input[type="datetime-local"],
        .form-group input[type="number"],
        .form-group select,
        .form-group textarea {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 1em;
            transition: all 0.3s;
        }

        .form-group input:focus,
        .form-group select:focus,
        .form-group textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .form-group textarea {
            resize: vertical;
            min-height: 100px;
        }

        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }

        .conditional-field {
            display: none;
            margin-top: 15px;
        }

        .conditional-field.show {
            display: block;
        }

        .btn {
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1.1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }

        .btn:active {
            transform: translateY(0);
        }

        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }

        .results-section {
            margin-top: 40px;
        }

        .task-card {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            border-left: 4px solid #667eea;
        }

        .task-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }

        .task-id {
            font-weight: 600;
            color: #667eea;
        }

        .task-status {
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
        }

        .status-pending {
            background: #fff3cd;
            color: #856404;
        }

        .status-running {
            background: #d1ecf1;
            color: #0c5460;
        }

        .status-completed {
            background: #d4edda;
            color: #155724;
        }

        .status-failed {
            background: #f8d7da;
            color: #721c24;
        }

        .task-details {
            color: #666;
            font-size: 0.95em;
            line-height: 1.6;
        }

        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .hidden {
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔥 小红书自动化系统</h1>
            <p>OpenManus 智能任务调度器</p>
        </div>

        <div class="card">
            <form id="taskForm">
                <div class="form-group">
                    <label for="taskDescription">📝 任务描述</label>
                    <textarea id="taskDescription" placeholder="例如：收集今天的小红书热点，分析用户需求，生成回复建议..." required></textarea>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label for="taskTime">⏰ 执行时间</label>
                        <input type="datetime-local" id="taskTime" required>
                    </div>

                    <div class="form-group">
                        <label for="platform">🎯 执行平台</label>
                        <select id="platform" onchange="toggleCustomUrl()" required>
                            <option value="xiaohongshu">小红书</option>
                            <option value="custom">自定义网址</option>
                        </select>
                    </div>
                </div>

                <div class="form-group conditional-field" id="customUrlField">
                    <label for="customUrl">🔗 自定义网址</label>
                    <input type="text" id="customUrl" placeholder="https://...">
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label for="maxTopics">📊 收集热点数量</label>
                        <input type="number" id="maxTopics" value="5" min="1" max="20">
                    </div>

                    <div class="form-group">
                        <label for="maxReplies">💬 生成回复数量</label>
                        <input type="number" id="maxReplies" value="3" min="1" max="10">
                    </div>
                </div>

                <button type="submit" class="btn" id="submitBtn">🚀 立即执行</button>
            </form>
        </div>

        <div class="card results-section hidden" id="resultsSection">
            <h2 style="margin-bottom: 20px;">📋 任务执行结果</h2>
            <div id="taskResults"></div>
        </div>
    </div>

    <script>
        // 设置默认时间为当前时间
        const now = new Date();
        now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
        document.getElementById('taskTime').value = now.toISOString().slice(0, 16);

        function toggleCustomUrl() {
            const platform = document.getElementById('platform').value;
            const customUrlField = document.getElementById('customUrlField');
            if (platform === 'custom') {
                customUrlField.classList.add('show');
                document.getElementById('customUrl').required = true;
            } else {
                customUrlField.classList.remove('show');
                document.getElementById('customUrl').required = false;
            }
        }

        document.getElementById('taskForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const submitBtn = document.getElementById('submitBtn');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="loading"></span> 提交中...';

            const taskData = {
                description: document.getElementById('taskDescription').value,
                time: document.getElementById('taskTime').value,
                platform: document.getElementById('platform').value,
                custom_url: document.getElementById('customUrl').value,
                max_topics: parseInt(document.getElementById('maxTopics').value),
                max_replies: parseInt(document.getElementById('maxReplies').value)
            };

            try {
                const response = await fetch('/api/execute', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(taskData)
                });

                const result = await response.json();

                // 显示结果区域
                document.getElementById('resultsSection').classList.remove('hidden');

                // 添加任务卡片
                addTaskCard(result.task_id, taskData);

                // 开始轮询任务状态
                pollTaskStatus(result.task_id);

            } catch (error) {
                alert('提交失败: ' + error.message);
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '🚀 立即执行';
            }
        });

        function addTaskCard(taskId, taskData) {
            const resultsDiv = document.getElementById('taskResults');
            const card = document.createElement('div');
            card.className = 'task-card';
            card.id = `task-${taskId}`;
            card.innerHTML = `
                <div class="task-header">
                    <span class="task-id">任务 #${taskId}</span>
                    <span class="task-status status-pending" id="status-${taskId}">
                        <span class="loading"></span> 等待执行
                    </span>
                </div>
                <div class="task-details">
                    <p><strong>任务:</strong> ${taskData.description}</p>
                    <p><strong>平台:</strong> ${taskData.platform === 'xiaohongshu' ? '小红书' : taskData.custom_url}</p>
                    <p><strong>配置:</strong> 收集 ${taskData.max_topics} 个热点，生成 ${taskData.max_replies} 组回复</p>
                </div>
            `;
            resultsDiv.insertBefore(card, resultsDiv.firstChild);
        }

        async function pollTaskStatus(taskId) {
            const interval = setInterval(async () => {
                try {
                    const response = await fetch(`/api/task_status/${taskId}`);
                    const data = await response.json();

                    const statusEl = document.getElementById(`status-${taskId}`);
                    const cardEl = document.getElementById(`task-${taskId}`);

                    if (data.status === 'running') {
                        statusEl.className = 'task-status status-running';
                        statusEl.innerHTML = '<span class="loading"></span> 执行中...';
                    } else if (data.status === 'completed') {
                        clearInterval(interval);
                        statusEl.className = 'task-status status-completed';
                        statusEl.innerHTML = '✅ 完成';

                        // 添加结果详情
                        const detailsDiv = cardEl.querySelector('.task-details');
                        detailsDiv.innerHTML += `
                            <hr style="margin: 15px 0; border: none; border-top: 1px solid #ddd;">
                            <p><strong>✨ 执行结果:</strong></p>
                            <ul style="margin-left: 20px; margin-top: 10px;">
                                <li>收集热点: ${data.result.topics_collected} 个</li>
                                <li>分析话题: ${data.result.topics_analyzed} 个</li>
                                <li>生成回复: ${data.result.replies_generated} 组</li>
                            </ul>
                            <p style="margin-top: 10px; color: #667eea;">
                                <a href="/api/task_result/${taskId}" target="_blank" style="color: #667eea; text-decoration: none;">
                                    🔍 查看详细报告 →
                                </a>
                            </p>
                        `;
                    } else if (data.status === 'failed') {
                        clearInterval(interval);
                        statusEl.className = 'task-status status-failed';
                        statusEl.innerHTML = '❌ 失败';

                        const detailsDiv = cardEl.querySelector('.task-details');
                        detailsDiv.innerHTML += `
                            <hr style="margin: 15px 0; border: none; border-top: 1px solid #ddd;">
                            <p style="color: #dc3545;"><strong>错误:</strong> ${data.error}</p>
                        `;
                    }
                } catch (error) {
                    console.error('轮询失败:', error);
                }
            }, 2000);
        }
    </script>
</body>
</html>
    '''

@app.route('/api/execute', methods=['POST'])
def execute_task():
    """执行任务"""
    global task_counter
    task_counter += 1
    task_id = task_counter

    data = request.json
    task_config = {
        'description': data.get('description'),
        'time': data.get('time'),
        'platform': data.get('platform'),
        'custom_url': data.get('custom_url'),
        'max_topics': data.get('max_topics', 5),
        'max_replies': data.get('max_replies', 3)
    }

    # 初始化任务状态
    task_results[task_id] = {
        'id': task_id,
        'status': 'pending',
        'config': task_config,
        'created_at': datetime.now().isoformat()
    }

    # 在后台线程中执行任务
    thread = Thread(target=run_background_task, args=(task_id, task_config))
    thread.daemon = True
    thread.start()

    # 立即更新为运行状态
    task_results[task_id]['status'] = 'running'

    return jsonify({
        'success': True,
        'task_id': task_id,
        'message': '任务已提交，正在执行中...'
    })

@app.route('/api/task_status/<int:task_id>')
def get_task_status(task_id):
    """获取任务状态"""
    if task_id not in task_results:
        return jsonify({'error': '任务不存在'}), 404

    return jsonify(task_results[task_id])

@app.route('/api/task_result/<int:task_id>')
def get_task_result(task_id):
    """获取任务详细结果"""
    if task_id not in task_results:
        return jsonify({'error': '任务不存在'}), 404

    task = task_results[task_id]

    # 查找最新的报告文件
    workspace = Path('workspace/xiaohongshu/generated_content')
    if workspace.exists():
        reports = sorted(workspace.glob('report_*.md'), reverse=True)
        if reports:
            report_content = reports[0].read_text(encoding='utf-8')
            return f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>任务 #{task_id} - 详细报告</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
            max-width: 900px;
            margin: 40px auto;
            padding: 20px;
            line-height: 1.6;
            background: #f5f5f5;
        }}
        .markdown-body {{
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        pre {{
            background: #f6f8fa;
            padding: 16px;
            border-radius: 6px;
            overflow-x: auto;
        }}
        code {{
            background: #f6f8fa;
            padding: 2px 6px;
            border-radius: 3px;
        }}
        h1, h2, h3 {{
            margin-top: 24px;
            margin-bottom: 16px;
        }}
    </style>
</head>
<body>
    <div class="markdown-body">
        <a href="/" style="color: #667eea; text-decoration: none;">← 返回任务列表</a>
        <hr style="margin: 20px 0;">
        {report_content}
    </div>
</body>
</html>
            '''

    return '报告文件未找到', 404

@app.route('/api/tasks')
def list_tasks():
    """列出所有任务"""
    return jsonify(list(task_results.values()))

# ============ 启动服务器 ============
if __name__ == '__main__':
    print()
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "小红书自动化系统" + " " * 27 + "║")
    print("║" + " " * 12 + "🌐 简化版 Web 界面" + " " * 27 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    print("✅ 服务器启动中...")
    print()
    print("📱 访问地址: http://localhost:5000")
    print("📋 功能说明:")
    print("   - 单页面任务输入")
    print("   - 后台自动执行")
    print("   - 实时结果显示")
    print()
    print("按 Ctrl+C 停止服务器")
    print()

    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
