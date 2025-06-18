# 📋 项目评审 TODO 列表

> 目标：列出当前代码库中 **偏离"Gemini 2.5 Flash + MCP Tool 定期扫描 K8s 并写入 SQLite"核心需求** 的问题或风险，按优先级排序，后续逐项整改。

---

## ⛳ HIGH ‑ 优先级最高（立即修复 / 决定性阻塞）

1. **`src/cache` 模块缺失**  
   - 多处代码（`ClusterScanApp`、`RealClusterScanApp`、`ScanCoordinator` 等）导入 `src.cache.*`。当前仓库未包含任何 `src/cache` 目录或实现，程序将直接 `ImportError` ⛔。
2. **SQLite 数据层完全未落地**  
   - 缓存/持久化逻辑依赖 `CacheManager`，但其实现缺失 ⇒ 无法真正把扫描结果写入 SQLite，与原始需求严重偏离。
3. **"定期扫描"调度缺位**  
   - `ClusterScanApp` / `ScanCoordinator` 仅提供手动调用示例，没有后台计划任务（`asyncio` loop / cron / APScheduler 等）来持续扫描集群。
4. **`ClusterScanner` 未使用传入的 `MCPToolLoader` 也不校验可用工具**  
   - 直接调用 Agent，若工具不存在运行期才报错 → 与"Fail-Fast、预加载工具"设计冲突。
5. **关键路径对 `mcp_use.MCPAgent` 的调用假定为 `async`，可能类型不匹配**  
   - `await self.agent.run(...)` 被 `asyncio.wait_for` 包裹，但 Upstream 库 `mcp_use` 暂无异步接口文档，存在运行时阻塞或类型错误风险。
6. **模块路径通过 `sys.path.insert` 临时注入**  
   - 多处脚本在运行时修改 `sys.path` 指向项目根，破坏模块化 & 可部署性，需用正确的 Python 包结构或入口脚本解决。
7. **批量重复代码 & 职责分散**  
   - `cluster_scan_app.py` 与 `real_cluster_scan_app.py` 有大量复制粘贴 → 维护成本高，易出现功能漂移。

---

## 🚧 MEDIUM ‑ 中优先级（近期修复 / 设计改进）

1. **TTL / 过期策略实现不完整**  
   - `ResourceParser` 为模型对象填充 `ttl_expires_at`，但 `ClusterScanner` 产生的 `raw_data` 不包含 TTL，`CacheManager` 如何利用 TTL 未定义。
2. **`CacheManager` 接口假定存在 `to_dict()`**  
   - 多处直接调用 `obj.to_dict()`；部分解析器返回原始 `dict`，一致性有待统一。
3. **Secrets 处理可能泄露元数据**  
   - 当前仅剔除 `data` 字段，但仍保存 `binary_data_keys`、labels 等，需要再次评估安全合规性。
4. **`llm_config` 使用 `langchain_openai.ChatOpenAI`**  
   - 依赖外部 OpenRouter 代理实现 Gemini；需确认实际兼容性、速率限制与超长上下文是否可达。
5. **异常链路过长，缺少复用**  
   - `create_exception_context` 无细节，多个自定义异常含义重叠。需要统一错误语义、防止日志噪音。
6. **单元测试覆盖盲区**  
   - 测试目录引用 `src.cache`，当前全数跳过；CI 通过率被虚高掩盖。
7. **文档与实现脱节**  
   - 文档描述支持"所有 K8s 资源类型、1M tokens Context"，实际扫描/解析覆盖有限；应更新文档或补齐实现。

---

## 📌 LOW ‑ 低优先级（优化 / 清理）

1. **代码规范违背自订标准**  
   - 多文件 >150 行 / 函数 >40 行（与 `python-coding-standards.md` 不符）。
2. **硬编码 Demo 数据**  
   - `ClusterScanApp._parse_*` 中大量示例值（版本、IP）→ 应依赖真实返回或删除 Demo 代码。
3. **重复环境变量校验逻辑**  
   - 多个模块各自 `_validate_environment`，可集中到统一配置管理。
4. **日志格式不统一**  
   - `print()` 与 `logging` 混用，未来需换成结构化日志。
5. **Notebook / 脚本路径引用**  
   - `PROJECT_ROOT` 计算方式略显脆弱，迁移时易失效。

---

## 📈 后续步骤建议

1. 首先落地 `src/cache`（SQLite schema + DAO）并修复所有导入。  
2. 引入调度器（如 `APScheduler` 或自写 `asyncio` loop）→ 支持静态 & 动态 TTL 扫描。  
3. 统一 `MCPToolLoader`、`ClusterScanner`、`*ScanApp` 的依赖关系，移除重复代码。  
4. 补齐单元测试，CI 必须真正运行代码而不是 `pytest -k "not implemented"`。  
5. 完成后再对文档与代码进行一次同步审校，确保描述与实现一致。

---

> **备注**：以上排序依据对"能否运行 & 是否满足业务目标"的影响程度评估，如有遗漏请在后续 Review 中补充。 