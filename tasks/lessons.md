# 教训记录

## L1 · 间接依赖不锁版本 → pool_pre_ping 全线 500

**现象**：代码未改动，重建镜像后约一半的 DB 请求返回 500：
`TypeError: AsyncAdapt_aiomysql_connection.ping() missing 1 required positional argument: 'reconnect'`

**根因**：不是 SQLAlchemy 或 aiomysql 的问题，而是**未固定的间接依赖 PyMySQL**。

SQLAlchemy `dialects/mysql/pymysql.py` 的 `do_ping()` 靠**反射 PyMySQL 的 `Connection.ping` 签名**来决定怎么调用：

```python
if self._send_false_to_ping:
    dbapi_connection.ping(False)
else:
    dbapi_connection.ping()      # 无参
```

- PyMySQL 1.1.1：`ping(self, reconnect=True)` → 走 `ping(False)` → 正常
- PyMySQL **1.2.0**：`ping(self, reconnect=False)` → 走无参 `ping()` → 而 SQLAlchemy 自己的
  `AsyncAdapt_aiomysql_connection.ping(self, reconnect)` 要求位置参数 → TypeError

`requirements.txt` 里 PyMySQL 由 aiomysql 间接带入、没有固定版本，PyMySQL 1.2.0 一发布，
任何一次重建镜像都会踩中。这是「代码没动却突然坏了」的典型来源。

**修复**：`backend/requirements.txt` 固定 `pymysql==1.1.1`（保留 `pool_pre_ping`）。

**教训**：
1. **先证伪再动手**。最初的两个候选方案（升 SQLAlchemy ≥2.0.31、升 aiomysql）看起来都很合理，
   实测 2.0.31/2.0.32/2.0.36/2.0.41/2.0.43 和 aiomysql 0.3.2 **全部无效**。
   如果直接按「首选方案」改完就提交，会得到一个假修复。
2. **验证必须用真实依赖栈**。SQLite 或 mock 完全测不出这个问题 —— 它只在
   MySQL + aiomysql + 连接池复用 三者同时成立时才触发。
3. **确定性复现优先于概率复现**。用 `pool_size=1` 强制连接复用，把「约 50% 概率」
   变成「稳定交替 OK/FAIL」，才能可靠地判断修没修好。
4. **要做对照实验**。修复后镜像通过不等于是这个改动修好的；必须拿修复前镜像跑同一套测试，
   看到它确实失败，因果才成立。
5. **锁间接依赖**。建议后续用 `pip-compile` 生成带哈希的完整锁文件，
   否则同类问题会在别的传递依赖上重演。

## L2 · 状态标记只在「新建」分支写入 → 迁移后的老数据永远走错路径

**现象**：2026-08-17 真机联调 `whatsapp_gateway` 的 CRM 分支。入站正常
（`POST /internal/whatsapp/inbound 200`），后台手动回复也「成功」了，用户收到了消息，
表面上完全正常。

但网关的 `/internal/whatsapp/outbound` 接口**自部署以来调用次数为 0** ——
回复根本没走网关，是 crm_os 自己直连 Graph API 发出去的。

**根因**：`app/services/whatsapp_service.py` 的 `_handle_message()` 里，
`is_gateway=True` 只写在**新建联系人**的分支内：

```python
if not contact:
    contact = Contact(..., is_gateway=is_gateway)   # 只有这里赋值
# 联系人已存在时，什么都不做
```

测试用的号码在 7 月直连测试时就已入库，`is_gateway` 是默认的 `False`。
走网关进来时这个标记不会被补上，于是 `send_message()` 里
`if contact.is_gateway:` 判断走了 else 分支，回落到直连 Graph API。

**为什么危险**：当时能成功，只是因为 crm_os 自己还持有一份有效 token。
一旦按架构规划把凭据收归网关独占，**所有迁移前就存在的联系人回复都会静默失败**，
而新建联系人一切正常 —— 故障只影响老数据，最难被测试发现。

**修复**：`_handle_message()` 增加 `elif is_gateway and not contact.is_gateway:` 分支，
在已存在的联系人从网关入站时补写标记。新增测试
`test_existing_contact_upgraded_to_gateway` 覆盖。

**教训**：
1. **「成功」不等于「走对了路」**。端到端手工测试只能证明用户收到了消息，
   证明不了它走的是设计的那条链路。要验证链路，得看**中间节点的日志有没有被打到**。
2. **查缺失比查存在更有效**。这个 bug 是靠「网关 outbound 调用次数为 0」发现的，
   不是靠任何一条报错。诊断时主动问一句：按设计**应该出现**但没出现的日志是什么？
3. **迁移引入的布尔标记，必须考虑存量数据**。新增 `is_gateway` 这类字段时，
   除了「新建时赋值」，一定要问「已存在的记录什么时候、由谁补上」。
   本例选择在下次入站时自动补写（幂等、无需数据迁移脚本），
   代价是「再也不发消息进来的老联系人」仍需人工处理。
4. **对照实验同 L1**：新测试先在未修复的代码上跑一遍，确认它**确实失败**
   （`assert contact.is_gateway is True` → 实际 `False`），修复后再跑通，因果才成立。
