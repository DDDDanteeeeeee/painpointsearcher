# 小红书热点挖掘与智能回复系统

## 📋 系统概述

基于 OpenManus 框架的小红书自动化系统，实现热点挖掘、需求分析和智能回复功能。

**方案：Level 2 + Level 3 混合**
- Level 2（初始阶段）：智能辅助，自动填写 + 手动发送
- Level 3（稳定后）：半自动化，限制频率 + 人工抽检

---

## 🏗️ 系统架构

### 核心组件

```
┌─────────────────────────────────────────────────────────┐
│                    用户控制层                            │
│  - 启动/停止控制                                         │
│  - 频率设置（每天N条）                                   │
│  - 人工审核确认                                         │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│              XiaohongshuAgent (主控制器)                │
│  - 任务调度                                             │
│  - 流程编排                                             │
│  - 安全控制                                             │
└──────────────────┬──────────────────────────────────────┘
                   │
       ┌───────────┼───────────┐
       │           │           │
       ▼           ▼           ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│热点抓取  │ │需求分析  │ │内容生成  │
│模块      │ │模块      │ │模块      │
└──────────┘ └──────────┘ └──────────┘
       │           │           │
       └───────────┼───────────┘
                   ▼
          ┌─────────────────┐
          │  半自动回复层   │
          │  - 自动填写     │
          │  - 截图预览     │
          │  - 等待确认     │
          └─────────────────┘
```

---

## 🔄 工作流程

### 第一阶段：数据收集与分析

```
1. 启动浏览器（真实 Chrome）
   ↓
2. 访问小红书（使用用户登录状态）
   ↓
3. 浏览热点页面
   - 热搜榜
   - 推荐流
   - 话题页
   ↓
4. 提取热点内容
   - 标题
   - 正文
   - 互动数据（点赞、评论、收藏）
   - 评论区内容
   ↓
5. LLM 分析挖掘
   - 识别用户痛点
   - 挖掘潜在需求
   - 评估商业价值
   - 优先级排序
```

### 第二阶段：内容生成

```
6. 针对高价值热点生成
   - 问题分析
   - 解决方案
   - 评论文案（3-5个版本）
   - 个性化回复内容
   ↓
7. 内容质量检查
   - 相关性评分
   - 吸引力评分
   - 原创性检查
   - 敏感词过滤
```

### 第三阶段：智能回复（半自动）

```
8. 打开目标帖子
   ↓
9. 定位评论框
   ↓
10. 填写回复内容（模拟真实打字）
   ↓
11. 截图预览
   ↓
12. 等待用户确认
   - 用户点击"确认" → 发送
   - 用户点击"修改" → 返回步骤6
   - 用户点击"跳过" → 记录并继续下一个
```

---

## 🛡️ 安全机制

### 1. 频率控制

```python
# 限制规则
MAX_DAILY_REPLIES = 10          # 每天最多10条
MIN_INTERVAL_SECONDS = 3600     # 两条回复最少间隔1小时
RANDOM_DELAY_RANGE = (300, 900) # 随机延迟5-15分钟

# 时间分散
WORKING_HOURS = (9, 22)         # 9:00-22:00（模拟人类作息）
REST_DAYS = []                  # 休息日（可选）
```

### 2. 行为模拟

```python
# 真实人类行为
MOUSE_MOVEMENT = True           # 鼠标移动轨迹（非直线）
TYPING_SPEED_VARIANCE = True    # 打字速度变化
READING_PAUSE = True            # 阅读/思考停顿
SCROLL_PATTERN = "natural"      # 自然滚动模式
```

### 3. 内容质量控制

```python
# 质量标准
MIN_RELEVANCE_SCORE = 0.7       # 最小相关性评分
MIN_ATTRACTIVENESS_SCORE = 0.6  # 最小吸引力评分
DUPLICATE_CONTENT_CHECK = True  # 重复内容检查
SENSITIVE_WORD_FILTER = True    # 敏感词过滤
```

### 4. 异常处理

```python
# 异常情况
CAPTCHA_DETECTED = "pause"      # 验证码 → 暂停
ACCOUNT_WARNING = "stop"        # 账号警告 → 立即停止
NETWORK_ERROR = "retry"         # 网络错误 → 重试（最多3次）
CONTENT_REPORTED = "alert"      # 内容被举报 → 通知用户
```

---

## 📁 项目结构

```
OpenManus-main/
├── app/
│   ├── agent/
│   │   └── xiaohongshu_agent.py    # 小红书主 Agent
│   ├── xiaohongshu/                  # 小红书专用模块
│   │   ├── __init__.py
│   │   ├── config.py                 # 配置管理
│   │   ├── hot_topics.py             # 热点抓取
│   │   ├── demand_analyzer.py        # 需求分析
│   │   ├── content_generator.py      # 内容生成
│   │   ├── auto_replier.py           # 自动回复
│   │   ├── safety_controller.py      # 安全控制
│   │   └── prompts.py                 # Prompt 模板
│   └── tool/                          # 已有工具
├── config/
│   ├── config.example.toml
│   └── xiaohongshu.toml              # 小红书专用配置
├── workspace/
│   └── xiaohongshu/                   # 工作空间
│       ├── hot_topics/                # 热点数据
│       ├── analysis/                  # 分析结果
│       ├── generated_content/         # 生成的内容
│       └── logs/                      # 运行日志
└── run_xiaohongshu.py                 # 启动脚本
```

---

## 🚀 使用流程

### 初始化（第一次）

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 API
cp config/config.example.toml config/config.toml
# 编辑 config/config.toml 添加 API Key

# 3. 配置小红书
cp config/xiaohongshu.example.toml config/xiaohongshu.toml
# 编辑 config/xiaohongshu.toml 设置参数

# 4. 启动系统
python run_xiaohongshu.py
```

### 日常使用

```bash
# 启动（自动开始任务）
python run_xiaohongshu.py

# 或指定任务
python run_xiaohongshu.py --task "collect_hot_topics"
python run_xiaohongshu.py --task "analyze_and_reply"
```

---

## 📊 数据输出格式

### 分析报告示例

```markdown
# 小红书热点分析报告 - 2025-01-29

## 今日热点 TOP 10

1. 【护肤】早C晚A的正确打开方式... (🔥热度: 9.8/10)
   - 潜力需求: ⭐⭐⭐⭐⭐
   - 用户痛点: 护肤步骤混乱、产品搭配不当
   - 商业价值: 高（护肤产品推荐）
   - 建议回复数: 3-5条

## 推荐回复策略

### 热点 #1: 早C晚A
目标帖子: [链接]
推荐回复角度:
- 专业角度：护肤科普
- 产品角度：推荐搭配
- 个人经验：真实分享

生成内容: 见附件 reply_001.md
```

---

## ⚙️ 配置参数

### `config/xiaohongshu.toml`

```toml
[xiaohongshu]
# 目标设置
target_daily_replies = 5              # 每天目标回复数
max_daily_replies = 10               # 最大回复数
working_hours_start = 9              # 开始时间
working_hours_end = 22               # 结束时间

# 内容质量
min_relevance_score = 0.7            # 最小相关性
min_attractiveness_score = 0.6       # 最小吸引力
require_human_review = true          # 需要人工审核

# 安全设置
enable_safety_limits = true          # 启用安全限制
random_delay_min = 300               # 最小延迟（秒）
random_delay_max = 900               # 最大延迟（秒）

# 行为模拟
simulate_human_typing = true         # 模拟打字
simulate_reading = true              # 模拟阅读
random_mouse_movement = true         # 随机鼠标移动

# 数据保存
save_analysis_report = true          # 保存分析报告
save_generated_content = true        # 保存生成内容
save_reply_logs = true               # 保存回复日志
```

---

## 🎯 分阶段实施计划

### Phase 1: 基础功能（Week 1）
- ✅ 热点抓取模块
- ✅ 需求分析模块
- ✅ 内容生成模块
- ✅ 配置系统

### Phase 2: 智能回复（Week 2）
- ✅ 半自动回复机制
- ✅ 浏览器自动化集成
- ✅ 安全控制机制

### Phase 3: 优化提升（Week 3+）
- ✅ A/B 测试
- ✅ 效果追踪
- ✅ 模型优化
- ✅ 策略调整

---

## ⚠️ 免责声明

本系统仅供学习和研究使用。使用本系统进行社交媒体自动化可能违反平台服务条款，请：
1. 遵守小红书社区规范
2. 确保内容质量真实有价值
3. 控制频率避免被判定为垃圾行为
4. 承担使用风险

---

## 📞 技术支持

- GitHub Issues: [提交问题]
- 文档: [详细文档]
- 演示视频: [待添加]

---

**版本**: v1.0.0
**最后更新**: 2025-01-29
**基于**: OpenManus Framework
