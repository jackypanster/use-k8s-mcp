# MCP连接问题故障排除指南

## 🚨 问题描述

运行 `uv run python main.py` 时出现以下错误：

### 1. MCP服务器连接失败
```
httpcore.ConnectError
Error in SseConnectionManager task: unhandled errors in a TaskGroup
Both transport methods failed. Streamable HTTP: Connection closed, SSE: unhandled errors in a TaskGroup
```

### 2. MCPAgent内部错误
```
AttributeError: 'MCPAgent' object has no attribute '_tools'
```

## 🔍 问题分析

### 根本原因
1. **网络连接问题**: 无法连接到外部MCP服务器 `https://mcp.api-inference.modelscope.net/da81fcffd39044/sse`
2. **库版本兼容性**: `mcp-use` 库在连接失败时的错误处理不完善
3. **依赖问题**: 项目重组后缺少必要的依赖包

### 影响范围
- MCP功能无法使用
- 但LLM配置系统本身工作正常

## 🛠️ 解决方案

### 方案1: 使用独立模式（推荐）

**适用场景**: 主要关注LLM配置功能，不需要MCP服务器

```bash
# 运行独立版本（不依赖MCP）
uv run python standalone.py
```

**优势**:
- ✅ 完全独立运行
- ✅ 展示所有LLM配置功能
- ✅ 支持提供商切换
- ✅ 包含完整测试

### 方案2: 修复MCP连接

**适用场景**: 需要使用MCP功能

#### 2.1 检查网络连接
```bash
# 测试MCP服务器连接
curl -I https://mcp.api-inference.modelscope.net/da81fcffd39044/sse

# 检查代理设置
echo $HTTP_PROXY
echo $HTTPS_PROXY
```

#### 2.2 更换MCP服务器
编辑 `src/main.py`，更换为可用的MCP服务器：

```python
config = {
    "mcpServers": {
        "fetch": {
            "type": "sse",
            "url": "your-working-mcp-server-url"  # 替换为可用的服务器
        }
    }
}
```

#### 2.3 使用本地MCP服务器
```bash
# 启动本地MCP服务器（如果有的话）
# 然后修改配置指向本地服务器
```

### 方案3: 降级mcp-use版本

```bash
# 尝试使用较早版本
uv remove mcp-use
uv add "mcp-use==0.1.0"  # 或其他稳定版本
```

## 🧪 验证解决方案

### 测试LLM配置系统
```bash
# 运行独立测试
uv run python standalone.py

# 运行配置测试
uv run python run_tests.py

# 测试提供商切换
uv run python switch_provider.py status
```

### 测试MCP功能（如果修复了连接）
```bash
# 运行原始主程序
uv run python main.py
```

## 📋 当前状态总结

### ✅ 正常工作的功能
- LLM配置系统
- 提供商切换（OpenRouter ↔ Qwen3）
- 多环境配置（production, development, analysis）
- 配置验证和测试
- Kubernetes专用配置

### ❌ 受影响的功能
- MCP Agent功能
- 外部工具集成
- 网页抓取等MCP服务

### 🎯 推荐使用方式

**日常开发**: 使用独立模式
```bash
uv run python standalone.py
```

**MCP功能**: 等待网络问题解决或使用本地MCP服务器

## 🔧 预防措施

### 1. 网络配置
- 确保网络连接稳定
- 配置正确的代理设置
- 检查防火墙规则

### 2. 依赖管理
- 定期更新依赖
- 锁定稳定版本
- 测试兼容性

### 3. 错误处理
- 添加连接超时设置
- 实现优雅降级
- 提供备用方案

## 📞 获取帮助

如果问题仍然存在：

1. **检查日志**: 查看详细错误信息
2. **网络诊断**: 确认网络连接状态
3. **版本兼容**: 验证所有依赖版本
4. **社区支持**: 查看mcp-use项目的Issue

## 🎉 成功案例

使用独立模式的成功输出示例：
```
🚀 独立LLM配置系统演示
============================================================
🤖 当前LLM提供商: Qwen3-32B (内网)
🔗 服务地址: http://10.49.121.127:8000/v1
============================================================
🏁 测试完成: 4/4 通过
🎉 所有测试通过! LLM配置系统工作正常
```

这表明核心功能完全正常，可以放心使用！
