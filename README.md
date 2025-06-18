# K8s MCP Agent - Kubernetes集群管理系统

基于Gemini 2.5 Flash和MCP (Model Context Protocol) 的智能Kubernetes集群管理系统。

## 🚀 核心功能

### 1. 智能集群交互 (主应用)
- **文件**: `src/main.py`
- **功能**: 基于LLM Agent的智能K8s集群管理
- **特点**: 自然语言交互，实时集群操作

### 2. 集群扫描系统 (扫描应用)
- **文件**: `src/k8s_scanner.py`
- **功能**: 自动发现MCP工具并扫描集群资源
- **特点**: 定期扫描，数据缓存，资源监控

## 📋 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   用户交互      │    │   集群扫描      │    │   共享层        │
│   (main.py)     │    │ (k8s_scanner.py)│    │                 │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • LLM Agent     │    │ • 工具发现      │    │ • MCP工具       │
│ • 自然语言交互  │    │ • 资源扫描      │    │ • SQLite缓存    │
│ • 实时操作      │    │ • 数据缓存      │    │ • 配置管理      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ K8s MCP Server  │
                    │ (真实K8s集群)   │
                    └─────────────────┘
```

## 🛠️ 快速开始

### 1. 环境配置

创建 `.env` 文件：

```bash
# LLM配置 (Gemini 2.5 Flash)
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL_NAME=google/gemini-2.5-flash
LLM_MAX_INPUT_CONTEXT=1048576
LLM_MAX_OUTPUT_TOKENS=32768
LLM_TEMPERATURE=0.0

# MCP服务器配置
MCP_SERVER_URL=http://your-k8s-mcp-server:port/sse
MCP_SERVER_TYPE=sse
MCP_SERVER_NAME=k8s
```

### 2. 安装依赖

```bash
uv sync
```

### 3. 使用方法

#### 智能集群交互
```bash
# 启动智能Agent
uv run python src/main.py
```

#### 集群扫描系统
```bash
# 发现MCP工具
uv run python src/k8s_scanner.py discover

# 扫描指定集群
uv run python src/k8s_scanner.py scan --cluster production-cluster

# 完整扫描流程 (工具发现 + 集群扫描)
uv run python src/k8s_scanner.py full-scan --cluster production-cluster

# 列出缓存的资源
uv run python src/k8s_scanner.py list
```

## 📊 数据管理

### 缓存数据库
- **位置**: `data/k8s_cache.db`
- **类型**: SQLite
- **内容**: 集群信息、命名空间、节点、Pod、服务、MCP工具

## 🔧 工具和脚本

### 保留的实用工具
- `script/check-scan-env.py` - 环境配置检查
- `script/list-available-tools.py` - 列出可用MCP工具
- `script/query-cache-db.py` - 查询缓存数据库
- `script/verify-scan-status.py` - 验证扫描状态

### 文档
- `script/cluster-scanning-user-guide.md` - 扫描系统用户指南
- `script/cluster-state-caching-system.md` - 缓存系统技术文档
- `script/system-architecture-working-principles.md` - 系统架构原理

## 🏗️ 系统组件

### 核心模块
```
src/
├── main.py                 # 智能Agent主应用
├── k8s_scanner.py         # 集群扫描器主应用
├── llm_config.py          # LLM配置管理
├── cache/                 # 缓存系统
│   ├── cache_manager.py   # 缓存管理器
│   ├── models.py          # 数据模型
│   └── database.py        # 数据库操作
├── scanner/               # 扫描系统
│   ├── tool_discovery.py  # 工具发现
│   ├── cluster_scan_app.py # 集群扫描应用
│   ├── cluster_scanner.py  # 集群扫描器
│   ├── resource_parser.py  # 资源解析器
│   └── scan_coordinator.py # 扫描协调器
└── mcp_tools/             # MCP工具管理
    ├── tool_loader.py     # 工具加载器
    └── models.py          # 工具模型
```

## 🔄 工作流程

### 1. 工具发现流程
1. 通过LLM Agent调用MCP服务器
2. 获取所有可用的K8s MCP工具
3. 解析工具信息（名称、描述、参数等）
4. 缓存工具信息到SQLite数据库

### 2. 集群扫描流程
1. 加载缓存的MCP工具信息
2. 使用Agent调用相应工具扫描集群资源
3. 解析扫描结果
4. 缓存资源信息到SQLite数据库
5. 应用TTL策略管理数据生命周期

### 3. 智能交互流程
1. 用户输入自然语言请求
2. LLM Agent分析用户意图
3. 选择合适的MCP工具或查询缓存
4. 执行操作并返回结果

## 📈 监控和维护

### 扫描状态监控
```bash
# 检查扫描状态
uv run python script/verify-scan-status.py

# 查看缓存统计
uv run python script/query-cache-db.py
```

### 环境检查
```bash
# 验证环境配置
uv run python script/check-scan-env.py
```

## 🚫 已清理的Demo程序

为了保持代码库的整洁，已删除以下demo程序：
- `script/fixed-scan-demo-v2.py`
- `script/fixed-scan-demo.py`
- `script/complete-scan-with-cache.py`
- `script/debug-agent-response.py`
- `script/run-scan-demo.sh`
- `script/run-scanner-demo.py`
- `script/simple-cache-test.py`
- `script/simple-scan-test.py`

## 📝 配置说明

系统遵循十二要素应用方法论，所有配置通过环境变量管理：

- **LLM配置**: OpenRouter API密钥、模型参数
- **MCP配置**: 服务器地址、连接类型
- **缓存配置**: 数据库路径、TTL设置
- **扫描配置**: 扫描间隔、超时设置

## 🔒 安全注意事项

- 生产部署前请移除代码中的私有域名信息
- 确保API密钥安全存储
- 定期更新依赖包
- 监控MCP服务器连接状态

## 📞 支持

如有问题，请查看：
1. 系统架构文档: `script/system-architecture-working-principles.md`
2. 用户指南: `script/cluster-scanning-user-guide.md`
3. 技术文档: `script/cluster-state-caching-system.md`