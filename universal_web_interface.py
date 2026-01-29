"""
智能URL分析系统 - 产品化版本
支持任意URL的内容分析和回复生成
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from flask import Flask, render_template, request, jsonify
from threading import Thread
import time
from openai import OpenAI
import requests
from bs4 import BeautifulSoup

# ============ 配置 ============
DEEPSEEK_API_KEY = "sk-b07c9af227fa49b68ff1f6e4ae36465f"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

app = Flask(__name__)

# 存储任务结果
task_results = {}
task_counter = 0

# ============ LLM 类 ============
class SimpleLLM:
    def __init__(self):
        self.client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL
        )

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            max_tokens=3000,
            temperature=0.0
        )

        return response.choices[0].message.content

# ============ URL分析器 ============
class UniversalAnalyzer:
    """通用URL分析器"""

    def __init__(self):
        self.llm = SimpleLLM()

    async def analyze_url(self, url: str, task_type: str = "general", task_description: str = "") -> Dict[str, Any]:
        """分析任意URL"""
        try:
            # 访问URL获取内容
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # 提取基本信息
            title = soup.find('title')
            page_title = title.text.strip() if title else "未知标题"

            # 提取文本内容
            page_text = soup.get_text(separator='\n', strip=True)
            content = page_text[:5000] if len(page_text) > 5000 else page_text

            # 使用AI分析
            result = await self._ai_analyze(page_title, content, url, task_type, task_description)

            return {
                "success": True,
                "title": page_title,
                "url": url,
                "content_length": len(response.text),
                "analysis": result
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def _ai_analyze(self, title: str, content: str, url: str, task_type: str, task_description: str = "") -> Dict[str, Any]:
        """使用AI分析内容"""

        if task_type == "xiaohongshu":
            prompt = f"""请分析这个小红书内容并生成智能回复。

页面标题：{title}
URL：{url}

内容摘要：
{content[:2000]}

请以JSON格式返回：
{{
  "content_type": "内容类型（如：穿搭分享、经验分享、产品推荐等）",
  "key_points": ["关键点1", "关键点2", "关键点3"],
  "user_pain_points": ["用户痛点1", "用户痛点2"],
  "suggested_replies": [
    {{
      "angle": "回复角度",
      "content": "回复内容",
      "score": 9.0
    }}
  ],
  "priority_score": 8.5
}}
"""

        elif task_type == "custom" and task_description:
            prompt = f"""您是一个专业的内容分析助手，请严格按照用户的要求完成任务。

页面标题：{title}
URL：{url}

用户的任务要求：
{task_description}

页面内容（前4000字）：
{content[:4000]}

重要指示：
1. 必须完全按照用户的任务要求去执行，不要做其他无关的分析
2. 如果用户要求提取特定信息，只提取那些信息
3. 如果用户要求总结，就做总结
4. 如果用户要求分析某个方面，就专注分析那个方面
5. 将任务执行结果放在"task_result"字段中

请以JSON格式返回：
{{
  "task_completed": true,
  "task_result": {{
    // 根据用户的具体任务返回相应的结构
    // 如果是提取信息：
    "extracted_data": ["结果1", "结果2", "结果3"],

    // 如果是总结：
    "summary": "总结内容",
    "key_points": ["要点1", "要点2"],

    // 如果是分析：
    "analysis": "分析内容",
    "findings": ["发现1", "发现2"],

    // 请根据实际任务返回最合适的结构
  }},
  "task_description_used": "{task_description[:100]}..."
}}

请确保task_result中的内容完全满足用户的要求。
"""

        else:
            prompt = f"""请分析这个网页内容。

页面标题：{title}
URL：{url}

内容摘要：
{content[:2000]}

请以JSON格式返回：
{{
  "content_type": "内容类型（如：新闻、博客、产品页面、社交媒体等）",
  "main_topic": "主要主题",
  "key_points": ["关键点1", "关键点2", "关键点3"],
  "summary": "100字以内的内容摘要",
  "tags": ["标签1", "标签2", "标签3"]
}}
"""

        try:
            response = self.llm.generate(prompt, "你是智能内容分析专家，擅长根据用户需求完成各类分析任务。")

            # 解析JSON
            if '{' in response and '}' in response:
                json_str = response[response.find('{'):response.rfind('}')+1]
                data = json.loads(json_str)

                # 标记任务类型
                data['task_type'] = task_type
                if task_description:
                    data['task_description'] = task_description

                return data

        except Exception as e:
            print(f"AI分析失败: {e}")

        # 返回基础分析
        return {
            "content_type": "未知",
            "main_topic": title,
            "key_points": [content[:200] + "..."],
            "summary": content[:300],
            "tags": [],
            "task_type": task_type
        }

# ============ 后端任务执行 ============
def run_background_task(task_id, task_config):
    """后台执行任务"""
    try:
        print(f"[任务 {task_id}] 开始执行...")
        print(f"   URL: {task_config.get('url')}")
        print(f"   类型: {task_config.get('task_type')}")

        if task_config.get('task_description'):
            print(f"   任务: {task_config.get('task_description')}")

        analyzer = UniversalAnalyzer()

        # 运行分析
        result = asyncio.run(analyzer.analyze_url(
            task_config.get('url'),
            task_config.get('task_type', 'general'),
            task_config.get('task_description', '')
        ))

        # 更新任务状态
        task_results[task_id]['status'] = 'completed'
        task_results[task_id]['result'] = result
        task_results[task_id]['completed_at'] = datetime.now().isoformat()

        print(f"[任务 {task_id}] 执行完成")

    except Exception as e:
        print(f"[任务 {task_id}] 执行失败: {e}")
        import traceback
        traceback.print_exc()
        task_results[task_id]['status'] = 'failed'
        task_results[task_id]['error'] = str(e)
        task_results[task_id]['completed_at'] = datetime.now().isoformat()

# ============ 路由 ============
@app.route('/')
def index():
    """主页 - 产品化界面"""
    return '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI智能URL分析系统</title>
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
            max-width: 900px;
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
            margin-bottom: 30px;
        }

        .form-group label {
            display: block;
            font-weight: 600;
            margin-bottom: 12px;
            color: #333;
            font-size: 1.05em;
        }

        .form-group input[type="url"],
        .form-group select {
            width: 100%;
            padding: 15px 20px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 1em;
            transition: all 0.3s;
        }

        .form-group input:focus,
        .form-group select:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
        }

        .help-text {
            display: block;
            margin-top: 8px;
            color: #666;
            font-size: 0.9em;
        }

        .btn {
            width: 100%;
            padding: 18px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 1.15em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5);
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
            padding: 25px;
            margin-bottom: 20px;
            border-left: 5px solid #667eea;
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
            font-size: 1.1em;
        }

        .task-status {
            padding: 8px 16px;
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
            line-height: 1.8;
        }

        .result-content {
            margin-top: 20px;
            padding: 20px;
            background: white;
            border-radius: 8px;
        }

        .result-item {
            margin-bottom: 15px;
        }

        .result-label {
            font-weight: 600;
            color: #333;
            margin-bottom: 5px;
        }

        .result-value {
            color: #666;
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

        .examples {
            margin-top: 15px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }

        .examples-title {
            font-weight: 600;
            margin-bottom: 10px;
            color: #333;
        }

        .example-link {
            display: block;
            padding: 8px 12px;
            background: white;
            border-radius: 6px;
            margin-bottom: 8px;
            color: #667eea;
            text-decoration: none;
            transition: all 0.2s;
        }

        .example-link:hover {
            background: #667eea;
            color: white;
            transform: translateX(5px);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI智能URL分析系统</h1>
            <p>输入任意网址，AI自动提取关键信息并生成智能回复</p>
        </div>

        <div class="card">
            <form id="taskForm">
                <div class="form-group">
                    <label for="url">🔗 网页链接（URL）</label>
                    <input type="url" id="url" placeholder="https://..." required>
                    <span class="help-text">支持任意网页链接（小红书、微博、博客、新闻等）</span>

                    <div class="examples">
                        <div class="examples-title">💡 示例链接（点击快速填入）：</div>
                        <a href="#" class="example-link" onclick="setUrl('https://www.xiaohongshu.com/discovery/item/697a9077000000000e00e7fc'); return false;">
                            小红书 - 美国女兵ootd
                        </a>
                        <a href="#" class="example-link" onclick="setUrl('https://www.zhihu.com/question/123456789'); return false;">
                            知乎 - 问答内容
                        </a>
                        <a href="#" class="example-link" onclick="setUrl('https://weibo.com/ttarticle/p/show?id=123456'); return false;">
                            微博 - 热门话题
                        </a>
                    </div>
                </div>

                <div class="form-group">
                    <label for="taskType">🎯 分析类型</label>
                    <select id="taskType" onchange="toggleTaskDescription()">
                        <option value="xiaohongshu">小红书（生成智能回复）</option>
                        <option value="general">通用分析（提取关键信息）</option>
                        <option value="custom">自定义任务</option>
                    </select>
                    <span class="help-text">选择分析类型以获得最佳结果</span>
                </div>

                <div class="form-group" id="taskDescriptionGroup" style="display: none;">
                    <label for="taskDescription">📝 任务描述</label>
                    <textarea id="taskDescription" rows="4" placeholder="请描述您希望AI在这个页面中做什么...&#10;&#10;例如：&#10;- 提取所有产品价格和名称&#10;- 总结文章的核心观点&#10;- 分析页面的商业模式&#10;- 提取联系信息"></textarea>
                    <span class="help-text">详细描述您的需求，AI会根据您的要求进行分析</span>
                </div>

                <button type="submit" class="btn" id="submitBtn">🚀 开始分析</button>
            </form>
        </div>

        <div class="card results-section hidden" id="resultsSection">
            <h2 style="margin-bottom: 20px;">📊 分析结果</h2>
            <div id="taskResults"></div>
        </div>
    </div>

    <script>
        function setUrl(url) {
            document.getElementById('url').value = url;
        }

        function toggleTaskDescription() {
            const taskType = document.getElementById('taskType').value;
            const taskDescGroup = document.getElementById('taskDescriptionGroup');

            if (taskType === 'custom') {
                taskDescGroup.style.display = 'block';
                document.getElementById('taskDescription').required = true;
            } else {
                taskDescGroup.style.display = 'none';
                document.getElementById('taskDescription').required = false;
            }
        }

        document.getElementById('taskForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const submitBtn = document.getElementById('submitBtn');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="loading"></span> 分析中...';

            const taskData = {
                url: document.getElementById('url').value,
                task_type: document.getElementById('taskType').value,
                task_description: document.getElementById('taskDescription').value
            };

            try {
                const response = await fetch('/api/analyze', {
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
                submitBtn.innerHTML = '🚀 开始分析';
            }
        });

        function addTaskCard(taskId, taskData) {
            const resultsDiv = document.getElementById('taskResults');
            const card = document.createElement('div');
            card.className = 'task-card';
            card.id = `task-${taskId}`;

            let typeText = '';
            if (taskData.task_type === 'xiaohongshu') {
                typeText = '小红书智能回复';
            } else if (taskData.task_type === 'general') {
                typeText = '通用分析';
            } else {
                typeText = '自定义任务';
            }

            card.innerHTML = `
                <div class="task-header">
                    <span class="task-id">任务 #${taskId}</span>
                    <span class="task-status status-pending" id="status-${taskId}">
                        <span class="loading"></span> 等待执行
                    </span>
                </div>
                <div class="task-details">
                    <p><strong>🔗 URL:</strong> ${taskData.url}</p>
                    <p><strong>🎯 分析类型:</strong> ${typeText}</p>
                    ${taskData.task_description ? `<p><strong>📝 任务描述:</strong> ${taskData.task_description}</p>` : ''}
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
                        statusEl.innerHTML = '<span class="loading"></span> 分析中...';
                    } else if (data.status === 'completed') {
                        clearInterval(interval);
                        statusEl.className = 'task-status status-completed';
                        statusEl.innerHTML = '✅ 完成';

                        // 显示分析结果
                        displayResult(cardEl, data.result);

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

        function displayResult(cardEl, result) {
            const detailsDiv = cardEl.querySelector('.task-details');

            if (!result.success) {
                detailsDiv.innerHTML += `
                    <hr style="margin: 15px 0; border: none; border-top: 1px solid #ddd;">
                    <p style="color: #dc3545;"><strong>错误:</strong> ${result.error}</p>
                `;
                return;
            }

            const analysis = result.analysis || {};

            let resultHtml = `
                <hr style="margin: 15px 0; border: none; border-top: 1px solid #ddd;">
                <div class="result-content">
                    <div class="result-item">
                        <div class="result-label">📌 页面标题</div>
                        <div class="result-value">${result.title || '未知'}</div>
                    </div>
            `;

            if (analysis.content_type) {
                resultHtml += `
                    <div class="result-item">
                        <div class="result-label">📋 内容类型</div>
                        <div class="result-value">${analysis.content_type}</div>
                    </div>
                `;
            }

            if (analysis.key_points && analysis.key_points.length > 0) {
                resultHtml += `
                    <div class="result-item">
                        <div class="result-label">🔑 关键信息</div>
                        <div class="result-value">
                            <ul style="margin-left: 20px;">
                                ${analysis.key_points.map(point => `<li>${point}</li>`).join('')}
                            </ul>
                        </div>
                    </div>
                `;
            }

            if (analysis.summary) {
                resultHtml += `
                    <div class="result-item">
                        <div class="result-label">📝 内容摘要</div>
                        <div class="result-value">${analysis.summary}</div>
                    </div>
                `;
            }

            if (analysis.user_pain_points && analysis.user_pain_points.length > 0) {
                resultHtml += `
                    <div class="result-item">
                        <div class="result-label">😟 用户痛点</div>
                        <div class="result-value">
                            <ul style="margin-left: 20px;">
                                ${analysis.user_pain_points.map(point => `<li>${point}</li>`).join('')}
                            </ul>
                        </div>
                    </div>
                `;
            }

            if (analysis.suggested_replies && analysis.suggested_replies.length > 0) {
                resultHtml += `
                    <div class="result-item">
                        <div class="result-label">💬 智能回复建议</div>
                        <div class="result-value">
                            ${analysis.suggested_replies.map((reply, idx) => `
                                <div style="padding: 10px; background: #f8f9fa; border-radius: 6px; margin-bottom: 10px;">
                                    <div style="font-weight: 600; color: #667eea;">
                                        版本 ${idx + 1}: ${reply.angle} (评分: ${reply.score}/10)
                                    </div>
                                    <div style="margin-top: 8px;">${reply.content}</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            }

            if (analysis.tags && analysis.tags.length > 0) {
                resultHtml += `
                    <div class="result-item">
                        <div class="result-label">🏷️ 标签</div>
                        <div class="result-value">
                            ${analysis.tags.map(tag => `<span style="display: inline-block; padding: 4px 12px; background: #667eea; color: white; border-radius: 15px; margin-right: 8px; margin-bottom: 8px; font-size: 0.9em;">${tag}</span>`).join('')}
                        </div>
                    </div>
                `;
            }

            // 自定义任务的特定结果显示
            if (analysis.task_result && Object.keys(analysis.task_result).length > 0) {
                resultHtml += `
                    <div class="result-item">
                        <div class="result-label">✅ 任务执行结果</div>
                        <div class="result-value">
                            <div style="padding: 15px; background: #f0f7ff; border-left: 4px solid #667eea; border-radius: 6px;">
                `;

                for (const [key, value] of Object.entries(analysis.task_result)) {
                    if (Array.isArray(value)) {
                        resultHtml += `
                            <div style="margin-bottom: 12px;">
                                <strong>${key}:</strong>
                                <ul style="margin-left: 20px; margin-top: 5px;">
                                    ${value.map(item => `<li>${item}</li>`).join('')}
                                </ul>
                            </div>
                        `;
                    } else if (typeof value === 'string' && value.length > 50) {
                        resultHtml += `
                            <div style="margin-bottom: 12px;">
                                <strong>${key}:</strong>
                                <p style="margin-top: 5px; line-height: 1.6;">${value}</p>
                            </div>
                        `;
                    } else {
                        resultHtml += `
                            <div style="margin-bottom: 8px;">
                                <strong>${key}:</strong> ${value}
                            </div>
                        `;
                    }
                }

                resultHtml += `
                            </div>
                        </div>
                    </div>
                `;
            }

            resultHtml += `
                </div>
                <div style="margin-top: 20px; text-align: center;">
                    <a href="${result.url}" target="_blank" style="display: inline-block; padding: 10px 25px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; border-radius: 8px; font-weight: 600;">
                        🔗 查看原网页
                    </a>
                </div>
            `;

            detailsDiv.innerHTML += resultHtml;
        }
    </script>
</body>
</html>
    '''

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """分析URL"""
    global task_counter
    task_counter += 1
    task_id = task_counter

    data = request.json
    task_config = {
        'url': data.get('url'),
        'task_type': data.get('task_type', 'general'),
        'task_description': data.get('task_description', '')
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
        'message': '任务已提交，正在分析中...'
    })

@app.route('/api/task_status/<int:task_id>')
def get_task_status(task_id):
    """获取任务状态"""
    if task_id not in task_results:
        return jsonify({'error': '任务不存在'}), 404

    return jsonify(task_results[task_id])

@app.route('/api/tasks')
def list_tasks():
    """列出所有任务"""
    return jsonify(list(task_results.values()))

# ============ 启动服务器 ============
if __name__ == '__main__':
    print()
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 12 + "AI智能URL分析系统" + " " * 30 + "║")
    print("║" + " " * 8 + "🚀 产品化版本 - 支持任意URL" + " " * 22 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    print("✅ 服务器启动中...")
    print()
    print("📱 访问地址: http://localhost:5000")
    print("📋 功能说明:")
    print("   - 支持任意网页URL分析")
    print("   - AI自动提取关键信息")
    print("   - 智能生成回复建议")
    print("   - 实时显示分析结果")
    print()
    print("⚠️  按 Ctrl+C 停止服务器")
    print("=" * 60)
    print()

    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
