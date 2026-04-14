# CRM 客户关系管理系统 — 需求文档

**版本**: v1.4  
**日期**: 2026-04-12  
**适用对象**: Claude Code / 开发工程师  

---

## 一、项目概述

### 1.1 项目目标

构建一套面向多行业的 **Web 端 CRM 客户关系管理系统**，支持销售团队对客户全生命周期进行管理，包括客户录入、跟进记录、商机管理、任务分配及数据分析。

### 1.2 目标用户

- 销售代表（日常录入、跟进客户）
- 销售主管（查看团队数据、分配任务）
- 管理员（系统配置、用户管理）

### 1.3 支持行业

科技/IT、金融/保险、医疗/健康、教育/培训、零售/电商、制造/工业、房地产、咨询/服务、餐饮/酒店、物流/供应链（可在后台扩展）

---

## 二、技术选型

| 层级 | 技术栈 |
|------|--------|
| 前端框架 | React 18 + TypeScript |
| UI 组件库 | Tailwind CSS（自定义主题，**响应式 Mobile + PC**）|
| 国际化 | **react-i18next**（支持中文 zh / 英文 en，语言偏好存用户表）|
| 状态管理 | Zustand 或 React Context |
| 后端框架 | **Python 3.11 + FastAPI** |
| ORM | **SQLAlchemy 2.0（async）+ Alembic（迁移）** |
| 数据验证 | **Pydantic v2** |
| 数据库 | **MySQL 8.0（主库）+ Redis 7（缓存/会话）** |
| 认证 | JWT（python-jose）— Access Token（15分钟）+ Refresh Token（7天）|
| 密码加密 | **passlib[bcrypt]** |
| 消息集成 | **WhatsApp Business API（Cloud API）+ SMTP 邮件（收件监听）** |
| 反向代理 | **Nginx（负载均衡，2 个后端副本）** |
| 文件存储 | 本地 / AWS S3 |
| 部署 | Docker Compose |

---

## 三、数据模型

### 3.1 用户表（users）

```sql
id            CHAR(36) PRIMARY KEY DEFAULT (UUID())   -- MySQL 8.0+ 支持 UUID()
name          VARCHAR(100) NOT NULL
email         VARCHAR(200) NOT NULL UNIQUE
password_hash VARCHAR(255) NOT NULL
role          ENUM('admin', 'manager', 'sales') NOT NULL DEFAULT 'sales'
avatar_url    TEXT
language      ENUM('zh', 'en') NOT NULL DEFAULT 'zh'  -- 界面语言偏好
manager_id    CHAR(36) DEFAULT NULL                   -- 上级 manager（sales 填此字段，manager/admin 为 NULL）
is_active     TINYINT(1) NOT NULL DEFAULT 1           -- 软删除标志
created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
```

### 3.2 客户表（contacts）

```sql
id            CHAR(36) PRIMARY KEY DEFAULT (UUID())
name          VARCHAR(100) NOT NULL
company       VARCHAR(200) DEFAULT NULL                -- 公司名称，可为空
industry      VARCHAR(50)
status        ENUM('潜在客户','跟进中','谈判中','已成交','已流失') NOT NULL DEFAULT '潜在客户'
priority      ENUM('高','中','低') NOT NULL DEFAULT '中'
deal_value    DECIMAL(15,2) DEFAULT 0.00
email         VARCHAR(200)
phone         VARCHAR(30)
address       TEXT
notes         TEXT
assigned_to   CHAR(36)                                -- FK → users.id（应用层维护）
last_contact  DATE
tags          JSON                                    -- MySQL 8.0+ 原生 JSON，存储字符串数组
deleted_at    DATETIME DEFAULT NULL                   -- 软删除
created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP

INDEX idx_status (status)
INDEX idx_industry (industry)
INDEX idx_assigned_to (assigned_to)
INDEX idx_deleted_at (deleted_at)
```

### 3.3 跟进记录表（activities）

```sql
id            CHAR(36) PRIMARY KEY DEFAULT (UUID())
contact_id    CHAR(36) NOT NULL
user_id       CHAR(36) NOT NULL
type          ENUM('电话','邮件','会面','WhatsApp','其他','状态变更') NOT NULL
content       TEXT
follow_date   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP

INDEX idx_contact_id (contact_id)
```

### 3.4 任务表（tasks）

```sql
id            CHAR(36) PRIMARY KEY DEFAULT (UUID())
title         VARCHAR(300) NOT NULL
contact_id    CHAR(36)
assigned_to   CHAR(36)
priority      ENUM('高','中','低') NOT NULL DEFAULT '中'
due_date      DATE
is_done       TINYINT(1) NOT NULL DEFAULT 0
done_at       DATETIME DEFAULT NULL
created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP

INDEX idx_assigned_to (assigned_to)
INDEX idx_due_date (due_date)
INDEX idx_is_done (is_done)
```

### 3.5 系统配置表（settings）

```sql
`key`         VARCHAR(100) PRIMARY KEY
value         JSON NOT NULL
updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
```

### 3.6 消息记录表（messages）

```sql
id            CHAR(36) PRIMARY KEY DEFAULT (UUID())
contact_id    CHAR(36)                                -- 关联客户（可为空，首次消息未创建客户前）
channel       ENUM('whatsapp','email') NOT NULL       -- 来源渠道
direction     ENUM('inbound','outbound') NOT NULL     -- 入站/出站
sender_id     VARCHAR(200) NOT NULL                   -- 发件人（WhatsApp 号码 / 邮箱地址）
recipient_id  VARCHAR(200) NOT NULL                   -- 收件人
subject       VARCHAR(500)                            -- 邮件主题（WhatsApp 为空）
body          TEXT NOT NULL                           -- 消息正文
external_id   VARCHAR(200) UNIQUE                     -- WhatsApp message_id / 邮件 Message-ID
is_read       TINYINT(1) NOT NULL DEFAULT 0
assigned_to   CHAR(36)                                -- 分配给哪位销售
created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP

INDEX idx_contact_id (contact_id)
INDEX idx_channel (channel)
INDEX idx_sender_id (sender_id)
INDEX idx_created_at (created_at)
```

### 3.7 客户分配规则表（routing_rules）

```sql
id            CHAR(36) PRIMARY KEY DEFAULT (UUID())
name          VARCHAR(100) NOT NULL                   -- 规则名称
is_active     TINYINT(1) NOT NULL DEFAULT 1
priority      INT NOT NULL DEFAULT 0                  -- 数值越小优先级越高
strategy      ENUM('workload','region','win_rate') NOT NULL  -- 分配策略
conditions    JSON                                    -- 规则条件（地区列表等）
target_users  JSON                                    -- 参与分配的销售 ID 列表
created_by    CHAR(36)
created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
```

### 3.8 销售月度目标表（sales_targets）

```sql
id            CHAR(36) PRIMARY KEY DEFAULT (UUID())
user_id       CHAR(36) NOT NULL
year          SMALLINT NOT NULL
month         TINYINT NOT NULL                        -- 1-12
target_amount DECIMAL(15,2) NOT NULL DEFAULT 0        -- 成交金额目标
target_count  INT NOT NULL DEFAULT 0                  -- 成交单数目标
created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP

UNIQUE KEY uk_user_year_month (user_id, year, month)
```

> **MySQL 注意事项**：
> - MySQL 不支持 `TEXT[]` 数组类型，tags 字段使用 `JSON` 类型存储（`["标签A","标签B"]`）
> - MySQL 不支持 `JSONB`，使用 `JSON` 类型（查询性能略低，对本项目体量无影响）
> - 外键关系在应用层（SQLAlchemy relationship）维护，不强制 DB 级 FK，避免迁移复杂度
> - 字符集统一设置为 `utf8mb4`，排序规则为 `utf8mb4_unicode_ci`

---

## 四、功能模块详细需求

---

### 4.1 认证模块

#### 4.1.1 登录

- **路由**: `POST /api/auth/login`
- 接受 email + password
- 密码使用 bcrypt 存储
- 登录成功返回 `access_token`（15分钟有效）+ `refresh_token`（7天有效）
- 失败超过 5 次锁定账号 10 分钟

#### 4.1.2 Token 刷新

- **路由**: `POST /api/auth/refresh`
- 使用 Refresh Token 换取新 Access Token

#### 4.1.3 登出

- **路由**: `POST /api/auth/logout`
- 服务端将 Refresh Token 加入黑名单（存 Redis）

#### 4.1.4 前端登录页

- 邮箱 + 密码输入框，显示/隐藏密码切换
- 「记住我」复选框（7天免登录）
- 表单校验：邮箱格式、密码不能为空
- 错误提示：账号不存在 / 密码错误 / 账号已锁定

---

### 4.2 仪表盘模块

仪表盘根据用户角色自动渲染不同视图，共三个版本，路由均为 `/dashboard`，前端按 `currentUser.role` 选择组件。

---

#### 4.2.1 Admin 仪表盘

**路由**: `GET /api/dashboard/admin`（仅 admin 可访问）

**① KPI Cards（6 张，实时数据，全公司范围）**

| 卡片 | 字段 | 计算方式 |
|------|------|----------|
| 今日新增线索 | `new_leads_today` | contacts.created_at = 今日 |
| 今日待跟进 | `follow_up_today` | tasks.due_date = 今日 AND is_done=0 |
| 报价中数量 | `quoting_count` | contacts.status = '谈判中' |
| 本月成交 GMV | `monthly_gmv` | status='已成交' 且成交时间在本月内的 deal_value 之和 |
| 本月成交率 | `monthly_win_rate` | 本月成交数 / 本月新增线索数，百分比 |
| 预计 Pipeline 金额 | `pipeline_value` | status IN ('跟进中','谈判中') 的 deal_value 之和 |

**② 销售漏斗 Funnel（全公司）**

| 漏斗阶段 | 对应 status | 说明 |
|----------|------------|------|
| 新线索 | 潜在客户 | - |
| 已联系 | 跟进中 | - |
| 需求确认 | 跟进中（有跟进记录）| 至少有 1 条 activity |
| 报价中 | 谈判中 | - |
| 成交 | 已成交 | - |

**③ 销售排行榜**

**路由**: `GET /api/dashboard/leaderboard?month=YYYY-MM`

返回字段：销售员姓名、头像、本月成交金额、本月成交单数，按成交金额降序，最多返回 10 条。

**④ GMV 趋势图**

**路由**: `GET /api/dashboard/gmv-trend?period=month|year`

- `period=month`：返回近 12 个月每月成交 GMV
- `period=year`：返回近 5 年每年成交 GMV
- 返回格式：`[{ "label": "2026-03", "value": 1200000 }, ...]`

---

#### 4.2.2 Manager 仪表盘

**路由**: `GET /api/dashboard/manager`（仅 manager 可访问，数据范围为其所在团队）

> Manager 的"团队"定义：`assigned_to IN (该 manager 管理的销售 ID 列表)`。管理关系可在用户管理中配置（用户表扩展 `manager_id` 字段，见 3.1 备注）。

**① 团队 KPI（5 张卡片）**

| 卡片 | 字段 | 计算方式 |
|------|------|----------|
| 本月团队成交 GMV | `team_monthly_gmv` | 团队成员负责的本月已成交 deal_value 之和 |
| 团队目标完成率 | `team_target_rate` | 团队本月总成交 GMV / 团队本月 sales_targets 金额之和，百分比 |
| Pipeline 总金额 | `team_pipeline_value` | 团队客户中 status IN ('跟进中','谈判中') 的 deal_value 之和 |
| 团队 Win Rate | `team_win_rate` | 团队本月成交数 / 团队本月新增线索数，百分比 |
| 平均销售周期 | `avg_sales_cycle_days` | 团队已成交客户从 created_at 到成交时间的平均天数（近 90 天）|

**② 团队销售漏斗**

| 漏斗阶段 | 对应规则 |
|----------|----------|
| 新线索 | 团队客户 status = '潜在客户' |
| 已联系 | status = '跟进中' |
| 需求确认 | status = '跟进中' 且有至少 1 条 activity |
| 报价中 | status = '谈判中' |
| 谈判中 | status = '谈判中' 且有 2 条以上 activity |
| 成交 | status = '已成交' |

**③ 团队排行榜**

**路由**: `GET /api/dashboard/team-leaderboard?month=YYYY-MM`

| 列 | 说明 |
|----|------|
| 销售姓名 | - |
| 成交额 | 本月已成交 deal_value 之和 |
| 成交数 | 本月成交客户数 |
| Win Rate | 本月成交数 / 本月接手线索数，百分比 |

按成交额降序，显示该 manager 团队内全部成员。

---

#### 4.2.3 Sales 仪表盘

**路由**: `GET /api/dashboard/sales`（只返回当前登录销售的数据）

**① 我的 KPI（5 张卡片）**

| 卡片 | 字段 | 计算方式 |
|------|------|----------|
| 今日新增客户 | `new_contacts_today` | 我负责的 contacts，created_at = 今日 |
| 今日待跟进 | `follow_up_today` | 分配给我的 tasks，due_date = 今日 AND is_done=0 |
| 本月成交金额 | `monthly_gmv` | 我负责的已成交客户本月 deal_value 之和 |
| 本月成交单数 | `monthly_won_count` | 我负责的本月成交客户数 |
| 目标完成率 | `target_completion_rate` | 本月成交金额 / sales_targets 中设置的目标金额，百分比 |

**② 我的 Pipeline**

| Pipeline 阶段 | 对应 status |
|--------------|------------|
| 新客户 | 潜在客户 |
| 已联系 | 跟进中 |
| 报价中 | 谈判中 |
| 谈判中 | 谈判中（有报价记录）|
| 成交 | 已成交 |

每个阶段卡片展示：数量、金额合计、最近更新时间。

### 4.3 客户管理模块

#### 4.3.1 客户列表

**路由**: `GET /api/contacts`

**查询参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| search | string | 模糊匹配姓名、公司名 |
| industry | string | 行业筛选 |
| status | string | 状态筛选 |
| priority | string | 优先级筛选 |
| assigned_to | UUID | 负责人筛选 |
| page | integer | 当前页，默认 1 |
| page_size | integer | 每页条数，默认 20，最大 100 |
| sort_by | string | 排序字段（deal_value/last_contact/created_at） |
| order | string | asc / desc |

**返回结构**：

```json
{
  "data": [ ...客户列表... ],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

**前端列表展示字段**：头像字母、姓名、公司、行业、状态Badge、优先级图标、商机金额、最后联系日期

#### 4.3.2 客户详情面板

- 点击列表中任意客户，右侧展开详情面板（不跳转页面）
- 面板内容：基本信息、联系方式、备注、标签、商机金额
- 包含快捷操作按钮：「发起跟进」「编辑资料」「删除」

#### 4.3.3 新建客户页面

**前端路由**: `/contacts/new`（独立全页面，不再是弹窗）

页面顶部提供两种录入方式的 Tab 切换：

---

##### 方式一：手动录入

**路由**: `POST /api/contacts`

**表单字段**（必填项标注 *）：

- 姓名 *
- 公司名称（选填，可为空）
- 所属行业（下拉选择）
- 客户状态（下拉选择，默认「潜在客户」）
- 优先级（高/中/低，默认中）
- 商机金额
- 邮箱（需校验格式）
- 电话
- 备注
- 标签（支持自定义输入，回车添加）
- 负责销售（管理员/主管可选，销售默认为自己；**只展示 is_active=1 的销售账号**）

**验证规则**：
- 姓名不能为空
- 公司名称可为空，填写时无格式限制
- 邮箱如填写必须合法
- 商机金额必须为正数
- 负责销售只能选择 `is_active = 1` 的用户，后端须二次校验

---

##### 方式二：Excel 批量导入

支持同时导入**新客户**和**更新已有客户**资料。

**前端操作流程**：

1. 用户点击「下载模板」获取标准 Excel 模板（`.xlsx`）
2. 填写后上传文件（支持 `.xlsx` / `.xls`，大小限制 10MB）
3. 前端解析预览：展示解析后的数据表格，高亮错误行（红色）和警告行（黄色）
4. 用户确认无误后点击「确认导入」提交
5. 后端处理并返回导入结果汇总

**Excel 模板列定义**：

| 列名 | 字段 | 必填 | 说明 |
|------|------|------|------|
| 姓名 | name | ✅ | 不能为空 |
| 公司名称 | company | ❌ | 可为空 |
| 行业 | industry | ❌ | 须匹配系统行业列表，不匹配则忽略（取默认空）|
| 状态 | status | ❌ | 须为：潜在客户/跟进中/谈判中/已成交/已流失，不填默认「潜在客户」|
| 优先级 | priority | ❌ | 高/中/低，不填默认「中」|
| 商机金额 | deal_value | ❌ | 数字，不填默认 0 |
| 邮箱 | email | ❌ | 填写时须符合邮箱格式 |
| 电话 | phone | ❌ | - |
| 地址 | address | ❌ | - |
| 备注 | notes | ❌ | - |
| 标签 | tags | ❌ | 多个标签用英文逗号分隔，如 `大客户,VIP` |
| 负责销售邮箱 | assigned_to_email | ❌ | 填写系统内销售的邮箱（须 is_active=1），不填则触发 Routing 规则自动分配 |
| 客户ID（更新时填写）| id | ❌ | 填写已存在的客户 UUID 表示更新该客户，留空表示新建 |

**后端导入接口**：

- **路由**: `POST /api/contacts/import`
- Content-Type: `multipart/form-data`
- 请求参数：`file`（Excel 文件）
- 处理逻辑：
  1. 使用 `openpyxl` 解析 Excel
  2. 逐行校验：姓名不能为空、邮箱格式、状态/优先级枚举合法性、assigned_to_email 对应用户须 `is_active=1`
  3. 有 `id` 列且非空 → 执行 UPDATE（仅更新文件中有值的字段，空列不覆盖原值）
  4. 无 `id` 列或为空 → 执行 INSERT（新建客户）
  5. 所有行在一个事务中处理：任意行发生数据库错误时整体回滚
  6. 校验错误（格式非法等）不触发回滚，跳过该行并记录到错误列表

- **返回结构**：

```json
{
  "success": true,
  "data": {
    "total": 50,
    "inserted": 35,
    "updated": 12,
    "skipped": 3,
    "errors": [
      { "row": 5, "field": "email", "message": "邮箱格式不正确" },
      { "row": 12, "field": "assigned_to_email", "message": "销售账号不存在或已停用" }
    ]
  }
}
```

**模板下载接口**：

- **路由**: `GET /api/contacts/import/template`
- 返回标准 `.xlsx` 文件，包含表头行和一行示例数据，Content-Disposition 为附件下载

**依赖库**（加入 requirements.txt）：

```
openpyxl==3.1.2    # Excel 读写
```

**前端解析预览**（客户端处理，无需额外上传）：

- 使用 `xlsx`（SheetJS）库在浏览器端读取文件并渲染预览表格
- 实时标红必填项为空、邮箱格式错误等可即时发现的问题
- 展示「共 N 行，预计新增 X 条，更新 Y 条，X 行有问题」的摘要
- 用户可在预览中查看每行数据，确认后再提交



#### 4.3.4 编辑客户

**路由**: `PUT /api/contacts/:id`

- 表单同新建，自动填充已有数据
- 状态变更需记录变更历史（存入 activities 表，type='状态变更'）
- 负责销售下拉列表只展示 `is_active = 1` 的用户；后端收到请求时须校验 `assigned_to` 对应用户的 `is_active = 1`，否则返回 400

#### 4.3.5 删除客户

**路由**: `DELETE /api/contacts/:id`

- 二次确认弹窗（"此操作不可撤销，确认删除吗？"）
- 软删除（增加 deleted_at 字段）

#### 4.3.6 跟进记录

**路由**: 
- `GET /api/contacts/:id/activities` — 查看该客户跟进历史
- `POST /api/contacts/:id/activities` — 新增跟进记录

**新增跟进表单**：
- 跟进方式（电话/邮件/会面/微信/其他）
- 跟进内容（文本域）
- 跟进时间（默认当前时间，可修改）

跟进记录以时间线（Timeline）形式展示。

---

### 4.4 销售漏斗模块

**路由**: `GET /api/pipeline`

**功能**：

- 以看板视图展示五个阶段：潜在客户 → 跟进中 → 谈判中 → 已成交 → 已流失
- 每列展示：阶段名称、客户数量、该阶段商机总额
- 每张卡片展示：客户姓名、公司、行业标签、商机金额
- **支持拖拽**：将卡片拖到其他列，自动更新客户 status（调用 `PUT /api/contacts/:id` 接口）
- 点击卡片跳转到客户管理模块并打开详情面板

---

### 4.5 任务中心模块

#### 4.5.1 任务列表

**路由**: `GET /api/tasks`

**查询参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| status | string | all / pending / done |
| priority | string | 优先级筛选 |
| assigned_to | UUID | 负责人 |
| due_before | date | 截止日期筛选 |

**展示字段**：完成勾选框、任务标题、关联客户名、截止日期、优先级标签

#### 4.5.2 新建任务

**路由**: `POST /api/tasks`

**表单字段**：
- 任务标题 *
- 关联客户（搜索下拉选择）
- 指派给（下拉选择，默认当前用户）
- 优先级
- 截止日期

#### 4.5.3 完成/取消完成

**路由**: `PATCH /api/tasks/:id/toggle`

- 点击勾选框即触发，不需弹窗确认
- 更新 is_done 和 done_at 字段

#### 4.5.4 今日到期提醒

- 系统加载时，自动检测 due_date = 今日 且 is_done = false 的任务
- 在页面顶部或右下角弹出通知提示，显示任务数量

---

### 4.6 消息集成模块（WhatsApp + Email）

#### 4.6.1 功能概述

当客户**首次**通过 WhatsApp 或 邮件发起咨询时，系统自动在 CRM 中创建新客户记录，并触发客户分配规则（见 4.7）。后续该客户的所有消息均记录在消息记录表（messages）中，可在客户详情面板内查看历史对话。

#### 4.6.2 WhatsApp 集成

**使用 WhatsApp Business Cloud API（Meta 官方）**

**入站消息处理流程**：

1. Meta 推送 Webhook 到 `POST /api/webhooks/whatsapp`
2. 后端校验 `X-Hub-Signature-256` 签名（防伪造）
3. 提取发送方号码 `from`、消息内容 `text.body`、`timestamp`
4. 查询 messages 表：`sender_id = from AND channel = 'whatsapp'`
   - **首次消息**（未找到记录）：
     - 调用客户分配规则，得到 `assigned_to` 用户 ID
     - 在 contacts 表创建新客户（name=号码，phone=号码，status='潜在客户'，来源=whatsapp）
     - 写入 messages 表（contact_id=新客户 ID）
     - 推送系统通知给被分配的销售
   - **已有客户**：直接写入 messages 表，关联已有 contact_id
5. 返回 HTTP 200（必须，否则 Meta 会重试）

**出站消息**：

- **路由**: `POST /api/messages/whatsapp/send`
- 请求体：`{ contact_id, message }`
- 后端调用 Meta Graph API 发送消息，写入 messages 表（direction=outbound）

**Webhook 验证**（GET 请求，Meta 首次配置时校验）：

- **路由**: `GET /api/webhooks/whatsapp`
- 返回 `hub.challenge` 参数

**所需环境变量**（见第十二章 `.env` 统一配置）：`WHATSAPP_PHONE_NUMBER_ID`、`WHATSAPP_ACCESS_TOKEN`、`WHATSAPP_WEBHOOK_VERIFY_TOKEN`、`WHATSAPP_APP_SECRET`

#### 4.6.3 Email 集成

**方式：IMAP 轮询（每 60 秒）+ SMTP 发送**

**入站邮件处理流程**：

1. 后台定时任务（AsyncIO 或 APScheduler）每 60 秒连接 IMAP，拉取 UNSEEN 邮件
2. 解析发件人地址 `From`、主题 `Subject`、正文（优先 text/plain，fallback text/html）、`Message-ID`
3. 去重检查：`external_id = Message-ID` 是否已存在
4. 查询 contacts 表：`email = From地址 AND deleted_at IS NULL`
   - **首次邮件**（未找到客户）：
     - 解析发件人姓名（From 头中的 display name）
     - 调用客户分配规则，得到 `assigned_to`
     - 创建新客户（name=显示名/邮箱前缀，email=地址，status='潜在客户'，来源=email）
     - 写入 messages 表
     - 推送通知给被分配销售
   - **已有客户**：直接写入 messages 表
5. 将邮件标记为已读（IMAP STORE +FLAGS \Seen）

**出站邮件**：

- **路由**: `POST /api/messages/email/send`
- 请求体：`{ contact_id, subject, body }`
- 使用 SMTP 发送，写入 messages 表（direction=outbound）

**所需环境变量**（见第十二章 `.env` 统一配置）：`IMAP_HOST`、`IMAP_PORT`、`IMAP_USER`、`IMAP_PASSWORD`、`IMAP_POLL_INTERVAL_SECONDS`、`SMTP_HOST`、`SMTP_PORT`、`SMTP_USER`、`SMTP_PASSWORD`、`SMTP_FROM`

#### 4.6.4 消息收件箱页面

**路由**: `/inbox`

- 左侧：消息列表（按时间倒序），显示渠道图标（WhatsApp/邮件）、发件人、内容摘要、时间
- 右侧：选中消息的完整对话记录（Timeline 形式）
- 顶部筛选：全部 / WhatsApp / 邮件 / 未读
- 每条消息显示：关联客户名（如已创建）、负责销售、渠道标识
- 支持直接在收件箱内回复消息

**接口**：

- `GET /api/messages` — 消息列表（支持 channel、is_read、contact_id 筛选）
- `PATCH /api/messages/:id/read` — 标记已读
- `GET /api/messages/contact/:contact_id` — 某客户的完整消息记录

---

### 4.7 客户分配（Routing）模块

#### 4.7.1 功能概述

当新客户通过 WhatsApp / 邮件进入系统，或手动创建客户且未指定负责人时，系统按照激活的分配规则自动为该客户指派销售。

#### 4.7.2 分配策略

支持以下三种策略，可在后台配置：

| 策略 | 说明 |
|------|------|
| `workload`（当前工作量，默认）| 分配给当前负责客户数最少的销售 |
| `region`（地区匹配）| 根据客户的地区/来源，匹配预设地区负责人 |
| `win_rate`（历史成交率）| 优先分配给成交率最高的销售（近 90 天已成交/总接手客户数）|

**分配执行逻辑**（`routing_service.py`）**：

```python
async def assign_contact(contact, db) -> str:
    """返回 assigned_to 的 user_id"""
    rules = await get_active_rules(db)  # 按 priority 排序
    for rule in rules:
        # 关键：从候选列表中过滤掉 is_active=0 的用户
        eligible_users = await filter_active_users(rule.target_users, db)
        if not eligible_users:
            continue
        if rule.strategy == "region":
            user_id = match_region(contact, rule, eligible_users)
        elif rule.strategy == "win_rate":
            user_id = get_highest_win_rate(eligible_users, db)
        else:  # workload（默认兜底）
            user_id = get_least_workload(eligible_users, db)
        if user_id:
            return user_id
    # 兜底：取第一个 is_active=1 的销售，若无则抛出异常
    return await get_default_active_user(db)

async def filter_active_users(user_ids: list, db) -> list:
    """只保留 is_active=1 的用户 ID"""
    result = await db.execute(
        select(User.id).where(User.id.in_(user_ids), User.is_active == 1)
    )
    return result.scalars().all()
```

> **重要约束**：任何分配操作（自动 Routing、手动编辑客户指派、新建客户选择负责人）均不得将客户分配给 `is_active = 0` 的用户。后端须在所有写入 `assigned_to` 的接口中统一校验，前端下拉列表也只展示 `is_active = 1` 的销售账号。

#### 4.7.3 分配规则管理页面

**路由**: `/settings/routing`（仅 Admin）

**列表页**：

- 显示所有规则：规则名称、策略类型、优先级、状态（启用/禁用）、操作按钮
- 支持拖拽排序调整优先级
- 开关按钮切换启用/禁用

**新建/编辑规则表单**：

| 字段 | 说明 |
|------|------|
| 规则名称 | 字符串，必填 |
| 分配策略 | 下拉选择（当前工作量/地区/历史成交率）|
| 参与分配的销售 | 多选用户列表 |
| 地区条件（策略为地区时显示）| 输入地区关键词列表（如「华南」「广东」）|
| 优先级 | 数字，越小越优先 |
| 是否启用 | 开关 |

**接口**：

- `GET /api/routing/rules` — 获取全部规则列表
- `POST /api/routing/rules` — 创建规则
- `PUT /api/routing/rules/:id` — 更新规则
- `DELETE /api/routing/rules/:id` — 删除规则
- `PATCH /api/routing/rules/:id/toggle` — 启用/禁用
- `PATCH /api/routing/rules/reorder` — 批量更新优先级（拖拽排序后调用）

---

### 4.8 数据分析模块

**路由**: `GET /api/analytics`

#### 展示指标

| 指标 | 计算方式 |
|------|----------|
| 平均客单价 | 总商机金额 / 客户总数 |
| 成交转化率 | 已成交客户数 / 总客户数 |
| 高优先占比 | priority='高' 客户数 / 总客户数 |

#### 图表

1. **各行业商机价值** — 横向进度条，按金额降序排列
2. **销售漏斗分析** — 梯形漏斗图，每阶段显示人数和金额
3. **月度新增客户趋势**（可选增强）— 折线图，近12个月每月新增客户数

---

### 4.9 用户与权限模块（管理员功能）

#### 权限矩阵

| 功能 | 销售 | 主管 | 管理员 |
|------|------|------|--------|
| 查看自己客户 | ✅ | ✅ | ✅ |
| 查看全部客户 | ❌ | ✅ | ✅ |
| 新建/编辑客户 | ✅（自己的）| ✅ | ✅ |
| 删除客户 | ❌ | ❌ | ✅ |
| 查看全部任务 | ❌ | ✅ | ✅ |
| 消息收件箱（全部）| ❌ | ✅ | ✅ |
| 消息收件箱（自己的）| ✅ | ✅ | ✅ |
| 配置 Routing 规则 | ❌ | ❌ | ✅ |
| 设置销售目标 | ❌ | ❌ | ✅ |
| 用户管理 | ❌ | ❌ | ✅ |
| 系统设置 | ❌ | ❌ | ✅ |

#### 用户管理接口

- `GET /api/users` — 获取用户列表
- `POST /api/users` — 创建用户（发送初始密码邮件）
- `PUT /api/users/:id` — 修改用户信息/角色
- `DELETE /api/users/:id` — 停用账号（软删除）

---

## 五、前端页面结构

```
/login                        登录页
/dashboard                   仪表盘（Admin/Manager 版 或 Sales 版，按角色自动切换）
/contacts                    客户列表（含右侧详情面板）
/contacts/new                新建客户页面（手动录入 + Excel 批量导入）
/pipeline                    销售漏斗看板
/tasks                       任务中心
/inbox                       消息收件箱（WhatsApp + 邮件）
/analytics                   数据分析
/settings                    系统设置（仅管理员）
  /settings/users            用户管理
  /settings/routing          客户分配规则
  /settings/targets          销售目标设置
  /settings/integrations     WhatsApp / 邮件集成配置
  /settings/industries       行业配置
```

---

## 六、UI/UX 规范

### 6.1 整体风格

- **主题**: 深色商务风（Dark Theme）
- **主色**: #3b82f6（蓝）、#8b5cf6（紫）渐变
- **背景**: #080c14（页面背景）、#0d1526（卡片背景）
- **边框**: #1e2d4a
- **文字**: #f1f5f9（主文字）、#94a3b8（次要文字）、#64748b（辅助文字）

### 6.2 状态颜色

| 状态 | 文字颜色 | 背景色 |
|------|----------|--------|
| 潜在客户 | #60a5fa（蓝） | rgba(59,130,246,0.15) |
| 跟进中 | #4ade80（绿） | rgba(34,197,94,0.15) |
| 谈判中 | #fbbf24（黄） | rgba(245,158,11,0.15) |
| 已成交 | #a78bfa（紫） | rgba(139,92,246,0.15) |
| 已流失 | #f87171（红） | rgba(239,68,68,0.15) |

### 6.3 交互规范

- 列表项 hover 时背景加深
- 操作按钮有 loading 状态，防止重复提交
- 表单提交失败显示内联错误提示（非弹窗）
- 删除操作必须二次确认
- 所有列表支持空状态（Empty State）提示
- 数据加载时显示 Skeleton 骨架屏

### 6.5 国际化（i18n）

**实现方案**：`react-i18next` + `i18next`

**支持语言**：

| 语言 | locale key | 说明 |
|------|-----------|------|
| 简体中文 | `zh` | 默认语言 |
| English | `en` | 英文 |

**语言文件结构**：

```
frontend/src/locales/
├── zh/
│   ├── common.json      通用词汇（保存、取消、确认、删除...）
│   ├── dashboard.json   仪表盘相关
│   ├── contacts.json    客户相关
│   ├── tasks.json       任务相关
│   ├── inbox.json       消息相关
│   └── settings.json    设置相关
└── en/
    ├── common.json
    ├── dashboard.json
    ├── contacts.json
    ├── tasks.json
    ├── inbox.json
    └── settings.json
```

**语言切换入口**：

- 位置：所有角色的 Dashboard 页面**右上角**，Header 区域
- 形式：下拉菜单或切换按钮（🇨🇳 中文 / 🇬🇧 English）
- 切换后：
  1. 立即更新前端 i18next 语言（`i18n.changeLanguage(lang)`）
  2. 调用 `PATCH /api/users/me/language` 将偏好持久化到用户表
  3. 下次登录时，前端读取 `currentUser.language` 自动恢复语言

**接口**：

- `PATCH /api/users/me/language` — 请求体 `{ language: "zh" | "en" }`，更新 users.language 字段

**翻译覆盖范围**：所有 UI 文本（页面标题、表单标签、按钮文字、状态名称、错误提示、空状态文字、Toast 通知）均须提供中英文翻译，不得出现硬编码中文字符串。

系统需同时适配桌面端和移动端，使用 Tailwind CSS 断点实现：

| 断点 | 宽度 | 布局策略 |
|------|------|----------|
| 桌面端（lg+）| ≥ 1024px | 固定侧边栏 + 内容区，完整功能 |
| 平板（md）| 768–1023px | 侧边栏可折叠为图标模式 |
| 手机端（sm）| < 768px | 底部 Tab 导航，隐藏侧边栏 |

**移动端专项规范**：

- 侧边栏替换为**底部 Tab Bar**（仪表盘、客户、任务、消息、更多）
- 列表使用卡片式布局，去掉表格形式
- 客户详情从右侧面板改为**全屏抽屉（Drawer）**，从底部滑入
- 销售漏斗看板支持横向滑动浏览各阶段
- 表单字段垂直单列排列（PC 端可双列）
- 按钮、输入框高度不低于 44px（符合移动端点击目标规范）
- 收件箱页面在手机端改为列表 → 点击进入详情页的两级结构
- 所有浮层/弹窗在手机端使用 Bottom Sheet 而非居中 Modal

---

## 七、接口通用规范

### 7.1 请求头

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

### 7.2 统一响应格式

**成功**：
```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功"
}
```

**失败**：
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "邮箱格式不正确",
    "fields": { "email": "格式不正确" }
  }
}
```

### 7.3 HTTP 状态码

| 状态码 | 场景 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未登录/Token 失效 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 八、非功能性需求

| 项目 | 要求 |
|------|------|
| 接口响应时间 | 列表查询 < 500ms，复杂统计 < 2s |
| 并发支持 | 支持 50 人同时在线 |
| 数据安全 | SQL 注入防护、XSS 防护、CSRF 防护 |
| 日志 | 所有增删改操作记录操作日志 |
| 错误追踪 | 服务端错误写入日志文件，格式为 JSON |
| 密码策略 | 最少 8 位，包含字母和数字 |

---

## 九、目录结构建议

```
project/
├── frontend/
│   ├── src/
│   │   ├── components/         通用组件（Button, Modal, Badge, BottomSheet...）
│   │   ├── pages/              页面组件
│   │   │   ├── Dashboard/      （Admin版 + Sales版，按角色渲染）
│   │   │   ├── Contacts/
│   │   │   ├── Pipeline/
│   │   │   ├── Tasks/
│   │   │   ├── Inbox/          消息收件箱
│   │   │   ├── Analytics/
│   │   │   └── Settings/
│   │   │       ├── Users/
│   │   │       ├── Routing/    客户分配规则
│   │   │       ├── Targets/    销售目标
│   │   │       └── Integrations/
│   │   ├── hooks/              自定义 Hooks（useBreakpoint, useAuth...）
│   │   ├── locales/            i18n 翻译文件
│   │   │   ├── zh/             中文（common, dashboard, contacts, tasks, inbox, settings）
│   │   │   └── en/             英文（同上）
│   │   ├── services/           API 请求封装（axios）
│   │   ├── store/              全局状态
│   │   ├── types/              TypeScript 类型定义
│   │   └── utils/              工具函数
│   └── public/
├── backend/
│   ├── app/
│   │   ├── main.py             FastAPI 入口，注册路由和中间件
│   │   ├── config.py           配置（读取 .env，Pydantic BaseSettings）
│   │   ├── database.py         SQLAlchemy async engine & session
│   │   ├── dependencies.py     公共依赖（get_db、get_current_user）
│   │   ├── models/             SQLAlchemy ORM 模型
│   │   │   ├── user.py
│   │   │   ├── contact.py
│   │   │   ├── activity.py
│   │   │   ├── task.py
│   │   │   ├── message.py
│   │   │   ├── routing_rule.py
│   │   │   ├── sales_target.py
│   │   │   └── setting.py
│   │   ├── schemas/            Pydantic 请求/响应 Schema
│   │   │   ├── auth.py
│   │   │   ├── contact.py
│   │   │   ├── task.py
│   │   │   ├── message.py
│   │   │   ├── routing.py
│   │   │   └── user.py
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── contacts.py
│   │   │   ├── tasks.py
│   │   │   ├── dashboard.py
│   │   │   ├── analytics.py
│   │   │   ├── messages.py
│   │   │   ├── webhooks.py     WhatsApp Webhook
│   │   │   ├── routing.py
│   │   │   └── users.py
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   ├── contact_service.py
│   │   │   ├── task_service.py
│   │   │   ├── whatsapp_service.py
│   │   │   ├── email_service.py   （IMAP 收件 + SMTP 发件）
│   │   │   └── routing_service.py （分配逻辑）
│   │   ├── tasks/
│   │   │   └── email_poller.py    APScheduler 定时拉取邮件
│   │   ├── middleware/
│   │   │   └── logging.py
│   │   └── utils/
│   │       ├── security.py
│   │       └── response.py
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   ├── seed.py
│   ├── requirements.txt
│   ├── alembic.ini
│   └── .env.example
├── nginx/
│   ├── nginx.conf              主配置（upstream + 负载均衡）
│   └── conf.d/
│       └── crm.conf            虚拟主机配置
├── docker-compose.yml
└── README.md
```

---

## 十、开发优先级

### P0（必须完成）

1. 认证系统（登录/登出/Token刷新）
2. 客户管理 CRUD（列表、详情面板、编辑、删除）
3. 新建客户页面 `/contacts/new`（手动录入 + Excel 批量导入）
4. 客户状态筛选和搜索
5. Admin 仪表盘（6张 KPI 卡片 + 漏斗 + 排行榜 + GMV 趋势图）
6. Manager 仪表盘（5张团队 KPI + 团队漏斗 + 团队排行榜）
7. Sales 仪表盘（5张 KPI 卡片 + 我的 Pipeline）
8. 响应式布局（Mobile 底部导航 + PC 侧边栏）
9. i18n 中英文支持 + 右上角语言切换

### P1（重要功能）

9. 销售漏斗看板（含拖拽更新状态）
10. 任务中心（增删改查 + 完成切换）
11. 跟进记录（新增和时间线展示）
12. 权限控制（角色隔离数据）
13. 客户分配规则（Routing）— 配置页 + 执行逻辑
14. WhatsApp Webhook 接入 + 自动创建客户
15. Email IMAP 轮询 + 自动创建客户
16. 消息收件箱页面

### P2（增强功能）

17. 数据分析图表
18. GMV 趋势图（月度/年度）
19. 今日任务到期提醒
20. 用户管理（管理员后台）
21. 销售目标设置与目标完成率
22. 月度客户趋势图

---

## 十一、初始数据（种子数据）

系统初始化时需写入以下测试数据，方便开发调试：

- 3 个用户：1 个 admin、1 个 manager、1 个 sales
- 10 个客户（覆盖全部行业和全部状态）
- 5 条任务（含已完成和未完成）
- 每个客户至少 1 条跟进记录

## 十二、后端实现规范（FastAPI + MySQL）

### 12.1 依赖清单（requirements.txt）

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
sqlalchemy[asyncio]==2.0.30
aiomysql==0.2.0              # MySQL 异步驱动
alembic==1.13.1
pydantic[email]==2.7.0
pydantic-settings==2.2.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9
redis==5.0.4
python-dotenv==1.0.1
httpx==0.27.0                # 调用 WhatsApp Graph API
apscheduler==3.10.4          # 邮件定时轮询
aioimaplib==1.1.0            # 异步 IMAP
aiosmtplib==3.0.1            # 异步 SMTP
beautifulsoup4==4.12.3       # 解析 HTML 邮件正文
openpyxl==3.1.2              # Excel 导入解析
```

### 12.2 统一环境变量（.env / .env.example）

**所有环境变量统一放在项目根目录的 `.env` 文件中**，后端通过 `pydantic-settings` 的 `BaseSettings` 读取，前端通过 Vite 的 `import.meta.env` 读取（前端变量须以 `VITE_` 开头）。

```env
# ─────────────────────────────────────────
# 数据库（MySQL）
# ─────────────────────────────────────────
DB_HOST=localhost
DB_PORT=3306
DB_USER=crm_user
DB_PASSWORD=your_db_password
DB_NAME=crm_os

# ─────────────────────────────────────────
# 缓存（Redis）
# ─────────────────────────────────────────
REDIS_URL=redis://localhost:6379/0

# ─────────────────────────────────────────
# JWT 认证
# ─────────────────────────────────────────
SECRET_KEY=your-secret-key-minimum-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# ─────────────────────────────────────────
# 应用配置
# ─────────────────────────────────────────
APP_ENV=development                    # development | production
CORS_ORIGINS=http://localhost:5173

# ─────────────────────────────────────────
# WhatsApp Business Cloud API
# ─────────────────────────────────────────
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_ACCESS_TOKEN=your_permanent_token
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_custom_verify_token
WHATSAPP_APP_SECRET=your_app_secret

# ─────────────────────────────────────────
# 邮件（IMAP 收件 + SMTP 发件）
# ─────────────────────────────────────────
IMAP_HOST=imap.example.com
IMAP_PORT=993
IMAP_USER=crm@example.com
IMAP_PASSWORD=your_imap_password
IMAP_POLL_INTERVAL_SECONDS=60

SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=crm@example.com
SMTP_PASSWORD=your_smtp_password
SMTP_FROM=CRM System <crm@example.com>

# ─────────────────────────────────────────
# 前端（Vite，须加 VITE_ 前缀）
# ─────────────────────────────────────────
VITE_API_BASE_URL=http://localhost/api
VITE_APP_NAME=CRM Pro
VITE_DEFAULT_LANGUAGE=zh              # zh | en
```

**后端读取方式（config.py）**：

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    db_host: str
    db_port: int = 3306
    db_user: str
    db_password: str
    db_name: str

    redis_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    app_env: str = "development"
    cors_origins: str = "http://localhost:5173"

    whatsapp_phone_number_id: str = ""
    whatsapp_access_token: str = ""
    whatsapp_webhook_verify_token: str = ""
    whatsapp_app_secret: str = ""

    imap_host: str = ""
    imap_port: int = 993
    imap_user: str = ""
    imap_password: str = ""
    imap_poll_interval_seconds: int = 60

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

> **安全说明**：`.env` 文件包含敏感凭据，必须加入 `.gitignore`，仓库中只提交 `.env.example`（值全部替换为占位符）。生产环境建议使用 Docker Secrets 或云端 Secret Manager 注入，而非直接挂载 `.env` 文件。

### 12.3 数据库连接（database.py）

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = "mysql+aiomysql://user:pass@host/dbname?charset=utf8mb4"

engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

### 12.4 路由注册（main.py）

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, contacts, tasks, dashboard, analytics, users

app = FastAPI(title="CRM API", version="1.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(auth.router,      prefix="/api/auth",      tags=["认证"])
app.include_router(contacts.router,  prefix="/api/contacts",  tags=["客户"])
app.include_router(tasks.router,     prefix="/api/tasks",     tags=["任务"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["仪表盘"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["分析"])
app.include_router(users.router,     prefix="/api/users",     tags=["用户"])
```

### 12.5 统一响应封装

```python
# utils/response.py
from fastapi.responses import JSONResponse

def ok(data=None, message="操作成功", status_code=200):
    return JSONResponse({"success": True, "data": data, "message": message}, status_code)

def fail(message, code="ERROR", fields=None, status_code=400):
    return JSONResponse({"success": False,
        "error": {"code": code, "message": message, "fields": fields}}, status_code)
```

### 12.6 Alembic 迁移命令

```bash
# 初始化（仅一次）
alembic init alembic

# 生成迁移文件
alembic revision --autogenerate -m "create tables"

# 执行迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

### 12.7 Docker Compose

```yaml
version: "3.9"
services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: 123456
      MYSQL_DATABASE: crm_os
      MYSQL_USER: root
      MYSQL_PASSWORD: 123456
    ports: ["3306:3306"]
    volumes: [mysql_data:/var/lib/mysql]
    command: --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  backend_1:
    build: ./backend
    env_file: ./backend/.env
    environment:
      - INSTANCE_ID=backend_1
    depends_on: [mysql, redis]
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000

  backend_2:
    build: ./backend
    env_file: ./backend/.env
    environment:
      - INSTANCE_ID=backend_2
    depends_on: [mysql, redis]
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000

  nginx:
    image: nginx:1.25-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
    depends_on: [backend_1, backend_2, frontend]

  frontend:
    build: ./frontend
    expose: ["80"]

volumes:
  mysql_data:
```

### 12.8 Nginx 配置（nginx/conf.d/crm.conf）

```nginx
upstream crm_backend {
    least_conn;                          # 最少连接数负载均衡
    server backend_1:8000 weight=1;
    server backend_2:8000 weight=1;
    keepalive 32;
}

server {
    listen 80;
    server_name _;

    # 前端静态资源
    location / {
        proxy_pass http://frontend:80;
        proxy_set_header Host $host;
        try_files $uri $uri/ /index.html;  # SPA fallback
    }

    # API 请求 → 后端负载均衡
    location /api/ {
        proxy_pass http://crm_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 60s;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
    }

    # WhatsApp Webhook（需外网可访问）
    location /api/webhooks/ {
        proxy_pass http://crm_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 健康检查
    location /health {
        proxy_pass http://crm_backend/health;
    }
}
```

> **注意**：WhatsApp Webhook 要求 HTTPS，生产环境需配置 SSL 证书（推荐 Let's Encrypt + Certbot）。两个后端实例共享同一 MySQL 和 Redis，Session/Token 状态通过 Redis 共享，无需担心负载均衡导致的会话丢失。

---

*文档结束。如有疑问，请根据实际情况调整实现细节，核心业务逻辑以本文档为准。*
