# crm_os 任务清单

---

# 任务一：把 demo 数据从真实业务视图里排除（✅ 已完成）

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

### 阶段 B —— 业务列表（3 个文件）✅ 2026-08-18 完成

- [x] `backend/app/services/contact_service.py` 的 `list_contacts()` 加 `contact_not_demo()`
      （列表、总数、排序共用同一个 `query`，一处即全覆盖；`_bulk_deal_summary()` 拿的是已过滤的
      contact_ids，不用改）
- [x] `backend/app/services/deal_service.py` 的 `list_deals()` 加 `deal_not_demo()`
- [x] `backend/app/routers/pipeline.py`：该文件已有一个「排除已删除/已归档联系人」的子查询，
      把 `contact_not_demo()` 加进那个子查询即可 —— 两个查询都用 `*base_where`，比再套一层
      `deal_not_demo()` 子查询干净

验收：红绿对照通过 —— 未加过滤时 3 项断言失败（`assert 2 == 1`），加上后全套 **15 项通过**。
其中 `test_demo_contact_still_reachable_by_id` 专门守住那个刻意保留的口子。

### 明确不动

- `backend/app/routers/messages.py` —— 收件箱和单会话，保留 demo
- `contact_service.get_contact()` —— 按 id 查单个，保留

## ⚠️ 已知的遗留问题：`is_gateway` 语义重载（真实号码上线前必须解决）

`Contact.is_gateway` 现在**同时表示两件事**：

1. 「消息从共享网关进来的」—— 传输方式
2. 「是 demo 访客」—— 业务性质

今天这两者重合，因为只有测试号一个号码，所以本任务的过滤是正确的。

**但按多号码架构，真实业务号也会走同一个网关**（见 `whatsapp_gateway/docs/multi-number-architecture.md`）。
到那时真实客户也会带 `is_gateway=True`，本任务加的过滤会**把真实线索从联系人列表、
商机列表、管道和看板里全部藏起来** —— 与「每个新进来的顾客指派给销售跟进」的需求完全相反。

**解决方向**（属于网关设计文档的阶段 4）：网关在转发时带上消息落在哪个号码/哪条线上，
crm_os 据此区分，而不是靠「是否经过网关」。届时把 `is_gateway` 拆成
「传输来源」和「是否 demo」两个概念。

2026-08-18 与用户确认：先按当前方案上线（方案 A），真实号码落地时一并处理。

## 可选项（本次不做，需要再说）

- 前端加「显示 demo 数据」开关，把过滤做成可切换而不是硬排除
- `tasks` / `activities` / `sales_targets` 视图：当前 demo 流程不产生这些数据，暂不处理
- 给 demo 联系人在收件箱里加一个视觉标记（如「DEMO」徽章），避免客服误以为是真实客户
- 历史 demo 数据清理：现有的 demo 联系人已经带 `is_gateway=True`，加过滤后自动生效，
  不需要数据迁移；如果想彻底删除，另开任务

## 评审记录

- 2026-08-18：`dashboard_service.py` 里 24 处统计查询全部走 `_deal_alive()` / `_contact_alive()`
  两个 helper，改 helper 即全覆盖三套看板和两个漏斗，不必逐个调用点改。同理 `analytics.py`
  的所有 Deal 查询都由 `_get_scoped_deal_conditions()` 构造，`pipeline.py` 已有一个联系人子查询。
  **动手前先找 choke point，比逐处加过滤省一个数量级的改动量，也不会漏。**
- 2026-08-18：`Message.contact_id` 可空，`NULL NOT IN (...)` 在 SQL 里求值为 NULL 会把整行滤掉，
  差点静默丢弃所有无联系人的邮件。可空外键上写 `notin_` 一律要配 `is_(None)` 分支。
- 2026-08-18：analytics 端点无法在测试里跑（趋势查询用 MySQL 专有的 `func.date_format`，
  SQLite 报 `OperationalError`），改成直接测被修改的 `_get_scoped_deal_conditions()`。
  `dashboard_service` 的 manager 看板同样用了 `func.datediff`，目前测试只覆盖 admin 看板。

---

# 任务二：WhatsApp 多客服协作（规划中）

> 提出时间：2026-08-18
> 需求：「每个新进来的 CRM 顾客，指派给一个销售人员跟进」，一个 WhatsApp 号码多人共用。
> 平台层面这是可行的 —— 号码接进 Cloud API 后就没有 WhatsApp App 那一层了，
> 谁处理哪个会话完全由 CRM 决定。**注意：号码一旦注册到 Cloud API，
> 就不能再在 WhatsApp Business App 里使用**，员工必须在 CRM 里工作。

## 已经具备的能力（不用重做）

| 能力 | 位置 |
|------|------|
| 新联系人自动分派，三种策略（工作量 / 区域 / 赢率）+ 可配规则优先级 | `routing_service.assign_contact()` |
| 找不到匹配规则时兜底取第一个在职 sales | `routing_service.assign_contact()` 末尾 |
| 收件箱按角色隔离：sales 只看自己、manager 看团队、admin 看全部 | `routers/messages.py:31-38` |
| 从 CRM 后台回复并经网关发出 | 已于 2026-08-17 真机验证 |

## 核实过的缺口（以下均已读代码确认，非推测）

### 缺口 1 · 批量导入的联系人可能完全没有负责人 —— 严重度：高

`import_contacts()` 的负责人取自 `assigned_to_email` 列；该列为空时，**只有当导入者本人是
sales 角色**才回落到导入者自己。**管理员导入一批没有负责人列的线索 → 全部 `assigned_to = None`。**

后果：这些线索在销售和主管的**联系人列表和收件箱里完全不可见**（两处都按 `assigned_to` 过滤），
只有管理员看得到，且没有任何告警。而且 import 这条路径**根本不调用路由引擎**，
与 WhatsApp / 邮件 / 手工创建三条入口的行为不一致。

- [ ] 修复：`import_contacts()` 在没有显式负责人时调用 `routing_service.assign_contact()`

### 缺口 2 · 转派后历史消息留在原负责人名下 —— 严重度：高

`Message.assigned_to` 是消息创建时从 `contact.assigned_to` 拷贝的快照。
`contact_service.update_contact()` 修改 `contact.assigned_to` 时**不会同步已有的 Message 行**。

后果：把客户转给同事后，接手的人（sales 角色）在收件箱里**看不到任何历史消息**，
原负责人反而还看得到。多客服场景下这条最致命 —— 转派等于丢上下文。

- [ ] 修复：`update_contact()` 改动 `assigned_to` 时，同步更新该联系人名下的 Message
- [ ] 或者改为收件箱不按 `Message.assigned_to` 过滤，而是 join 到 `Contact.assigned_to`
      （去掉冗余字段，从根上消除不同步；需评估对邮件等无联系人消息的影响）

### 缺口 3 · 没有会话级的转派与认领机制 —— 严重度：中

只能通过改联系人的 `assigned_to` 来换人，没有会话级的转派或认领接口，
也没有「他人正在处理」的标记 —— 两个销售可能同时回复同一个客户，
而 WhatsApp 那一侧看不出是谁回的。

- [ ] 设计：认领 / 转派接口 + 简单的并发保护（如回复前校验当前归属）
- [ ] 可选：出站消息记录实际操作人，与「归属人」区分开

### 缺口 4 · 悬空会话没有兜底 —— 严重度：低（但影响面大）

因为 `assign_contact()` 有兜底逻辑，只要系统里有至少一个在职 sales，
WhatsApp / 邮件 / 手工创建这三条路径几乎总能分到人。**（这一条我最初高估了严重度，
实际核实后发现路由兜底覆盖了绝大多数情况，真正的悬空来源是上面的缺口 1。）**

剩余风险：`assigned_to = None` 的联系人对 sales 和 manager 完全不可见且无告警。

- [ ] 加一个「未分派」视图或告警，让悬空线索不至于无声无息

## 建议顺序

缺口 1 → 缺口 2 → 缺口 3。前两个是明确的 bug，各自独立、可单独验收；
缺口 3 是新功能，需要先定交互再动手。缺口 4 可以并进缺口 1 一起做。

## 实施前须知

按项目规则，每个缺口**先写能重现的测试**，并在未修复的代码上确认它确实失败。
本地无 Docker 且依赖钉死旧版本，测试在 VPS 上用 `ghcr.io/kelvinpang90/crm_os-backend:latest`
镜像挂载临时副本跑（见任务一的做法）。

## 实施拆分（2026-08-18 用户确认三条需求后细化）

用户明确的三条：
1. 批量导入时询问是否自动指派负责人，且可选择指派逻辑
2. 转派后历史消息要转给新负责人
3. 销售发消息时，判断当前客户是否在该销售名下

按「超 3 个文件先拆分」拆成四个子任务，按风险从低到高排：

### 2.1 转派带走历史消息（需求 2）—— 1 个文件 ✅ 2026-08-18 完成

- [x] `contact_service.update_contact()`：在 setattr 循环**之前**先算出 `reassigned`
      （循环会把 `contact.assigned_to` 覆盖掉，之后就比不出变化了），
      然后 `UPDATE messages SET assigned_to = ? WHERE contact_id = ?`
- [x] 测试 `backend/tests/test_contact_reassign.py` 两项：转派后历史消息归属跟着变；
      只改其他字段时不动消息（避免误伤）

红绿对照：未修复时 `test_reassign_transfers_message_history` 失败，修复后全套 17 项通过。

注意：**不动 Deal.assigned_to**。商机归属牵涉业绩归属和提成，不能顺手改，
需要单独决策。

### 2.2 发送前校验客户归属（需求 3）—— 1 个文件 ✅ 2026-08-18 完成

用户定的口径：销售发给非自己名下的客户 → 拒绝；主管可发团队成员名下的；
管理员不受限；**无负责人的客户只有管理员能发，或先分派给人之后才能发**。

- [x] `routers/messages.py` 新增 `_may_message_contact()`，`/whatsapp/send` 和
      `/email/send` 在调用 service **之前**校验，不通过返回 403 `NOT_ASSIGNED`
- [x] 测试 `backend/tests/test_message_permission.py`：9 组权限矩阵 + 1 项端点测试
      （断言 403 且下游 service 一次都没被调用）

实现要点：「无负责人只有管理员能发」不需要特判 —— `assigned_to = None` 既不等于
销售自己的 id，也不在主管的团队列表里，非管理员自动被拒。查不到的联系人同样按拒绝
处理，不泄露它是否存在。

红绿对照：部署版本上越权发送返回 **200 且消息真的发出去了**（mock 被调用），
加守卫后返回 403 且下游未被调用，全套 27 项通过。

### 2.3 导入自动指派 —— 后端（需求 1）—— 3 个文件

- [ ] `routing_service.py`：暴露一个按指定策略分派的入口（现有 `assign_contact()`
      走的是规则引擎，策略是规则里配的，不能由调用方指定）
- [ ] `contact_service.import_contacts()`：新增 `auto_assign` / `assign_strategy` 参数
- [ ] `routers/contacts.py` 的 `POST /import`：multipart 表单新增这两个字段

### 2.4 导入自动指派 —— 前端（需求 1）—— 2 个文件

- [ ] `frontend/src/pages/Contacts/ExcelImport.tsx`：加「自动指派负责人」开关 + 策略下拉
- [ ] `frontend/src/services/contacts.ts`：`importContacts()` 带上新参数
