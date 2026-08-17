# 任务：把 demo 数据从真实业务视图里排除

> 提出时间：2026-08-18
> 背景：`whatsapp_gateway` 的 CRM demo 上线后，每个来体验的访客都会在真实 CRM 里
> 创建 `Contact` + 一条 `status=lead` 的 `Deal` + 若干 `Message`，污染真实业务数据。
> `Contact.is_gateway` 字段已存在，且有索引 `idx_contacts_is_gateway`，过滤成本很低。

## 核心取舍

**收件箱必须保留 demo 会话。** CRM demo 的卖点就是「消息进到 CRM 后台，由真人回复」——
如果把 demo 联系人从所有地方排除掉，客服就没法回复，demo 本身就废了。

所以口径是：**排除出「统计与业务列表」，保留在「收件箱与单条会话」**。

| 视图 | 是否排除 demo | 理由 |
|------|--------------|------|
| Dashboard KPI / 漏斗 | ✅ 排除 | demo 会虚增新增线索数、商机数 |
| Analytics 图表 | ✅ 排除 | 同上 |
| 联系人列表 | ✅ 排除 | 销售不该看到一堆 demo 访客 |
| 商机列表 / Pipeline | ✅ 排除 | demo Deal 全是 amount=0 的 lead，污染漏斗 |
| **消息收件箱** | ❌ 保留 | 客服要在这里回复 demo 访客 |
| **联系人详情（按 id 查）** | ❌ 保留 | 从收件箱点进去要能打开 |

## 实施拆分（按「超 3 个文件先拆分」规则分两阶段）

### 阶段 A —— 统计口径（3 个文件）✅ 2026-08-18 完成

- [x] 新增 `backend/app/utils/demo_scope.py`，提供三个查询谓词：
  - `contact_not_demo()` → `Contact.is_gateway.is_(False)`
  - `deal_not_demo()` → `Deal.contact_id.notin_(...)`。`Deal.contact_id` 是 NOT NULL，裸 `notin_` 安全
  - `message_not_demo()` → **`Message.contact_id` 可空**，而 `NULL NOT IN (...)` 求值为 NULL 会把
    行整个滤掉，所以必须显式 `or_(Message.contact_id.is_(None), ...)`，否则无联系人的邮件会被静默丢弃
- [x] `backend/app/services/dashboard_service.py`：把 `_deal_alive()` / `_contact_alive()`
      改名为 `_deal_in_stats()` / `_contact_in_stats()` 并在body里合入谓词。
      **这个文件里 24 处统计查询全部走这两个 helper，改 helper 即全覆盖**（admin / manager /
      sales 三套看板 + 两个漏斗），不需要逐个调用点改
- [x] `backend/app/routers/analytics.py`：`_get_scoped_deal_conditions()` 加 `deal_not_demo()`
      （该 router 所有 Deal 查询都由它构造），渠道分布查询加 `message_not_demo()`

验收：新增 `backend/tests/test_demo_scope.py` 3 项测试，红绿对照通过 —— 未加过滤时
`test_admin_dashboard_excludes_demo` 和 `test_analytics_deal_scope_excludes_demo` 断言失败，
加上后全套 11 项通过。

踩到的坑：analytics 端点本身无法在测试里跑，它的趋势查询用了 MySQL 专有的 `func.date_format`，
SQLite 报 `OperationalError`。改成直接测 `_get_scoped_deal_conditions()` 构造出的条件列表 ——
那才是本次真正改动的地方。（`dashboard_service` 的 manager 看板同样用了 MySQL 专有的
`func.datediff`，目前测试只覆盖 admin 看板。）

### 阶段 B —— 业务列表（3 个文件）

- [ ] `backend/app/services/contact_service.py` 的 `list_contacts()`
- [ ] `backend/app/services/deal_service.py` 的 `list_deals()`
- [ ] `backend/app/routers/pipeline.py`

验收：断言 demo 联系人不出现在联系人列表和 pipeline，但 `get_contact(id)` 仍能查到

### 明确不动

- `backend/app/routers/messages.py` —— 收件箱和单会话，保留 demo
- `contact_service.get_contact()` —— 按 id 查单个，保留

## 可选项（本次不做，需要再说）

- 前端加「显示 demo 数据」开关，把过滤做成可切换而不是硬排除
- `tasks` / `activities` / `sales_targets` 视图：当前 demo 流程不产生这些数据，暂不处理
- 给 demo 联系人在收件箱里加一个视觉标记（如「DEMO」徽章），避免客服误以为是真实客户
- 历史 demo 数据清理：现有的 demo 联系人已经带 `is_gateway=True`，加过滤后自动生效，
  不需要数据迁移；如果想彻底删除，另开任务

## 评审记录

（实施后填写）
