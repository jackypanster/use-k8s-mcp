# Use K8s MCP

A Python project demonstrating the integration of MCP (Model Context Protocol) with OpenRouter API for AI-powered search capabilities.

## 🚀 Features

- **MCP Integration**: Uses MCP (Model Context Protocol) for tool-based AI interactions
- **OpenRouter API**: Configured to work with OpenRouter for accessing various AI models
- **Google Search**: Demonstrates AI-powered search functionality through MCP tools
- **Async Support**: Built with async/await for efficient API calls

## 📋 Prerequisites

- Python 3.13+
- OpenRouter API key
- Virtual environment support

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd use-k8s-mcp
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv .venv

   # On Windows
   .venv\Scripts\Activate.ps1

   # On macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install python-dotenv langchain-openai mcp-use
   ```

4. **Configure environment variables**

   Create a `.env` file in the project root:
   ```env
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   ```

## 🔧 Configuration

The project is configured for **Kubernetes cluster management** with maximum precision and reliability:

- **Model**: `anthropic/claude-3-5-sonnet` (Excellent for infrastructure tasks)
- **Base URL**: `https://openrouter.ai/api/v1`
- **Max Context**: 200,000 tokens (200K) - Handle large K8s manifests
- **Max Tokens**: 4,096 (Sufficient for detailed configurations)
- **Temperature**: 0.0 (**CRITICAL**: Eliminates randomness for consistent commands)
- **Top P**: 0.1 (**STRICT**: Uses only most probable tokens)
- **Max Retries**: 5 (Enhanced reliability for critical operations)
- **Request Timeout**: 120s (Allows time for complex cluster analysis)
- **Stream**: Disabled (Complete, validated responses)
- **MCP Server**: Fetch service for web search capabilities

### 🛡️ Production Safety Features

- **Deterministic Outputs**: Zero randomness ensures consistent K8s commands
- **Safety Stop Sequences**: Prevents dangerous command execution
- **Command Validation**: Built-in validation for Kubernetes operations
- **Enhanced Reliability**: 5 retries with extended timeouts
- **Large Context**: 200K tokens for analyzing complex cluster configurations

## 🏃‍♂️ Usage

Run the main script:

```bash
python main.py
```

The script will:
1. Load environment variables from `.env`
2. Initialize MCP client with fetch service
3. Create ChatOpenAI instance with OpenRouter configuration
4. Execute a search query: "Find the best restaurant in San Francisco USING GOOGLE SEARCH"

## 📁 Project Structure

```
use-k8s-mcp/
├── main.py              # Main application script
├── .env                 # Environment variables (API keys)
├── .gitignore          # Git ignore rules
├── pyproject.toml      # Project configuration
├── README.md           # This file
└── .venv/              # Virtual environment (ignored by git)
```

## 🔑 API Key Setup

1. Get your OpenRouter API key from [OpenRouter](https://openrouter.ai/)
2. Add it to your `.env` file:
   ```env
   OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
   ```
3. The `.env` file is automatically ignored by git for security

## 🐛 Troubleshooting

### Common Issues

1. **ModuleNotFoundError**: Make sure virtual environment is activated and dependencies are installed
2. **API Key Error**: Verify your OpenRouter API key is correctly set in `.env`
3. **Model Not Found**: Some models may not support tool use - stick with `openai/gpt-3.5-turbo`
4. **Connection Timeout**: Network issues with external services are normal and will be handled gracefully

### Kubernetes-Optimized Models

Models specifically configured for infrastructure and cluster management:

| Model                           | Context Length | K8s Strengths                                   | Precision | Cost   |
| ------------------------------- | -------------- | ----------------------------------------------- | --------- | ------ |
| `anthropic/claude-3-5-sonnet` ⭐ | 200K tokens    | YAML parsing, complex reasoning, error analysis | Highest   | Medium |
| `openai/gpt-4-turbo`            | 128K tokens    | Precise instructions, troubleshooting           | High      | High   |
| `qwen/qwen2.5-coder-32b`        | 128K tokens    | Code generation, debugging, cost-effective      | High      | Low    |
| `openai/gpt-4o`                 | 128K tokens    | Latest features, multi-modal analysis           | High      | High   |

**Current Configuration**: Using `anthropic/claude-3-5-sonnet` for maximum precision in Kubernetes operations.

### 🎯 Configuration Profiles

| Environment     | Model             | Temperature | Safety Level | Use Case                      |
| --------------- | ----------------- | ----------- | ------------ | ----------------------------- |
| **Production**  | Claude-3.5-Sonnet | 0.0         | Maximum      | Live cluster operations       |
| **Staging**     | Claude-3.5-Sonnet | 0.0         | High         | Pre-production testing        |
| **Development** | Qwen-Coder-32B    | 0.1         | Medium       | Development clusters          |
| **Analysis**    | Claude-3.5-Sonnet | 0.0         | High         | Log analysis, troubleshooting |

## 📝 Example Output

```
2025-06-18 01:06:23,320 - mcp_use - INFO - Starting MCP Agent...
Result: I found several highly-rated restaurants in San Francisco...
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source. Please check the license file for details.

## 🔗 Related Links

- [OpenRouter API Documentation](https://openrouter.ai/docs)
- [MCP (Model Context Protocol)](https://github.com/modelcontextprotocol)
- [LangChain OpenAI Integration](https://python.langchain.com/docs/integrations/chat/openai)

---

**Note**: Keep your API keys secure and never commit them to version control. The `.gitignore` file is configured to protect your `.env` file.