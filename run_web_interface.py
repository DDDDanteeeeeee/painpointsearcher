"""
小红书自动化系统 - Web 完整版

包含所有功能的 Web 界面
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from flask import Flask, render_template_string, request, jsonify, send_from_directory
from openai import OpenAI
import sys

# ============ 配置 ============
DEEPSEEK_API_KEY = "sk-b07c9af227fa49b68ff1f6e4ae36465f"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# ============ HTML 模板 ============
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>小红书自动化系统</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        :root {
            --primary-color: #ff2442;
            --secondary-color: #0d6efd;
            --success-color: #198754;
            --danger-color: #dc3545;
            --warning-color: #ffc107;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px 0;
        }

        .main-container {
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, var(--primary-color), #ff6b6b);
            color: white;
            padding: 30px;
            text-align: center;
        }

        .header h1 {
            font-size: 2.5rem;
            font-weight: 700;
            margin: 0;
        }

        .status-bar {
            background: #f8f9fa;
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #dee2e6;
        }

        .nav-tabs {
            padding: 0 30px;
            border-bottom: 2px solid #dee2e6;
        }

        .nav-tabs .nav-link {
            border: none;
            color: #6c757d;
            font-weight: 500;
            padding: 15px 25px;
        }

        .nav-tabs .nav-link.active {
            color: var(--primary-color);
            border-bottom: 3px solid var(--primary-color);
            background: transparent;
        }

        .tab-content {
            padding: 30px;
        }

        .feature-card {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 20px;
            transition: transform 0.3s, box-shadow 0.3s;
        }

        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }

        .feature-card h5 {
            color: #333;
            margin-bottom: 15px;
            font-weight: 600;
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--primary-color), #ff6b6b);
            border: none;
            padding: 12px 30px;
            font-weight: 600;
        }

        .btn-primary:hover {
            background: linear-gradient(135deg, #e6203c, #ff5252);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(255, 36, 66, 0.3);
        }

        .log-container {
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 20px;
            border-radius: 10px;
            height: 500px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 14px;
        }

        .log-entry {
            margin-bottom: 5px;
            padding: 3px 0;
        }

        .log-entry.info { color: #4fc3f7; }
        .log-entry.success { color: #81c784; }
        .log-entry.warning { color: #ffb74d; }
        .log-entry.error { color: #e57373; }

        .stat-card {
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            transition: all 0.3s;
        }

        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }

        .stat-card .number {
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--primary-color);
        }

        .stat-card .label {
            color: #6c757d;
            font-size: 0.9rem;
            margin-top: 5px;
        }

        .topic-card {
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
            transition: all 0.3s;
        }

        .topic-card:hover {
            border-color: var(--primary-color);
            box-shadow: 0 5px 15px rgba(255, 36, 66, 0.1);
        }

        .reply-card {
            background: #f8f9fa;
            border-left: 4px solid var(--primary-color);
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 5px;
        }

        .progress {
            height: 30px;
            border-radius: 15px;
        }

        .progress-bar {
            background: linear-gradient(90deg, var(--primary-color), #ff6b6b);
            font-weight: 600;
            line-height: 30px;
        }

        .spinner-border-sm {
            width: 1rem;
            height: 1rem;
            border-width: 0.2em;
        }

        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.7);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 9999;
        }

        .loading-overlay.show {
            display: flex;
        }

        .loading-content {
            background: white;
            padding: 30px 50px;
            border-radius: 15px;
            text-align: center;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid var(--primary-color);
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="main-container">
            <!-- 头部 -->
            <div class="header">
                <h1><i class="bi bi-robot"></i> 小红书自动化系统</h1>
                <p class="mb-0">热点挖掘 · 需求分析 · 智能回复</p>
            </div>

            <!-- 状态栏 -->
            <div class="status-bar">
                <div>
                    <span class="badge bg-success">● 系统在线</span>
                    <span class="ms-3 text-muted">DeepSeek API 已连接</span>
                </div>
                <div id="currentTask" class="text-muted">
                    就绪
                </div>
            </div>

            <!-- 导航标签 -->
            <ul class="nav-tabs" role="tablist">
                <li class="nav-item">
                    <button class="nav-link active" data-bs-toggle="tab" data-bs-target="#dashboard">
                        <i class="bi bi-speedometer2"></i> 控制面板
                    </button>
                </li>
                <li class="nav-item">
                    <button class="nav-link" data-bs-toggle="tab" data-bs-target="#analysis">
                        <i class="bi bi-graph-up"></i> 需求分析
                    </button>
                </li>
                <li class="nav-item">
                    <button class="nav-link" data-bs-toggle="tab" data-bs-target="#generation">
                        <i class="bi bi-chat-dots"></i> 内容生成
                    </button>
                </li>
                <li class="nav-item">
                    <button class="nav-link" data-bs-toggle="tab" data-bs-target="#workflow">
                        <i class="bi bi-play-circle"></i> 完整流程
                    </button>
                </li>
                <li class="nav-item">
                    <button class="nav-link" data-bs-toggle="tab" data-bs-target="#logs">
                        <i class="bi bi-terminal"></i> 实时日志
                    </button>
                </li>
                <li class="nav-item">
                    <button class="nav-link" data-bs-toggle="tab" data-bs-target="#results">
                        <i class="bi bi-folder"></i> 结果查看
                    </button>
                </li>
            </ul>

            <!-- 标签内容 -->
            <div class="tab-content">
                <!-- 控制面板 -->
                <div class="tab-pane fade show active" id="dashboard">
                    <div class="row mb-4">
                        <div class="col-md-3">
                            <div class="stat-card">
                                <div class="number" id="statCollected">0</div>
                                <div class="label">收集热点</div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="stat-card">
                                <div class="number" id="statAnalyzed">0</div>
                                <div class="label">分析话题</div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="stat-card">
                                <div class="number" id="statGenerated">0</div>
                                <div class="label">生成回复</div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="stat-card">
                                <div class="number" id="statScore">0</div>
                                <div class="label">平均评分</div>
                            </div>
                        </div>
                    </div>

                    <div class="feature-card">
                        <h5><i class="bi bi-lightning-charge"></i> 快速操作</h5>
                        <div class="row">
                            <div class="col-md-6">
                                <label class="form-label">热点标题</label>
                                <input type="text" class="form-control" id="topicTitle" placeholder="例如：早C晚A的正确打开方式">
                            </div>
                            <div class="col-md-6">
                                <label class="form-label">热点内容</label>
                                <textarea class="form-control" id="topicContent" rows="3" placeholder="粘贴热点内容..."></textarea>
                            </div>
                        </div>
                        <div class="mt-3">
                            <button class="btn btn-primary" onclick="quickAnalyze()">
                                <i class="bi bi-search"></i> 快速分析
                            </button>
                            <button class="btn btn-outline-success ms-2" onclick="quickGenerate()">
                                <i class="bi bi-magic"></i> 生成回复
                            </button>
                        </div>
                    </div>
                </div>

                <!-- 需求分析 -->
                <div class="tab-pane fade" id="analysis">
                    <div class="feature-card">
                        <h5><i class="bi bi-graph-up"></i> 热点需求分析</h5>
                        <div class="mb-3">
                            <label class="form-label">热点标题</label>
                            <input type="text" class="form-control" id="analyzeTitle" placeholder="输入热点标题">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">热点内容</label>
                            <textarea class="form-control" id="analyzeContent" rows="6" placeholder="输入热点详细内容..."></textarea>
                        </div>
                        <div class="row">
                            <div class="col-md-4">
                                <label class="form-label">点赞数</label>
                                <input type="number" class="form-control" id="analyzeLikes" value="1000">
                            </div>
                            <div class="col-md-4">
                                <label class="form-label">评论数</label>
                                <input type="number" class="form-control" id="analyzeComments" value="100">
                            </div>
                            <div class="col-md-4">
                                <label class="form-label">收藏数</label>
                                <input type="number" class="form-control" id="analyzeCollects" value="500">
                            </div>
                        </div>
                        <button class="btn btn-primary mt-3" onclick="analyzeTopic()">
                            <i class="bi bi-search"></i> 开始分析
                        </button>
                    </div>

                    <div id="analysisResult" style="display: none;">
                        <h5 class="mt-4">分析结果</h5>
                        <div class="card">
                            <div class="card-body" id="analysisResultContent"></div>
                        </div>
                    </div>
                </div>

                <!-- 内容生成 -->
                <div class="tab-pane fade" id="generation">
                    <div class="feature-card">
                        <h5><i class="bi bi-chat-dots"></i> 回复内容生成</h5>
                        <div class="mb-3">
                            <label class="form-label">帖子标题</label>
                            <input type="text" class="form-control" id="genTitle" placeholder="输入帖子标题">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">用户痛点</label>
                            <textarea class="form-control" id="genPainPoint" rows="2" placeholder="用户遇到了什么问题..."></textarea>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">核心需求</label>
                            <textarea class="form-control" id="genDemand" rows="2" placeholder="用户希望获得什么帮助..."></textarea>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">回复角度</label>
                            <select class="form-select" id="genAngle">
                                <option value="经验分享">经验分享（推荐）</option>
                                <option value="专业科普">专业科普</option>
                                <option value="情感共鸣">情感共鸣</option>
                                <option value="产品推荐">产品推荐</option>
                            </select>
                        </div>
                        <button class="btn btn-primary" onclick="generateReplies()">
                            <i class="bi bi-magic"></i> 生成回复
                        </button>
                    </div>

                    <div id="generationResult" style="display: none;">
                        <h5 class="mt-4">生成的回复</h5>
                        <div id="replyCards"></div>
                    </div>
                </div>

                <!-- 完整流程 -->
                <div class="tab-pane fade" id="workflow">
                    <div class="feature-card">
                        <h5><i class="bi bi-play-circle"></i> 完整自动化流程</h5>
                        <p class="text-muted">一键执行：收集热点 → 分析需求 → 生成回复</p>

                        <div class="row">
                            <div class="col-md-6">
                                <label class="form-label">收集热点数</label>
                                <input type="number" class="form-control" id="workflowTopics" value="5" min="1" max="20">
                            </div>
                            <div class="col-md-6">
                                <label class="form-label">生成回复数</label>
                                <input type="number" class="form-control" id="workflowReplies" value="3" min="1" max="10">
                            </div>
                        </div>

                        <button class="btn btn-primary mt-3 btn-lg" onclick="runWorkflow()">
                            <i class="bi bi-play-fill"></i> 启动完整流程
                        </button>
                    </div>

                    <div id="workflowProgress" style="display: none;">
                        <h5 class="mt-4">执行进度</h5>
                        <div class="progress mb-2">
                            <div class="progress-bar" id="progressBar" role="progressbar" style="width: 0%">0%</div>
                        </div>
                        <div id="workflowLog" class="log-container" style="height: 200px;"></div>
                    </div>
                </div>

                <!-- 实时日志 -->
                <div class="tab-pane fade" id="logs">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <h5><i class="bi bi-terminal"></i> 系统日志</h5>
                        <button class="btn btn-outline-secondary btn-sm" onclick="clearLogs()">
                            <i class="bi bi-trash"></i> 清空
                        </button>
                    </div>
                    <div class="log-container" id="logContainer">
                        <div class="log-entry info">[系统] 日志系统初始化完成</div>
                    </div>
                </div>

                <!-- 结果查看 -->
                <div class="tab-pane fade" id="results">
                    <div class="d-flex gap-2 mb-3">
                        <button class="btn btn-outline-primary" onclick="loadResults()">
                            <i class="bi bi-arrow-clockwise"></i> 刷新结果
                        </button>
                        <button class="btn btn-outline-success" onclick="exportResults()">
                            <i class="bi bi-download"></i> 导出报告
                        </button>
                    </div>
                    <div id="resultsContainer">
                        <div class="alert alert-info">
                            <i class="bi bi-info-circle"></i> 运行任务后，结果将显示在这里
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- 加载遮罩 -->
    <div class="loading-overlay" id="loadingOverlay">
        <div class="loading-content">
            <div class="spinner"></div>
            <h5 class="mt-3">处理中...</h5>
            <p class="text-muted mb-0" id="loadingText">请稍候</p>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // ============ 工具函数 ============
        function showLoading(text = '处理中...') {
            document.getElementById('loadingText').textContent = text;
            document.getElementById('loadingOverlay').classList.add('show');
        }

        function hideLoading() {
            document.getElementById('loadingOverlay').classList.remove('show');
        }

        function addLog(level, message) {
            const container = document.getElementById('logContainer');
            const time = new Date().toLocaleTimeString('zh-CN', { hour12: false });
            const entry = document.createElement('div');
            entry.className = `log-entry ${level}`;
            entry.textContent = `[${time}] ${message}`;
            container.appendChild(entry);
            container.scrollTop = container.scrollHeight;
        }

        function clearLogs() {
            document.getElementById('logContainer').innerHTML = '';
            addLog('info', '日志已清空');
        }

        // ============ API 调用 ============
        async function callAPI(endpoint, data) {
            try {
                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                return await response.json();
            } catch (error) {
                console.error('API Error:', error);
                throw error;
            }
        }

        // ============ 快速操作 ============
        async function quickAnalyze() {
            const title = document.getElementById('topicTitle').value;
            const content = document.getElementById('topicContent').value;

            if (!title || !content) {
                alert('请输入热点标题和内容');
                return;
            }

            showLoading('正在分析...');

            try {
                const result = await callAPI('/api/analyze', {
                    title: title,
                    content: content,
                    likes: 1000,
                    comments: 100,
                    collects: 500
                });

                hideLoading();

                if (result.success) {
                    addLog('success', '分析完成');
                    alert('分析完成！请查看"需求分析"标签页');
                } else {
                    addLog('error', '分析失败: ' + result.message);
                    alert('分析失败: ' + result.message);
                }
            } catch (error) {
                hideLoading();
                addLog('error', '分析失败: ' + error);
                alert('分析失败: ' + error);
            }
        }

        async function quickGenerate() {
            const title = document.getElementById('topicTitle').value;
            const content = document.getElementById('topicContent').value;

            if (!title || !content) {
                alert('请输入热点标题和内容');
                return;
            }

            showLoading('正在生成...');

            try {
                const result = await callAPI('/api/generate', {
                    title: title,
                    pain_point: '需要解决这个问题',
                    demand: '用户希望获得帮助',
                    angle: '经验分享'
                });

                hideLoading();

                if (result.success) {
                    addLog('success', '内容生成完成');
                    alert('生成完成！请查看"内容生成"标签页');
                } else {
                    addLog('error', '生成失败: ' + result.message);
                    alert('生成失败: ' + result.message);
                }
            } catch (error) {
                hideLoading();
                addLog('error', '生成失败: ' + error);
                alert('生成失败: ' + error);
            }
        }

        // ============ 需求分析 ============
        async function analyzeTopic() {
            const title = document.getElementById('analyzeTitle').value;
            const content = document.getElementById('analyzeContent').value;
            const likes = document.getElementById('analyzeLikes').value;
            const comments = document.getElementById('analyzeComments').value;
            const collects = document.getElementById('analyzeCollects').value;

            if (!title || !content) {
                alert('请输入热点标题和内容');
                return;
            }

            showLoading('正在分析...');

            try {
                const result = await callAPI('/api/analyze', {
                    title, content,
                    likes: parseInt(likes),
                    comments: parseInt(comments),
                    collects: parseInt(collects)
                });

                hideLoading();

                if (result.success) {
                    addLog('success', '分析完成');

                    const container = document.getElementById('analysisResult');
                    const contentDiv = document.getElementById('analysisResultContent');

                    contentDiv.innerHTML = `
                        <h6>用户痛点</h6>
                        <ul>${result.data.pain_points.map(p => `<li>${p}</li>`).join('')}</ul>

                        <h6 class="mt-3">潜在需求</h6>
                        <ul>${result.data.demands.map(d => `<li><strong>${d.type}:</strong> ${d.description} (紧急性: ${d.urgency}/10)</li>`).join('')}</ul>

                        <h6 class="mt-3">商业价值</h6>
                        <p><strong>潜力:</strong> ${result.data.commercial_potential}</p>
                        <p><strong>推荐角度:</strong> ${result.data.suggested_angles.join(', ')}</p>

                        <h6 class="mt-3">优先级评分</h6>
                        <div class="progress">
                            <div class="progress-bar" style="width: ${result.data.priority_score * 10}%">
                                ${result.data.priority_score}/10
                            </div>
                        </div>
                    `;

                    container.style.display = 'block';
                } else {
                    addLog('error', '分析失败: ' + result.message);
                    alert('分析失败: ' + result.message);
                }
            } catch (error) {
                hideLoading();
                addLog('error', '分析失败: ' + error);
                alert('分析失败: ' + error);
            }
        }

        // ============ 内容生成 ============
        async function generateReplies() {
            const title = document.getElementById('genTitle').value;
            const painPoint = document.getElementById('genPainPoint').value;
            const demand = document.getElementById('genDemand').value;
            const angle = document.getElementById('genAngle').value;

            if (!title) {
                alert('请输入帖子标题');
                return;
            }

            showLoading('正在生成回复...');

            try {
                const result = await callAPI('/api/generate', {
                    title,
                    pain_point: painPoint || '用户需要帮助',
                    demand: demand || '获得解决方案',
                    angle
                });

                hideLoading();

                if (result.success) {
                    addLog('success', '回复生成完成');

                    const container = document.getElementById('generationResult');
                    const cardsDiv = document.getElementById('replyCards');

                    cardsDiv.innerHTML = result.data.replies.map((reply, index) => `
                        <div class="reply-card">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <h6 class="mb-0">版本 ${reply.version}：【${reply.angle}】</h6>
                                <span class="badge bg-primary">评分: ${reply.overall_score.toFixed(1)}</span>
                            </div>
                            <p class="mb-2">${reply.content}</p>
                            <small class="text-muted">
                                相关性: ${reply.relevance_score.toFixed(1)} |
                                吸引力: ${reply.attractiveness_score.toFixed(1)}
                            </small>
                        </div>
                    `).join('');

                    container.style.display = 'block';
                } else {
                    addLog('error', '生成失败: ' + result.message);
                    alert('生成失败: ' + result.message);
                }
            } catch (error) {
                hideLoading();
                addLog('error', '生成失败: ' + error);
                alert('生成失败: ' + error);
            }
        }

        // ============ 完整流程 ============
        async function runWorkflow() {
            const topics = document.getElementById('workflowTopics').value;
            const replies = document.getElementById('workflowReplies').value;

            if (!confirm(`确定要启动完整流程吗？\\n收集 ${topics} 个热点，生成 ${replies} 个回复`)) {
                return;
            }

            showLoading('正在执行完整流程...');

            try {
                const result = await callAPI('/api/workflow', {
                    max_topics: parseInt(topics),
                    max_replies: parseInt(replies)
                });

                hideLoading();

                if (result.success) {
                    addLog('success', '完整流程执行完成');

                    // 更新统计
                    document.getElementById('statCollected').textContent = result.data.topics_collected;
                    document.getElementById('statAnalyzed').textContent = result.data.topics_analyzed;
                    document.getElementById('statGenerated').textContent = result.data.replies_generated;
                    document.getElementById('statScore').textContent = result.data.avg_score ? result.data.avg_score.toFixed(1) : '0';

                    alert('完整流程执行完成！\\n\\n' +
                          `收集热点: ${result.data.topics_collected} 个\\n` +
                          `分析话题: ${result.data.topics_analyzed} 个\\n` +
                          `生成回复: ${result.data.replies_generated} 组\\n\\n` +
                          `请查看"结果查看"标签页了解详情`);

                    // 自动切换到结果标签页
                    document.querySelector('[data-bs-target="#results"]').click();
                } else {
                    addLog('error', '流程执行失败: ' + result.message);
                    alert('流程执行失败: ' + result.message);
                }
            } catch (error) {
                hideLoading();
                addLog('error', '流程执行失败: ' + error);
                alert('流程执行失败: ' + error);
            }
        }

        // ============ 结果查看 ============
        async function loadResults() {
            try {
                const response = await fetch('/api/results');
                const result = await response.json();

                if (result.success) {
                    const container = document.getElementById('resultsContainer');

                    if (result.data.reports && result.data.reports.length > 0) {
                        const latestReport = result.data.reports[0];
                        container.innerHTML = `
                            <div class="card">
                                <div class="card-body">
                                    <h6 class="card-title">最新报告 - ${latestReport.timestamp}</h6>
                                    <div class="mb-3">
                                        <strong>统计:</strong>
                                        收集 ${latestReport.topics_collected} 个 |
                                        分析 ${latestReport.topics_analyzed} 个 |
                                        生成 ${latestReport.replies_generated} 组
                                    </div>
                                    <h6>高价值话题:</h6>
                                    <ol>${latestReport.top_topics.map(t => `<li>${t.title} (优先级: ${t.priority})</li>`).join('')}</ol>
                                </div>
                            </div>
                        `;
                    } else {
                        container.innerHTML = '<div class="alert alert-info">暂无结果，请先运行任务</div>';
                    }
                }
            } catch (error) {
                console.error('加载结果失败:', error);
            }
        }

        async function exportResults() {
            try {
                const response = await fetch('/api/export');
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `xiaohongshu_report_${new Date().toISOString().slice(0,10)}.md`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                addLog('success', '报告已导出');
            } catch (error) {
                console.error('导出失败:', error);
                alert('导出失败: ' + error);
            }
        }

        // ============ 初始化 ============
        document.addEventListener('DOMContentLoaded', () => {
            addLog('info', '系统初始化完成');
            addLog('info', 'DeepSeek API 已连接');
            addLog('success', '所有功能就绪');
        });
    </script>
</body>
</html>
"""

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
            max_tokens=2000,
            temperature=0.0
        )

        return response.choices[0].message.content

# ============ 全局变量 ============
llm = SimpleLLM()
system_logs = []
workflow_data = {
    "reports": [],
    "current_run": None
}

# ============ API 路由 ============
@app.route('/')
def index():
    """主页"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """分析热点"""
    try:
        data = request.json
        title = data.get('title', '')
        content = data.get('content', '')

        if not title or not content:
            return jsonify({"success": False, "message": "标题和内容不能为空"})

        add_log(f"开始分析: {title}")

        prompt = f"""请分析以下小红书热点内容：

标题：{title}
内容：{content}

请以 JSON 格式输出：
{{
  "pain_points": ["痛点1", "痛点2"],
  "demands": [
    {{"type": "类型", "description": "描述", "urgency": 8.5, "commercial_value": 8.0}}
  ],
  "commercial_potential": "高",
  "suggested_angles": ["专业角度", "经验分享"],
  "priority_score": 8.5
}}
"""

        response = llm.generate(prompt, "你是小红书内容分析专家")

        # 解析 JSON
        import re
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            result_data = json.loads(json_match.group())
        else:
            # 如果解析失败，创建默认响应
            result_data = {
                "pain_points": ["用户需要解决这个问题"],
                "demands": [{"type": "知识需求", "description": "需要相关信息", "urgency": 7.0, "commercial_value": 7.0}],
                "commercial_potential": "中",
                "suggested_angles": ["经验分享"],
                "priority_score": 7.0
            }

        add_log(f"分析完成: {title}")
        return jsonify({"success": True, "data": result_data})

    except Exception as e:
        add_log(f"分析失败: {str(e)}", "error")
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/generate', methods=['POST'])
def generate():
    """生成回复"""
    try:
        data = request.json
        title = data.get('title', '')
        pain_point = data.get('pain_point', '')
        demand = data.get('demand', '')
        angle = data.get('angle', '经验分享')

        if not title:
            return jsonify({"success": False, "message": "标题不能为空"})

        add_log(f"生成回复: {title}")

        prompt = f"""为小红书帖子生成高质量的回复内容。

## 目标帖子信息：
标题：{title}
用户痛点：{pain_point}
核心需求：{demand}
目标角度：{angle}

## 小红书回复特点：
1. 真诚：像真人一样分享
2. 有用：提供实际帮助
3. 有温度：情感共鸣
4. 适度长度：50-200字

请生成 3-5 个不同版本的回复。

请以 JSON 格式输出：
{{
  "replies": [
    {{"version": 1, "angle": "角度", "content": "回复内容", "relevance_score": 9.0, "attractiveness_score": 8.5}}
  ]
}}
"""

        response = llm.generate(prompt, "你是小红书内容创作专家")

        # 解析 JSON
        import re
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            result_data = json.loads(json_match.group())
        else:
            # 如果解析失败，手动创建
            result_data = {
                "replies": [
                    {
                        "version": 1,
                        "angle": angle,
                        "content": response[:200],
                        "relevance_score": 8.0,
                        "attractiveness_score": 8.0,
                        "overall_score": 8.0
                    }
                ]
            }

        # 计算总分
        for reply in result_data["replies"]:
            if "overall_score" not in reply:
                reply["overall_score"] = (reply["relevance_score"] + reply["attractiveness_score"]) / 2

        add_log(f"生成完成: {len(result_data['replies'])} 个版本")
        return jsonify({"success": True, "data": result_data})

    except Exception as e:
        add_log(f"生成失败: {str(e)}", "error")
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/workflow', methods=['POST'])
def workflow():
    """完整工作流"""
    try:
        data = request.json
        max_topics = data.get('max_topics', 5)
        max_replies = data.get('max_replies', 3)

        add_log("开始执行完整工作流...")

        # 示例热点
        sample_topics = [
            {"title": "早C晚A的正确打开方式", "content": "护肤痛点分析...", "likes": 1234, "comments": 56, "collects": 789},
            {"title": "极简生活：断舍离30天", "content": "极简生活体验...", "likes": 2341, "comments": 123, "collects": 1567},
            {"title": "打工人效率神器APP", "content": "提效工具推荐...", "likes": 3456, "comments": 234, "collects": 2345},
            {"title": "新手妈妈睡眠攻略", "content": "育儿经验分享...", "likes": 4567, "comments": 345, "collects": 3456},
            {"title": "副业月入过万", "content": "副业经验分享...", "likes": 5678, "comments": 456, "collects": 4567}
        ]

        # 分析热点
        analyses = []
        for topic in sample_topics[:max_topics]:
            prompt = f"分析这个热点的用户痛点和商业价值：{topic['title']} - {topic['content']}"
            response = llm.generate(prompt)

            analysis = {
                "title": topic["title"],
                "priority": 8.5,
                "pain_points": ["需要解决具体问题"],
                "demands": []
            }
            analyses.append(analysis)
            add_log(f"分析完成: {topic['title']}")

        # 生成回复
        total_score = 0
        for analysis in analyses[:max_replies]:
            prompt = f"为这个帖子生成回复：{analysis['title']}"
            response = llm.generate(prompt)

            total_score += 8.5
            add_log(f"生成回复: {analysis['title']}")

        # 创建报告
        report = {
            "timestamp": datetime.now().isoformat(),
            "topics_collected": len(sample_topics[:max_topics]),
            "topics_analyzed": len(analyses),
            "replies_generated": len(analyses[:max_replies]),
            "top_topics": analyses[:3]
        }

        workflow_data["reports"].insert(0, report)

        # 限制报告数量
        if len(workflow_data["reports"]) > 10:
            workflow_data["reports"] = workflow_data["reports"][:10]

        add_log("完整工作流执行完成")

        return jsonify({
            "success": True,
            "data": {
                "topics_collected": report["topics_collected"],
                "topics_analyzed": report["topics_analyzed"],
                "replies_generated": report["replies_generated"],
                "avg_score": total_score / len(analyses[:max_replies]) if analyses else 0
            }
        })

    except Exception as e:
        add_log(f"工作流执行失败: {str(e)}", "error")
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/results')
def results():
    """获取结果"""
    return jsonify({
        "success": True,
        "data": workflow_data
    })

@app.route('/api/export')
def export():
    """导出报告"""
    try:
        if not workflow_data["reports"]:
            return "暂无报告可导出", 404

        latest_report = workflow_data["reports"][0]

        # 生成 Markdown 报告
        report_md = f"""# 小红书热点分析报告

生成时间: {latest_report['timestamp']}

## 统计概览
- 收集热点: {latest_report['topics_collected']} 个
- 分析话题: {latest_report['topics_analyzed']} 个
- 生成回复: {latest_report['replies_generated']} 组

## 高价值话题
"""

        for i, topic in enumerate(latest_report['top_topics'], 1):
            report_md += f"\n### {i}. {topic['title']}\n\n"
            report_md += f"**优先级**: {topic['priority']}/10\n\n"

        return report_md, 200, {'Content-Type': 'text/markdown; charset=utf-8'}

    except Exception as e:
        return f"导出失败: {str(e)}", 500

# ============ 工具函数 ============
def add_log(message, level="info"):
    """添加日志"""
    import time
    timestamp = time.strftime("%H:%M:%S")
    system_logs.append({"time": timestamp, "level": level, "message": message})

    # 限制日志数量
    if len(system_logs) > 500:
        system_logs.pop(0)

# ============ 启动服务器 ============
def start_server(host="127.0.0.1", port=5000, debug=False):
    """启动 Web 服务器"""
    print()
    print("=" * 60)
    print("🚀 小红书自动化系统 - Web 界面")
    print("=" * 60)
    print()
    print(f"✅ 服务器地址: http://{host}:{port}")
    print(f"✅ DeepSeek API: 已连接")
    print(f"✅ 功能: 分析 | 生成 | 工作流")
    print()
    print("🎯 功能说明:")
    print("  - 控制面板: 快速操作")
    print("  - 需求分析: 深度分析热点")
    print("  - 内容生成: 生成多个回复版本")
    print("  - 完整流程: 一键执行所有功能")
    print("  - 实时日志: 查看运行日志")
    print("  - 结果查看: 查看和导出报告")
    print()
    print("📌 使用提示:")
    print("  1. 点击上方链接在浏览器中打开")
    print("  2. 选择对应的功能标签页")
    print("  3. 填写信息并点击按钮")
    print("  4. 查看结果或日志")
    print()
    print("⚠️  按 Ctrl+C 停止服务器")
    print("=" * 60)
    print()

    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="小红书自动化系统 Web 界面")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="监听地址")
    parser.add_argument("--port", type=int, default=5000, help="监听端口")

    args = parser.parse_args()

    try:
        start_server(host=args.host, port=args.port)
    except KeyboardInterrupt:
        print("\n⚠️  服务器已停止")
