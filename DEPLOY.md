# CRM 部署手册（VPS + Docker Compose 共享栈 + GitHub Actions）

> 适用场景：VPS 已有 nginx / mysql / redis 以 Docker Compose 编排运行，本项目复用这些基础设施，通过 GitHub Actions 自动部署，使用独立二级域名 + Let's Encrypt HTTPS。WhatsApp / Email 集成暂不启用。

---

## 0. 占位符说明

下面所有命令出现的占位符，操作前替换成你环境的实际值：

| 占位符 | 含义 | 示例 |
|--------|------|------|
| `<DOMAIN>` | CRM 子域名 | `crm.example.com` |
| `<VPS_USER>` | VPS 登录用户 | `deploy` |
| `<VPS_HOST>` | VPS IP 或域名 | `1.2.3.4` |
| `<APP_DIR>` | 项目在 VPS 的目录 | `/opt/crm_os` |
| `<SHARED_NET>` | 共享 docker 网络名 | `shared-net` |
| `<MYSQL_CTN>` | 共享 mysql 容器名 | `mysql` |
| `<REDIS_CTN>` | 共享 redis 容器名 | `redis` |
| `<NGINX_CONF_DIR>` | 共享 nginx 配置目录 | `/opt/infra/nginx/conf.d` |
| `<DB_PASSWORD>` | crm_user 的 mysql 密码 | 16+ 位强密码 |
| `<SECRET_KEY>` | JWT 密钥 | `openssl rand -hex 32` |
| `<GHCR_USER>` | GitHub 用户名/组织名（小写） | `kelvin` |
| `<REPO>` | 仓库名 | `crm_os` |

---

## 1. 一次性准备（约 30 分钟）

### 1.1 盘点共享基础设施

SSH 进 VPS：

```bash
ssh <VPS_USER>@<VPS_HOST>

# 确认共享网络
docker network ls
# 确认 mysql / redis / nginx 容器名
docker ps --format "table {{.Names}}\t{{.Image}}"
# 确认共享 nginx 配置目录
docker inspect <nginx 容器名> | grep -A2 Mounts
```

把上述拿到的实际名称填入第 0 节占位符。

### 1.2 在共享 MySQL 内建库建用户

```bash
docker exec -it <MYSQL_CTN> mysql -uroot -p
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
docker exec -it <MYSQL_CTN> mysql -ucrm_user -p<DB_PASSWORD> -e "SHOW DATABASES;"
```

### 1.3 改造项目 `docker-compose.yml`

把仓库根目录 `docker-compose.yml` 改为只跑 backend 和 frontend，复用共享 mysql/redis/nginx：

```yaml
networks:
  shared:
    external: true
    name: <SHARED_NET>

services:
  backend_1:
    image: ghcr.io/<GHCR_USER>/<REPO>-backend:latest
    env_file: .env
    environment:
      - DB_HOST=<MYSQL_CTN>
      - REDIS_URL=redis://<REDIS_CTN>:6379/0
      - INSTANCE_ID=backend_1
    networks: [shared]
    restart: unless-stopped
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000

  backend_2:
    image: ghcr.io/<GHCR_USER>/<REPO>-backend:latest
    env_file: .env
    environment:
      - DB_HOST=<MYSQL_CTN>
      - REDIS_URL=redis://<REDIS_CTN>:6379/0
      - INSTANCE_ID=backend_2
    networks: [shared]
    restart: unless-stopped
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000

  frontend:
    image: ghcr.io/<GHCR_USER>/<REPO>-frontend:latest
    networks: [shared]
    restart: unless-stopped
```

> 注意：原 `docker-compose.yml` 里的 `mysql` / `redis` / `nginx` 服务和 `volumes: mysql_data` 全部删除。

### 1.4 准备生产 `.env`

在 VPS 上：

```bash
mkdir -p <APP_DIR>
cd <APP_DIR>
nano .env
```

内容：

```env
# 数据库
DB_HOST=<MYSQL_CTN>
DB_PORT=3306
DB_USER=crm_user
DB_PASSWORD=<DB_PASSWORD>
DB_NAME=crm_os

# Redis
REDIS_URL=redis://<REDIS_CTN>:6379/0

# JWT
SECRET_KEY=<SECRET_KEY>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# 应用
APP_ENV=production
CORS_ORIGINS=https://<DOMAIN>

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
VITE_API_BASE_URL=https://<DOMAIN>/api
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
sudo nano <NGINX_CONF_DIR>/crm.conf
```

内容：

```nginx
upstream crm_backend {
    least_conn;
    server backend_1:8000 max_fails=2 fail_timeout=10s;
    server backend_2:8000 max_fails=2 fail_timeout=10s;
    keepalive 32;
}

server {
    listen 80;
    server_name <DOMAIN>;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name <DOMAIN>;

    ssl_certificate     /etc/letsencrypt/live/<DOMAIN>/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/<DOMAIN>/privkey.pem;

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
docker exec -it <nginx 容器名> certbot --nginx -d <DOMAIN>
# 或宿主机 certbot：
sudo certbot certonly --webroot -w /var/www/html -d <DOMAIN>
```

重载共享 nginx：

```bash
docker exec <nginx 容器名> nginx -t
docker exec <nginx 容器名> nginx -s reload
```

### 1.6 GitHub 仓库准备

#### 1.6.1 启用 GHCR 镜像权限

GitHub → 仓库 → Settings → Actions → General → Workflow permissions：选 **Read and write permissions**。

#### 1.6.2 添加 Secrets

仓库 → Settings → Secrets and variables → Actions → New repository secret：

| Secret 名 | 值 |
|-----------|-----|
| `VPS_HOST` | `<VPS_HOST>` |
| `VPS_USER` | `<VPS_USER>` |
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
            cd <APP_DIR>
            git pull --ff-only
            echo "${{ secrets.GITHUB_TOKEN }}" | docker login ghcr.io -u ${{ github.actor }} --password-stdin
            docker compose pull
            docker compose up -d --remove-orphans
            docker compose exec -T backend_1 alembic upgrade head
            docker image prune -f
```

> 把 workflow 内的 `<APP_DIR>` 替换成实际路径。

---

## 2. 首次手动部署（验证链路）

```bash
ssh <VPS_USER>@<VPS_HOST>
cd <APP_DIR>

# 拉代码（首次）
git clone https://github.com/<GHCR_USER>/<REPO>.git .
# 此时 .env 已存在（步骤 1.4），不要被覆盖

# 登录 GHCR（首次拉镜像需要；后续 GHA 会自动登录）
echo <你的 GitHub PAT> | docker login ghcr.io -u <GHCR_USER> --password-stdin

# 触发一次 GHA 构建：本地 push 一个空提交
# （在你本机仓库执行 git commit --allow-empty -m "trigger build" && git push）

# 等 GHA 构建完成后，VPS 上拉镜像
docker compose pull
docker compose up -d

# 跑数据库迁移
docker compose exec backend_1 alembic upgrade head

# 可选：写入种子数据
docker compose exec backend_1 python seed.py
```

验证：

- 浏览器打开 `https://<DOMAIN>` → 看到登录页
- 用种子账号登录 → 进入仪表盘
- 检查 API：`curl https://<DOMAIN>/api/health`（如有健康检查接口）

---

## 3. 持续部署（日常使用）

### 3.1 标准发布流程

1. 本机改代码 → 提 PR → 合并到 `main`
2. GHA 自动：
   - 构建 backend / frontend 镜像并推 GHCR
   - SSH 进 VPS：`git pull` → `docker compose pull` → `docker compose up -d` → `alembic upgrade head`
3. nginx upstream `least_conn` 在 backend_1/2 滚动重启时自动绕过宕机实例，**接近零停机**

### 3.2 回滚

```bash
ssh <VPS_USER>@<VPS_HOST>
cd <APP_DIR>

# 找到上一次正常的 commit SHA
git log --oneline -10

# 回滚镜像 tag
docker pull ghcr.io/<GHCR_USER>/<REPO>-backend:<good-sha>
docker pull ghcr.io/<GHCR_USER>/<REPO>-frontend:<good-sha>

# 临时改 docker-compose.yml 的 image tag 或用 docker tag 重打 latest
docker tag ghcr.io/<GHCR_USER>/<REPO>-backend:<good-sha> ghcr.io/<GHCR_USER>/<REPO>-backend:latest
docker tag ghcr.io/<GHCR_USER>/<REPO>-frontend:<good-sha> ghcr.io/<GHCR_USER>/<REPO>-frontend:latest
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
docker compose logs -f --tail=200 backend_1
docker compose logs -f --tail=200 backend_2
docker compose logs -f frontend
```

---

## 4. 排错速查

| 现象 | 原因 | 处理 |
|------|------|------|
| `502 Bad Gateway` | 后端容器没起来 | `docker compose ps` 查状态，`docker compose logs backend_1` 看异常 |
| 前端能开但 API 401 | CORS 或 token 问题 | 确认 `.env` 中 `CORS_ORIGINS` 包含 `https://<DOMAIN>` |
| 数据库连不上 | mysql 容器名 / 网络不对 | `docker exec backend_1 ping <MYSQL_CTN>`；确认两边都接入 `<SHARED_NET>` |
| GHA `docker login` 失败 | Workflow permissions 没开 | Settings → Actions → Workflow permissions → Read & write |
| GHA SSH 失败 | key 格式错 / 公钥未授权 | secret 里粘**完整私钥**含 BEGIN/END 行；VPS 的 `authorized_keys` 加公钥 |
| Let's Encrypt 续期失败 | 80 端口被占 / 容器没 reload | `certbot renew --dry-run` 看错误；定时 cron 续期后 `nginx -s reload` |

---

## 5. 后续接入 WhatsApp / Email 时

只需在 VPS 的 `<APP_DIR>/.env` 填入对应字段后 `docker compose restart backend_1 backend_2`，无需重新部署。WhatsApp Webhook 公网入口已通过 nginx `/api/webhooks/whatsapp` 暴露（HTTPS 已就绪）。

---

*文档结束。首次执行时按 1 → 2 顺序，之后日常发布只走 3.1。*
