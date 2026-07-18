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
