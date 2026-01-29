# 小红书自动化系统 - 使用指南

## 📋 目录

- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [使用方法](#使用方法)
- [数据输出](#数据输出)
- [常见问题](#常见问题)
- [最佳实践](#最佳实践)

---

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 安装浏览器自动化工具（可选）
playwright install
```

### 2. 配置 API

#### 配置 LLM API

编辑 `config/config.toml`：

```toml
[llm]
model = "gpt-4o"  # 或 claude-3.5-sonnet
base_url = "https://api.openai.com/v1"
api_key = "sk-your-api-key-here"
max_tokens = 4096
temperature = 0.0
```

支持的模型：
- OpenAI: GPT-4, GPT-4o
- Anthropic: Claude 3.5 Sonnet
- 其他兼容 OpenAI API 的模型

#### 配置小红书参数

```bash
# 复制示例配置
cp config/xiaohongshu.example.toml config/xiaohongshu.toml

# 编辑配置（可选，使用默认值也行）
# vim config/xiaohongshu.toml
```

### 3. 运行系统

```bash
# 运行完整工作流
python run_xiaohongshu.py

# 或指定参数
python run_xiaohongshu.py --topics 30 --replies 5
```

---

## ⚙️ 配置说明

### 核心参数

| 参数 | 默认值 | 说明 |
|-----|--------|------|
| `target_daily_replies` | 5 | 每天目标回复数 |
| `max_daily_replies` | 10 | 最大回复数（硬限制） |
| `working_hours_start` | 9 | 工作开始时间 |
| `working_hours_end` | 22 | 工作结束时间 |

### 安全参数

| 参数 | 默认值 | 说明 |
|-----|--------|------|
| `enable_safety_limits` | true | 启用安全限制 |
| `random_delay_min` | 300 | 最小延迟（秒） |
| `random_delay_max` | 900 | 最大延迟（秒） |
| `require_human_review` | true | 需要人工审核 |

### 行为模拟

| 参数 | 默认值 | 说明 |
|-----|--------|------|
| `simulate_human_typing` | true | 模拟打字速度 |
| `simulate_reading` | true | 模拟阅读停顿 |
| `random_mouse_movement` | true | 随机鼠标移动 |
| `typing_speed_variance` | 0.3 | 打字速度变化 |

**建议：**
- **Level 2（推荐）**: 保持 `require_human_review = true`
- **Level 3（谨慎）**: 设置 `require_human_review = false`

---

## 📖 使用方法

### 运行模式

#### 1. 完整工作流（推荐）

```bash
python run_xiaohongshu.py
```

**执行流程：**
1. 收集热点（20个）
2. 分析需求
3. 生成回复（5个）
4. 填写到浏览器，等待确认

#### 2. 仅收集热点

```bash
python run_xiaohongshu.py --mode collect
```

**输出：** `workspace/xiaohongshu/hot_topics/hot_topics_YYYYMMDD.json`

#### 3. 收集并分析

```bash
python run_xiaohongshu.py --mode analyze
```

**输出：** `workspace/xiaohongshu/analysis/analysis_YYYYMMDD.jsonl`

#### 4. 生成回复（不发送）

```bash
python run_xiaohongshu.py --mode generate
```

**输出：**
- JSON: `workspace/xiaohongshu/generated_content/replies_YYYYMMDD_HHMMSS.json`
- Markdown: `workspace/xiaohongshu/generated_content/replies_YYYYMMDD_HHMMSS.md`

#### 5. 处理单个帖子

```bash
python run_xiaohongshu.py --mode single --url "https://www.xiaohongshu.com/..."
```

**Level 3（自动发送）:**
```bash
python run_xiaohongshu.py --mode single --url "..." --auto-send
```

⚠️ **警告**: `--auto-send` 会直接发送，不经过确认！

#### 6. 自定义数量

```bash
# 收集 30 个热点，回复 8 条
python run_xiaohongshu.py --topics 30 --replies 8
```

---

## 📂 数据输出

### 目录结构

```
workspace/xiaohongshu/
├── hot_topics/           # 热点数据
│   └── hot_topics_20250129.json
├── analysis/             # 分析结果
│   └── analysis_20250129.jsonl
├── generated_content/    # 生成的内容
│   ├── replies_20250129_143022.json
│   └── replies_20250129_143022.md
└── logs/                 # 日志
    ├── reply_log_20250129.jsonl
    ├── safety_events_20250129.jsonl
    └── daily_report_20250129.md
```

### 输出格式

#### 热点数据 (JSON)

```json
[
  {
    "title": "早C晚A的正确打开方式",
    "content": "最近护肤圈很火的早C晚A...",
    "url": "https://www.xiaohongshu.com/...",
    "likes": 1234,
    "comments": 56,
    "collects": 789,
    "tags": ["护肤", "早C晚A"],
    "collected_at": "2025-01-29T14:30:22"
  }
]
```

#### 分析结果 (JSONL)

```json
{
  "topic": {...},
  "pain_points": ["护肤步骤混乱", "产品搭配不当"],
  "demands": [
    {
      "demand_type": "知识需求",
      "description": "用户需要了解正确的护肤流程",
      "urgency": 8.5,
      "total_score": 8.2
    }
  ],
  "commercial_value": 8.0,
  "priority": 8.3
}
```

#### 回复内容 (Markdown)

```markdown
# 小红书回复内容

## 目标帖子
- **标题**: 早C晚A的正确打开方式
- **链接**: https://www.xiaohongshu.com/...

## 策略
- **角度**: 专业
- **用户痛点**: 护肤步骤混乱,产品搭配不当
- **核心需求**: 用户需要了解正确的护肤流程

## 生成的回复

### 版本 1：【专业】

**评分**: 相关性 9.0 | 吸引力 8.5 | 总分 8.8
**推荐**: ✅ 是

早C晚A的关键在于时间搭配：
早上维C（抗氧化）+ 防晒
晚上维A（修复）+ 保湿

新手建议从低浓度开始...
```

---

## ❓ 常见问题

### Q1: 如何配置 API Key？

**A:** 编辑 `config/config.toml`：

```toml
[llm]
api_key = "your-api-key"
```

支持的模型：
- OpenAI (GPT-4, GPT-4o)
- Anthropic (Claude 3.5 Sonnet)
- 其他兼容 API

### Q2: 浏览器如何登录小红书？

**A:** 系统会打开浏览器，你需要：
1. 手动登录小红书
2. 登录后系统会自动继续

### Q3: 如何调整回复频率？

**A:** 编辑 `config/xiaohongshu.toml`：

```toml
[xiaohongshu]
max_daily_replies = 5           # 每天5条
random_delay_min = 600          # 最少间隔10分钟
random_delay_max = 1800         # 最多间隔30分钟
```

### Q4: 生成的内容在哪里？

**A:** 查看以下目录：
- 热点数据: `workspace/xiaohongshu/hot_topics/`
- 分析结果: `workspace/xiaohongshu/analysis/`
- 生成内容: `workspace/xiaohongshu/generated_content/`

### Q5: 如何升级到 Level 3（自动发送）？

**A:** 编辑配置：

```toml
require_human_review = false  # 关闭人工审核
```

然后使用 `--auto-send` 参数：

```bash
python run_xiaohongshu.py --auto-send
```

⚠️ **注意**: Level 3 风险较高，建议先测试少量数据。

### Q6: 系统被暂停了怎么办？

**A:** 检查日志：
```bash
cat workspace/xiaohongshu/logs/safety_events_*.jsonl
```

可能原因：
- 错误次数过多
- 超过频率限制
- 不在工作时间

---

## 💡 最佳实践

### 1. 从 Level 2 开始

**建议先运行 Level 2（手动确认）2周：**
- 观察内容质量
- 收集用户反馈
- 优化 Prompt
- 建立信任

### 2. 控制频率

**保守策略：**
```toml
max_daily_replies = 3          # 每天3条
random_delay_min = 1800        # 间隔30分钟
random_delay_max = 3600        # 间隔60分钟
```

### 3. 内容质量把关

**人工审核要点：**
- ✅ 内容真实相关
- ✅ 有实际价值
- ✅ 符合小红书风格
- ✅ 无敏感词
- ❌ 不是纯广告
- ❌ 不夸大宣传

### 4. A/B 测试

**测试不同角度：**
- 专业角度（科普）
- 产品角度（推荐）
- 经验角度（分享）
- 情感角度（共鸣）

**追踪效果：**
- 哪个角度互动率高？
- 哪个时间回复效果好？
- 哪类话题更受欢迎？

### 5. 数据驱动优化

**每周分析：**
1. 回顾上周数据
2. 找出高互动回复
3. 总结成功模式
4. 调整策略

### 6. 安全第一

**遵守规则：**
- ✅ 提供真实价值
- ✅ 尊重社区氛围
- ✅ 控制频率
- ❌ 不刷屏
- ❌ 不发垃圾内容
- ❌ 不违规推广

---

## 📊 效果追踪

### 关键指标

| 指标 | 说明 | 目标 |
|-----|------|------|
| 回复成功率 | 成功发送/尝试发送 | > 90% |
| 平均互动率 | 点赞+评论/发送数 | > 20% |
| 内容相关性 | 人工评分 | > 8/10 |
| 账号健康度 | 无警告/无封号 | 100% |

### 优化方向

根据数据调整：
- **互动率低** → 优化内容生成 Prompt
- **相关性低** → 调整需求分析权重
- **成功率低** → 检查浏览器自动化逻辑
- **账号警告** → 立即降低频率

---

## 🆘 获取帮助

### 问题反馈

- GitHub Issues: [提交问题]
- 文档: 查看更多文档
- 日志: 检查 `workspace/xiaohongshu/logs/`

### 调试模式

```bash
# 查看详细日志
python run_xiaohongshu.py --debug

# 测试单个模块
python run_xiaohongshu.py --mode collect --topics 5
```

---

## ⚠️ 免责声明

本系统仅供学习和研究使用。使用本系统进行社交媒体自动化可能：
- 违反平台服务条款
- 导致账号限制或封禁
- 产生法律风险

**使用者需要：**
1. 了解并接受相关风险
2. 遵守平台规则
3. 确保内容质量
4. 承担使用责任

---

**版本**: v1.0.0
**更新**: 2025-01-29
**基于**: OpenManus Framework
