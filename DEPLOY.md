# CRM 部署手册（VPS + Docker Compose 共享栈 + GitHub Actions）

> 适用场景：VPS 已有 nginx / mysql / redis 以 Docker Compose 编排运行，本项目复用这些基础设施，通过 GitHub Actions 自动部署，使用独立二级域名 + Let's Encrypt HTTPS。WhatsApp / Email 集成暂不启用。

---

## 0. 占位符说明

下面所有命令出现的占位符，操作前替换成你环境的实际值：

| 占位符                       | 含义 | 示例                        |
|---------------------------|------|---------------------------|
| `crm.kelvinpeng.com`      | CRM 子域名 | `crm.kelvinpeng.com`      |
| `kelvin-peng`             | VPS 登录用户 | `kelvin-peng`             |
| `103.40.204.95`           | VPS IP 或域名 | `103.40.204.95`           |
| `/opt/crm_os`             | 项目在 VPS 的目录 | `/opt/crm_os`             |
| `proxy_net`               | nginx 所在网络（前端层） | `proxy_net`               |
| `data_net`                | mysql/redis 所在网络（数据层） | `data_net`                |
| `infra_mysql`             | 共享 mysql 容器名 | `infra_mysql`             |
| `infra_redis`             | 共享 redis 容器名 | `infra_redis`             |
| `infra_nginx`             | 共享 nginx 容器名 | `infra_nginx`             |
| `/srv/infra/nginx/conf.d` | 共享 nginx 配置目录 | `/srv/infra/nginx/conf.d` |
| `123456`                  | crm_user 的 mysql 密码（生产必须强密码） | `openssl rand -base64 24` |
| `<SECRET_KEY>`            | JWT 密钥 | `openssl rand -hex 32`    |
| `kelvin`                  | GitHub 用户名/组织名（小写） | `kelvin`                  |
| `crm_os`                  | 仓库名 | `crm_os`                  |

---

## 1. 一次性准备（约 30 分钟）

### 1.1 盘点共享基础设施

SSH 进 VPS：

```bash
ssh kelvin-peng@103.40.204.95

# 确认共享网络
docker network ls
# 确认 mysql / redis / nginx 容器名
docker ps --format "table {{.Names}}\t{{.Image}}"
# 确认共享 nginx 配置目录
docker inspect infra_nginx | grep -A2 Mounts
```

把上述拿到的实际名称填入第 0 节占位符。

### 1.2 在共享 MySQL 内建库建用户

```bash
docker exec -it infra_mysql mysql -uroot -p
```

```sql
CREATE DATABASE crm_os CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'crm_user'@'%' IDENTIFIED BY '<DB_PASSWORD>';
GRANT ALL PRIVILEGES ON crm_os.* TO 'crm_user'@'%';
FLUSH PRIVILEGES;
EXIT;
```

验证：

```bash
docker exec -it infra_mysql mysql -ucrm_user -p<DB_PASSWORD> -e "SHOW DATABASES;"
```

### 1.3 改造项目 `docker-compose.yml`

把仓库根目录 `docker-compose.yml` 改为只跑 backend 和 frontend，复用共享 mysql/redis/nginx：

```yaml
networks:
  proxy_net:
    external: true
    name: proxy_net          # nginx 所在网络
  data_net:
    external: true
    name: data_net           # mysql / redis 所在网络

services:
  backend:
    image: ghcr.io/kelvin/crm_os-backend:latest
    env_file: .env
    environment:
      - DB_HOST=infra_mysql
      - REDIS_URL=redis://infra_redis:6379/0
      - INSTANCE_ID=backend
    networks: [proxy_net, data_net]
    restart: unless-stopped
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000

  frontend:
    image: ghcr.io/kelvin/crm_os-frontend:latest
    networks: [proxy_net]
    restart: unless-stopped
```

> 网络拓扑：
> - `backend` 同时挂 `proxy_net`（让 `infra_nginx` 能反代）+ `data_net`（连 `infra_mysql` / `infra_redis`）
> - `frontend` 只挂 `proxy_net`
> - 原 `docker-compose.yml` 里的 `mysql` / `redis` / `nginx` 服务和 `volumes: mysql_data` 全部删除
>
> 单 backend 实例：发布时容器重启会有 ~5-10 秒短暂 502，不是零停机。后续如需高可用可加 `backend_2` 并改回 `least_conn` upstream。

### 1.4 准备生产 `.env`

在 VPS 上：

```bash
mkdir -p /opt/crm_os
cd /opt/crm_os
nano .env
```

内容：

```env
# 数据库
DB_HOST=infra_mysql
DB_PORT=3306
DB_USER=crm_user
DB_PASSWORD=<DB_PASSWORD>
DB_NAME=crm_os

# Redis
REDIS_URL=redis://infra_redis:6379/0

# JWT
SECRET_KEY=<SECRET_KEY>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# 应用
APP_ENV=production
CORS_ORIGINS=https://crm.kelvinpeng.com

# 集成（暂留空）
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_WEBHOOK_VERIFY_TOKEN=
WHATSAPP_APP_SECRET=
IMAP_HOST=
IMAP_PORT=993
IMAP_USER=
IMAP_PASSWORD=
IMAP_POLL_INTERVAL_SECONDS=60
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=

# 前端
VITE_API_BASE_URL=https://crm.kelvinpeng.com/api
VITE_APP_NAME=CRM Pro
VITE_DEFAULT_LANGUAGE=zh
```

```bash
chmod 600 .env
```

> 重要：`.env` 永远不进 Git。仓库已 `.gitignore`，但请二次确认。

### 1.5 配置共享 nginx 加 CRM vhost

在 VPS：

```bash
sudo nano /infra/nginx/conf.d/crm.conf
```

内容：

```nginx
upstream crm_backend {
    server backend:8000 max_fails=2 fail_timeout=10s;
    keepalive 32;
}

server {
    listen 80;
    server_name crm.kelvinpeng.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name crm.kelvinpeng.com;

    ssl_certificate     /etc/letsencrypt/live/crm.kelvinpeng.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/crm.kelvinpeng.com/privkey.pem;

    client_max_body_size 20M;

    location / {
        proxy_pass http://frontend:80;
        proxy_set_header Host $host;
    }

    location /api/ {
        proxy_pass http://crm_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_read_timeout 60s;
    }
}
```

申请证书（DNS 已解析到 VPS 后）：

```bash
docker exec -it infra_nginx certbot --nginx -d crm.kelvinpeng.com
# 或宿主机 certbot：
sudo certbot certonly --webroot -w /var/www/html -d crm.kelvinpeng.com
```

重载共享 nginx：

```bash
docker exec infra_nginx nginx -t
docker exec infra_nginx nginx -s reload
```

### 1.6 GitHub 仓库准备

#### 1.6.1 启用 GHCR 镜像权限

GitHub → 仓库 → Settings → Actions → General → Workflow permissions：选 **Read and write permissions**。

#### 1.6.2 添加 Secrets

仓库 → Settings → Secrets and variables → Actions → New repository secret：

| Secret 名 | 值 |
|-----------|-----|
| `VPS_HOST` | `103.40.204.95` |
| `VPS_USER` | `kelvin-peng` |
| `VPS_SSH_KEY` | 在 VPS 上 `ssh-keygen -t ed25519 -f ~/.ssh/gha_deploy` 生成的**私钥**全文 |
| `VPS_PORT` | SSH 端口（默认 22） |

把 `~/.ssh/gha_deploy.pub` 内容追加到 VPS 的 `~/.ssh/authorized_keys`。

#### 1.6.3 添加 GitHub Actions workflow

新建 `.github/workflows/deploy.yml`：

```yaml
name: Deploy CRM

on:
  push:
    branches: [main, master]

env:
  REGISTRY: ghcr.io
  IMAGE_BACKEND: ghcr.io/${{ github.repository }}-backend
  IMAGE_FRONTEND: ghcr.io/${{ github.repository }}-frontend

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4

      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build & push backend
        uses: docker/build-push-action@v5
        with:
          context: ./backend
          push: true
          tags: |
            ${{ env.IMAGE_BACKEND }}:latest
            ${{ env.IMAGE_BACKEND }}:${{ github.sha }}

      - name: Build & push frontend
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          push: true
          tags: |
            ${{ env.IMAGE_FRONTEND }}:latest
            ${{ env.IMAGE_FRONTEND }}:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: SSH deploy
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_SSH_KEY }}
          port: ${{ secrets.VPS_PORT }}
          script: |
            set -e
            cd /opt/crm_os
            git pull --ff-only
            echo "${{ secrets.GITHUB_TOKEN }}" | docker login ghcr.io -u ${{ github.actor }} --password-stdin
            docker compose pull
            docker compose up -d --remove-orphans
            docker compose exec -T backend alembic upgrade head
            docker image prune -f
```

> 把 workflow 内的 `/opt/crm_os` 替换成实际路径。

---

## 2. 首次手动部署（验证链路）

```bash
ssh kelvin-peng@103.40.204.95
cd /opt/crm_os

# 拉代码（首次）
git clone https://github.com/kelvin/crm_os.git .
# 此时 .env 已存在（步骤 1.4），不要被覆盖

# 登录 GHCR（首次拉镜像需要；后续 GHA 会自动登录）
echo <你的 GitHub PAT> | docker login ghcr.io -u kelvin --password-stdin

# 触发一次 GHA 构建：本地 push 一个空提交
# （在你本机仓库执行 git commit --allow-empty -m "trigger build" && git push）

# 等 GHA 构建完成后，VPS 上拉镜像
docker compose pull
docker compose up -d

# 跑数据库迁移
docker compose exec backend alembic upgrade head

# 可选：写入种子数据
docker compose exec backend python seed.py
```

验证：

- 浏览器打开 `https://crm.kelvinpeng.com` → 看到登录页
- 用种子账号登录 → 进入仪表盘
- 检查 API：`curl https://crm.kelvinpeng.com/api/health`（如有健康检查接口）

---

## 3. 持续部署（日常使用）

### 3.1 标准发布流程

1. 本机改代码 → 提 PR → 合并到 `main`
2. GHA 自动：
   - 构建 backend / frontend 镜像并推 GHCR
   - SSH 进 VPS：`git pull` → `docker compose pull` → `docker compose up -d` → `alembic upgrade head`
3. backend 容器重启时会有 ~5-10 秒 502 短暂中断（单实例代价）；`docker compose pull` + `up -d` 仅在镜像变化时重建，不变则秒级 noop

### 3.2 回滚

```bash
ssh kelvin-peng@103.40.204.95
cd /opt/crm_os

# 找到上一次正常的 commit SHA
git log --oneline -10

# 回滚镜像 tag
docker pull ghcr.io/kelvin/crm_os-backend:<good-sha>
docker pull ghcr.io/kelvin/crm_os-frontend:<good-sha>

# 临时改 docker-compose.yml 的 image tag 或用 docker tag 重打 latest
docker tag ghcr.io/kelvin/crm_os-backend:<good-sha> ghcr.io/kelvin/crm_os-backend:latest
docker tag ghcr.io/kelvin/crm_os-frontend:<good-sha> ghcr.io/kelvin/crm_os-frontend:latest
docker compose up -d
```

> 数据库迁移回滚需手动 `alembic downgrade -1`，且仅适用于向后兼容的迁移。

### 3.3 数据库迁移规范（避免破坏性变更）

新建迁移要满足"两阶段兼容"：

- 加列、加索引：直接发布
- 改列名 / 删列：先发版本 A（同时保留新旧列、双写），再发版本 B（清理旧列）
- 永不在生产做 `DROP TABLE` 而不备份

### 3.4 日志查看

```bash
docker compose logs -f --tail=200 backend
docker compose logs -f frontend
```

---

## 4. 排错速查

| 现象 | 原因 | 处理 |
|------|------|------|
| `502 Bad Gateway` | 后端容器没起来 | `docker compose ps` 查状态，`docker compose logs backend` 看异常 |
| 前端能开但 API 401 | CORS 或 token 问题 | 确认 `.env` 中 `CORS_ORIGINS` 包含 `https://crm.kelvinpeng.com` |
| 数据库连不上 | mysql 容器名 / 网络不对 | `docker exec backend ping infra_mysql`；确认 backend 已接入 `data_net` |
| GHA `docker login` 失败 | Workflow permissions 没开 | Settings → Actions → Workflow permissions → Read & write |
| GHA SSH 失败 | key 格式错 / 公钥未授权 | secret 里粘**完整私钥**含 BEGIN/END 行；VPS 的 `authorized_keys` 加公钥 |
| Let's Encrypt 续期失败 | 80 端口被占 / 容器没 reload | `certbot renew --dry-run` 看错误；定时 cron 续期后 `nginx -s reload` |

---

## 5. 后续接入 WhatsApp / Email 时

只需在 VPS 的 `/opt/crm_os/.env` 填入对应字段后 `docker compose restart backend`，无需重新部署。WhatsApp Webhook 公网入口已通过 nginx `/api/webhooks/whatsapp` 暴露（HTTPS 已就绪）。

---

*文档结束。首次执行时按 1 → 2 顺序，之后日常发布只走 3.1。*
