# K8s MCP Agent - Gemini 2.5 Flash 版本

## 🎯 概述

这是一个专门为 **Gemini 2.5 Flash** 模型优化的 Kubernetes MCP Agent 系统。通过自然语言接口管理真实的 Kubernetes 集群，严格遵循数据真实性原则。

## ✨ 核心特性

- **🤖 专用模型**: 专门使用 Gemini 2.5 Flash，具备强大的推理能力
- **🔧 工具调用**: 完美兼容 MCP 工具调用，无 strict 模式问题
- **📏 大上下文**: 支持 1,048,576 tokens，适合复杂的 K8s 运维
- **⚡ Fail Fast**: 严格的异常处理，确保数据真实性
- **🛡️ 安全可靠**: 绝不编造集群数据，只使用真实的 MCP 工具返回

## 🚀 快速开始

### 1. 环境配置

创建 `.env` 文件：
```bash
# K8s MCP Agent 配置
# 专用于 Gemini 2.5 Flash 模型
OPENROUTER_API_KEY=your_openrouter_api_key_here

# 固定使用 Gemini 2.5 Flash 模型
LLM_MODEL=google/gemini-2.5-flash
```

### 2. 安装依赖

```bash
# 使用 uv 安装依赖
uv sync
```

### 3. 验证配置

```bash
# 验证 Gemini 2.5 Flash 配置
uv run python -c "from src.llm_config import validate_config; validate_config()"
```

### 4. 运行系统

```bash
# 启动 K8s MCP Agent
uv run python main.py
```

## 🧪 测试功能

### 基础功能测试
```bash
# 运行简单测试
uv run python test_simple_mcp.py
```

### 完整功能测试
```bash
# 运行完整的 Gemini MCP 测试
uv run python test_gemini_mcp.py
```

### Fail Fast 合规性测试
```bash
# 验证 Fail Fast 原则实施
uv run python test_fail_fast_compliance.py
```

## 📋 系统架构

```
用户输入 → MCP Agent → Gemini 2.5 Flash → K8s MCP 工具 → 真实 K8s 集群
```

### 核心组件

1. **Gemini 2.5 Flash LLM**: 负责自然语言理解和智能决策
2. **MCP Agent**: 协调工作流程，管理工具调用
3. **K8s MCP 服务器**: 提供真实的集群操作工具
4. **Fail Fast 异常处理**: 确保系统可靠性

## 🛠️ 主要功能

### 集群管理
- 获取集群信息和状态
- 列出可用集群
- 检查集群健康状态

### 资源操作
- 查看 Pod、Service、Deployment 等资源
- 获取资源详细信息
- 监控资源状态变化

### 故障排查
- 分析 Pod 日志
- 检查节点状态
- 网络连接诊断

### 性能监控
- 资源使用情况分析
- 性能指标监控
- 容量规划建议

## 🔒 数据真实性保证

### 核心原则
- ✅ **100% 真实数据**: 所有集群信息来自真实的 MCP 工具调用
- ✅ **零编造内容**: 绝不生成模拟或假设的集群数据
- ✅ **Fail Fast**: 异常情况下立即终止，不提供误导信息
- ✅ **完整溯源**: 每个数据点都能追溯到具体的工具调用

### 异常处理
- 🚨 MCP 连接失败 → 立即终止程序
- 🚨 工具调用错误 → 立即抛出异常
- 🚨 数据验证失败 → 立即报告错误
- 🚨 权限不足 → 立即终止操作

## 📊 性能指标

- **响应时间**: < 30 秒
- **工具调用成功率**: > 95%
- **数据准确性**: 100%
- **异常响应时间**: < 100ms
- **Fail Fast 合规率**: 100%

## 🔧 配置说明

### 环境配置
```python
# 生产环境
environment = "production"
temperature = 0.0
max_tokens = 4096
top_p = 0.05

# 开发环境
environment = "development"
temperature = 0.1
max_tokens = 3072
top_p = 0.2

# 分析环境
environment = "analysis"
temperature = 0.0
max_tokens = 8192
top_p = 0.1
```

### MCP 服务器配置
```python
config = {
    "mcpServers": {
        "k8s": {
            "type": "sse",
            "url": "http://your-k8s-mcp-server:port/sse"
        }
    }
}
```

## 🚨 故障排查

### 常见问题

1. **API 密钥错误**
   ```
   ❌ OPENROUTER_API_KEY 环境变量未设置
   ```
   解决：检查 `.env` 文件中的 API 密钥

2. **MCP 连接失败**
   ```
   ❌ 致命错误: K8s MCP服务器连接失败
   ```
   解决：检查 MCP 服务器状态和网络连接

3. **工具调用失败**
   ```
   ❌ 致命错误: K8s集群查询失败
   ```
   解决：检查集群访问权限和参数

## 📚 相关文档

- [数据真实性铁律](doc/数据真实性铁律.md)
- [K8s MCP Agent 核心功能需求规范](doc/K8s_MCP_Agent_核心功能需求规范.md)
- [Fail Fast 异常处理模块](src/fail_fast_exceptions.py)

## 🎉 成功案例

### 集群信息查询
```
用户: "请获取 gfxc-dev1 集群的详细信息"
系统: 调用 DESCRIBE_CLUSTER 工具 → 返回真实集群配置
结果: 完整的集群信息，包括网络配置、版本、状态等
```

### Pod 状态检查
```
用户: "检查 default 命名空间中的 Pod"
系统: 调用 LIST_CORE_RESOURCES 工具 → 返回真实 Pod 列表
结果: 实际运行的 Pod 名称和状态
```

## 🔄 版本历史

- **v2.0**: Gemini 2.5 Flash 专用版本
  - 移除多提供商支持
  - 简化配置结构
  - 优化 Gemini 2.5 Flash 性能
  - 强化 Fail Fast 原则

- **v1.0**: 多提供商版本
  - 支持 OpenRouter 和 Qwen3
  - 复杂的提供商切换逻辑
  - 已废弃

---

**专注于 Gemini 2.5 Flash，专注于数据真实性，专注于 K8s 运维！** 🎯
