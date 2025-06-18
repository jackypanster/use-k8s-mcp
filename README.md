# use-k8s-mcp

Kubernetes MCP Agent with Gemini 2.5 Flash

## 📁 项目结构

```
use-k8s-mcp/
├── src/                    # 源代码
│   ├── llm_config.py      # 核心LLM配置模块 (Gemini 2.5 Flash)
│   ├── main.py            # 主程序
│   └── fail_fast_exceptions.py # Fail-fast异常处理
├── test/                   # 测试
│   └── test_llm_config.py # LLM配置测试
├── doc/                    # 文档
│   ├── README.md          # 详细说明文档
│   ├── MCP_TROUBLESHOOTING.md # MCP故障排除
│   └── TROUBLESHOOTING.md # 故障排除
├── script/                 # 部署脚本
│   └── deploy-vllm.sh     # VLLM部署脚本
├── .env                    # 环境配置
├── main.py                 # 主程序入口点
└── pyproject.toml         # 项目配置
```

## 🚀 快速开始

### 1. 安装依赖
```bash
uv sync
```

### 2. 配置环境
创建 `.env` 文件，配置所有必需的环境变量：

```bash
# ====== LLM 提供商配置 ======
# OpenRouter API 密钥 - 用于访问 Gemini 2.5 Flash 模型
OPENROUTER_API_KEY=your_openrouter_api_key_here

# OpenRouter API 基础 URL
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# LLM 提供商名称
LLM_PROVIDER_NAME=OpenRouter

# ====== 模型配置 ======
# Gemini 2.5 Flash 模型名称
LLM_MODEL_NAME=google/gemini-2.5-flash

# 最大输入上下文长度 (tokens)
LLM_MAX_INPUT_CONTEXT=1048576

# 最大输出 tokens 数量
LLM_MAX_OUTPUT_TOKENS=32768

# 请求超时时间 (秒)
LLM_REQUEST_TIMEOUT=600

# ====== 模型行为配置 ======
# 温度设置 (0.0-1.0)
LLM_TEMPERATURE=0.0

# Top-p 采样参数 (0.0-1.0)
LLM_TOP_P=0.05

# 最大重试次数
LLM_MAX_RETRIES=5

# 随机种子
LLM_SEED=42

# ====== MCP 服务器配置 ======
# K8s MCP 服务器 URL
MCP_SERVER_URL=http://your-k8s-mcp-server:port/sse

# MCP 服务器类型
MCP_SERVER_TYPE=sse

# MCP 服务器名称
MCP_SERVER_NAME=k8s

# ====== 安全配置 ======
# 安全停止序列 (用逗号分隔)
LLM_SAFETY_STOP_SEQUENCES=```bash,```sh,```shell,rm -rf,kubectl delete,docker rmi,sudo rm

# ====== 应用配置 ======
# 应用环境
APP_ENVIRONMENT=production

# 日志级别
LOG_LEVEL=INFO

# 是否启用详细日志
VERBOSE_LOGGING=false
```

> 💡 **配置说明**: 项目遵循十二要素应用方法论，所有配置通过环境变量管理，支持不同部署环境的灵活配置。

### 3. 运行程序
```bash
# 运行主程序
uv run python main.py
```

> 💡 **提示**: 如果遇到MCP连接错误，请查看 [MCP故障排除指南](doc/MCP_TROUBLESHOOTING.md)

### 4. 运行测试
```bash
# 运行配置测试
uv run python test/test_llm_config.py
```

## 📚 文档

详细文档请查看 `doc/` 目录：

- **[详细说明](doc/README.md)** - 完整的项目说明
- **[MCP故障排除](doc/MCP_TROUBLESHOOTING.md)** - MCP连接问题解决
- **[故障排除](doc/TROUBLESHOOTING.md)** - 其他常见问题

## 🔧 核心特性

- **🤖 专用模型**: 专门使用 Gemini 2.5 Flash，具备强大的推理能力
- **🔧 工具调用**: 完美兼容 MCP 工具调用
- **📏 大上下文**: 支持 1,048,576 tokens，适合复杂的 K8s 运维
- **⚡ Fail Fast**: 严格的异常处理，确保数据真实性
- **🛡️ 安全可靠**: 绝不编造集群数据，只使用真实的 MCP 工具返回
- **⚙️ 环境配置**: 遵循十二要素应用方法论，所有配置通过环境变量管理
- **🔒 安全第一**: API 密钥和敏感配置外部化，支持不同部署环境

## 🔧 开发

### 项目结构说明

- **`src/`** - 所有源代码文件
- **`test/`** - 测试文件
- **`doc/`** - 项目文档
- **`script/`** - 部署和运维脚本

### 运行测试

```bash
# 运行配置测试
uv run python test/test_llm_config.py
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License
