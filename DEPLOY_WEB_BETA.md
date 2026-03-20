# WayFare 网页版内测部署指南

本文针对当前仓库的**网页内测模式**：

- 前端：Astro SSR（Node adapter）
- API：Go 后端
- AI Sidecar：Python
- 域名入口：`https://beta.your-domain.com`

目标是让你把 WayFare 放到服务器上，带**登录鉴权、固定内测账号数量、HTTPS 和域名绑定**。

---

## 1. 推荐部署结构

建议一台 Linux 服务器上跑 3 层：

1. **Nginx**
   - 监听 80 / 443
   - 负责 HTTPS、域名绑定、反向代理
2. **Astro 前端**
   - 监听 `127.0.0.1:4321`
   - 负责页面 SSR、登录页、内测 Cookie
3. **Go API**
   - 监听 `127.0.0.1:8080`
   - 负责知识库 / 文档 / chat / schedules / profiles / feedback
   - 启动时会自动拉起 Python sidecar

---

## 2. 域名与 DNS

先在你的域名服务商那里加一条 A 记录：

- 主机记录：`beta`
- 记录值：你的服务器公网 IP

例如：

- 域名：`beta.example.com`
- 指向：`123.45.67.89`

等待 DNS 生效后再继续。

---

## 3. 服务器准备

以下示例假设服务器为 Ubuntu 22.04+。

先安装基础环境：

```bash
sudo apt update
sudo apt install -y nginx git curl unzip build-essential
```

再分别安装：

- Node.js 20+
- Go 1.22+
- Python 3.11+

可用命令验证：

```bash
node -v
npm -v
go version
python3 --version
```

---

## 4. 拉取项目

```bash
cd /opt
sudo git clone <你的仓库地址> wayfare
sudo chown -R $USER:$USER /opt/wayfare
cd /opt/wayfare
```

---

## 5. 前端构建

```bash
cd /opt/wayfare
npm ci
npm run build
```

构建后会得到：

- `dist/server/entry.mjs`

这是 Astro SSR 的启动入口。

---

## 6. Python sidecar 准备

```bash
cd /opt/wayfare/wayfare_ai_backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
deactivate
```

---

## 7. Go 后端构建

```bash
cd /opt/wayfare/wayfare_backend
go build -o wayfare_backend .
```

输出：

- `/opt/wayfare/wayfare_backend/wayfare_backend`

---

## 8. 关键环境变量

当前内测版最关键的是**Astro 和 Go 必须共用同一套内测鉴权配置**。

### 8.1 Astro 前端环境变量

在 `/opt/wayfare/.env` 中写：

```env
PUBLIC_API_BASE_URL=https://beta.example.com

BETA_AUTH_ENABLED=1
BETA_AUTH_COOKIE_NAME=wayfare_beta_auth
BETA_AUTH_SECRET=请换成一段长度足够的随机字符串
BETA_AUTH_SESSION_HOURS=24

# 用账号数量来限制内测人数
# 格式：用户名:密码,用户名:密码
BETA_ALLOWED_USERS=tester01:Pass_One_2026,tester02:Pass_Two_2026,tester03:Pass_Three_2026
```

### 8.2 Go 后端环境变量

给 Go 服务也配同样的鉴权字段，并补上运行参数：

```env
WAYFARE_OPEN_BROWSER=0
WAYFARE_PORT=8080
WAYFARE_BASE_DIR=/opt/wayfare/wayfare_backend/runtime

BETA_AUTH_ENABLED=1
BETA_AUTH_COOKIE_NAME=wayfare_beta_auth
BETA_AUTH_SECRET=请与 Astro 完全一致
BETA_ALLOWED_USERS=tester01:Pass_One_2026,tester02:Pass_Two_2026,tester03:Pass_Three_2026

WAYFARE_ALLOWED_ORIGINS=https://beta.example.com
```

### 8.3 Python sidecar 环境变量

在 `/opt/wayfare/wayfare_ai_backend/.env` 中至少补：

```env
LLM_API_KEY=你的模型服务密钥
LLM_BASE_URL=你的模型服务地址
LLM_MODEL_NAME=你的模型名
```

---

## 9. 如何限制内测用户数量

当前实现方式是：

> **只给固定数量的测试账号。**

也就是说：

- `BETA_ALLOWED_USERS` 里有几个账号
- 就最多允许几组测试身份进入

例如你只放 5 个账号，就天然把内测人数限制在 5 组凭证内。

如果你想进一步缩量：

- 删除某些账号
- 修改密码
- 重启 Astro 和 Go 服务

---

## 10. systemd 服务

建议分别注册两个 systemd 服务。

---

### 10.1 Astro 服务

新建：

`/etc/systemd/system/wayfare-frontend.service`

```ini
[Unit]
Description=WayFare Astro Frontend
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/wayfare
EnvironmentFile=/opt/wayfare/.env
Environment=HOST=127.0.0.1
Environment=PORT=4321
ExecStart=/usr/bin/node /opt/wayfare/dist/server/entry.mjs
Restart=always
RestartSec=3
User=www-data
Group=www-data

[Install]
WantedBy=multi-user.target
```

---

### 10.2 Go 后端服务

新建：

`/etc/systemd/system/wayfare-backend.service`

```ini
[Unit]
Description=WayFare Go Backend
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/wayfare/wayfare_backend
EnvironmentFile=/opt/wayfare/wayfare_backend/.env.runtime
ExecStart=/opt/wayfare/wayfare_backend/wayfare_backend
Restart=always
RestartSec=3
User=www-data
Group=www-data

[Install]
WantedBy=multi-user.target
```

然后把第 8.2 节那组 Go 环境变量写到：

`/opt/wayfare/wayfare_backend/.env.runtime`

---

## 11. 启动服务

```bash
sudo systemctl daemon-reload
sudo systemctl enable wayfare-frontend
sudo systemctl enable wayfare-backend
sudo systemctl start wayfare-frontend
sudo systemctl start wayfare-backend
```

检查状态：

```bash
sudo systemctl status wayfare-frontend
sudo systemctl status wayfare-backend
```

本地健康检查：

```bash
curl http://127.0.0.1:4321/login
curl http://127.0.0.1:8080/healthz
```

---

## 12. Nginx 反向代理

新建站点配置：

`/etc/nginx/sites-available/wayfare-beta`

```nginx
server {
    listen 80;
    server_name beta.example.com;

    client_max_body_size 100m;

    location /healthz {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location ~ ^/(knowledge-bases|documents|upload|chat|schedules|profiles|feedback)(/.*)?$ {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://127.0.0.1:4321;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection \"upgrade\";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

启用：

```bash
sudo ln -s /etc/nginx/sites-available/wayfare-beta /etc/nginx/sites-enabled/wayfare-beta
sudo nginx -t
sudo systemctl reload nginx
```

---

## 13. 绑定 HTTPS

如果你用的是 Let’s Encrypt：

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d beta.example.com
```

完成后：

- 80 会自动跳转到 443
- 浏览器访问会变成 `https://beta.example.com`

---

## 14. 首次上线后的检查清单

建议按这个顺序验证：

### 14.1 登录与鉴权

- 打开 `https://beta.example.com/login`
- 用测试账号登录
- 未登录时访问 `/dashboard` 会被重定向回 `/login`
- 登录后可正常进入 `/dashboard`

### 14.2 核心知识库链路

- 创建知识库
- 上传 PDF
- 等待解析完成
- 打开阅读器
- 向 AI 提问

### 14.3 反馈与画像

- Dashboard 能提交反馈
- Workspace 能提交反馈
- 能保存全局画像
- 能保存知识库画像
- AI 默认使用中文回答

### 14.4 服务器侧数据

检查这些文件是否生成：

```bash
/opt/wayfare/wayfare_backend/runtime/data/knowledge_bases.json
/opt/wayfare/wayfare_backend/runtime/data/schedules.json
/opt/wayfare/wayfare_backend/runtime/data/feedback.jsonl
/opt/wayfare/wayfare_backend/runtime/data/profiles/global_profile.md
/opt/wayfare/wayfare_backend/runtime/data/profiles/kb/
```

---

## 15. 常见问题

### Q1. 登录成功后 API 还是 401？

先检查：

1. Astro 和 Go 的这几个变量是否完全一致：
   - `BETA_AUTH_ENABLED`
   - `BETA_AUTH_COOKIE_NAME`
   - `BETA_AUTH_SECRET`
   - `BETA_ALLOWED_USERS`
2. 域名是否统一走 `beta.example.com`
3. 反代是否把请求拆到了错误端口

---

### Q2. 登录页能开，但上传失败？

通常看这几项：

- Nginx `client_max_body_size`
- Go 服务有没有启动
- Python sidecar 的 `.venv` 是否存在
- `wayfare_ai_backend/.env` 中模型配置是否齐全

---

### Q3. 为什么建议不要混用 localhost 和 127.0.0.1？

因为 Cookie 和跨端口请求在本地调试时会受主机名影响。  
本地联调时建议统一用：

- 前端：`http://127.0.0.1:4321`
- 后端：`http://127.0.0.1:8080`

---

## 16. 上线后的日常运维动作

### 更新前端

```bash
cd /opt/wayfare
git pull
npm ci
npm run build
sudo systemctl restart wayfare-frontend
```

### 更新后端

```bash
cd /opt/wayfare/wayfare_backend
git pull
go build -o wayfare_backend .
sudo systemctl restart wayfare-backend
```

### 下线某个测试账号

修改：

```env
BETA_ALLOWED_USERS=...
```

删掉对应账号后：

```bash
sudo systemctl restart wayfare-frontend
sudo systemctl restart wayfare-backend
```

---

## 17. 当前部署建议结论

对于你现在的内测阶段，我建议：

1. **先用固定少量账号做网页内测**
2. **把反馈、画像和 AI 中文稳定性跑顺**
3. **再考虑扩大名单或做更复杂的权限系统**

这样最省服务器压力，也最方便定位问题。
