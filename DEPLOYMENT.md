# 🚀 AI智能URL分析系统 - 部署指南

## ⚠️ 重要提示

**Netlify 不支持Flask后端应用！** Netlify主要用于静态网站（HTML/CSS/JS）。

您的应用是Python Flask后端，需要使用支持Python的平台。

---

## ✅ 推荐部署平台

### 方案1：Railway（最简单，强烈推荐）

**优点**：
- ✅ 自动识别Flask应用
- ✅ 免费额度充足
- ✅ 部署只需2分钟
- ✅ 自动HTTPS

**部署步骤**：

1. 访问 https://railway.app/
2. 点击 "Start a New Project"
3. 选择 "Deploy from GitHub repo"
4. 选择您的仓库：`DDDDanteeeeeee/painpointsearcher`
5. Railway会自动检测到Flask应用
6. **添加环境变量**：
   - 点击项目的 "Variables" 标签
   - 添加：`DEEPSEEK_API_KEY` = `sk-b07c9af227fa49b68ff1f6e4ae36465f`
   - 添加：`PORT` = `5000`
7. 点击 "Deploy"

**等待3-5分钟，您的应用就会在线上运行！**

Railway会提供一个类似 `https://your-app.railway.app` 的URL。

---

### 方案2：Render（也很推荐）

**优点**：
- ✅ 免费套餐
- ✅ 自动部署
- ✅ 支持Python

**部署步骤**：

1. 访问 https://render.com/
2. 注册并登录
3. 点击 "New +" -> "Web Service"
4. 连接GitHub仓库：`DDDDanteeeeeee/painpointsearcher`
5. 配置：
   - **Name**: `painpointsearcher`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python universal_web_interface.py`
6. **添加环境变量**（在 "Advanced" 标签）：
   - `DEEPSEEK_API_KEY` = `sk-b07c9af227fa49b68ff1f6e4ae36465f`
   - `PORT` = `5000`
7. 点击 "Create Web Service"

---

### 方案3：VPS/服务器（完全控制）

**适合**：有自己的服务器（阿里云、腾讯云等）

**部署步骤**：

```bash
# 1. 克隆代码
git clone https://github.com/DDDDanteeeeeee/painpointsearcher.git
cd painpointsearcher

# 2. 安装Python依赖
pip install -r requirements.txt

# 3. 设置环境变量
export DEEPSEEK_API_KEY="sk-b07c9af227fa49b68ff1f6e4ae36465f"

# 4. 启动服务（使用gunicorn生产环境）
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 universal_web_interface:app

# 或者使用screen保持后台运行
screen -S webapp
python universal_web_interface.py
# 按 Ctrl+A+D 退出screen
```

**使用Nginx反向代理**（推荐）：
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 📋 部署前检查清单

- [ ] GitHub仓库已推送到 `https://github.com/DDDDanteeeeeee/painpointsearcher`
- [ ] `requirements.txt` 包含所有依赖
- [ ] `Procfile` 已创建（用于Heroku/Render）
- [ ] `railway.json` 已创建（用于Railway）
- [ ] `.env.example` 已创建（环境变量模板）
- [ ] 代码中没有硬编码的敏感信息

---

## 🔧 本地开发

如果您想在本地运行：

```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export DEEPSEEK_API_KEY="sk-b07c9af227fa49b68ff1f6e4ae36465f"

# 运行应用
python universal_web_interface.py
```

访问：http://localhost:5000

---

## ❌ 为什么不能部署到Netlify？

**Netlify的限制**：
- ❌ 不支持Python后端
- ❌ 不支持Flask/Django等Web框架
- ✅ 只支持静态文件（HTML/CSS/JS）
- ✅ 只支持Serverless Functions（Node.js/Go）

**您的应用需要**：
- ✅ Python运行环境
- ✅ Flask Web框架
- ✅ 持续运行的后端服务

---

## 🎯 快速开始（推荐Railway）

1. 打开 https://railway.app/new
2. 点击 "Deploy from GitHub repo"
3. 选择 `painpointsearcher` 仓库
4. 添加环境变量：`DEEPSEEK_API_KEY`
5. 等待部署完成 ✅

**就这么简单！**

---

## 📞 需要帮助？

如果遇到问题，请检查：
1. 环境变量是否正确设置
2. `requirements.txt` 是否包含所有依赖
3. 端口是否正确（默认5000）
4. 防火墙是否开放相应端口

---

## 💡 成功部署后的URL示例

- Railway: `https://painpointsearcher.up.railway.app`
- Render: `https://painpointsearcher.onrender.com`
- 自定义域名: `https://your-domain.com`
