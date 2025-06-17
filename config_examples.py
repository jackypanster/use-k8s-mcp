"""
ChatOpenAI 配置示例 - 充分利用上下文 token
"""

import os
from langchain_openai import ChatOpenAI

# 示例 1: Qwen3-32B 最大上下文配置
def create_qwen_max_context():
    """
    Qwen3-32B 支持 128K 上下文长度
    适合处理长文档、复杂对话历史
    """
    return ChatOpenAI(
        model="qwen/qwen3-32b",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        max_tokens=4096,  # 输出token限制
        temperature=0.7,  # 平衡创造性和准确性
        max_retries=3,
        request_timeout=120,  # 长上下文需要更长处理时间
        model_kwargs={
            "max_context_length": 131072,  # 128K 上下文 (131072 tokens)
            "top_p": 0.9,
            "frequency_penalty": 0.1,
            "presence_penalty": 0.1,
            "stream": True,  # 流式输出，更好的用户体验
        }
    )

# 示例 2: Claude-3.5-Sonnet 超长上下文配置
def create_claude_max_context():
    """
    Claude-3.5-Sonnet 支持 200K 上下文长度
    适合分析超长文档、代码库
    """
    return ChatOpenAI(
        model="anthropic/claude-3-5-sonnet",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        max_tokens=8192,  # Claude 支持更长输出
        temperature=0.3,  # 较低温度保证准确性
        max_retries=3,
        request_timeout=180,  # 超长上下文需要更多时间
        model_kwargs={
            "max_context_length": 200000,  # 200K 上下文
            "top_p": 0.95,
            "stream": True,
        }
    )

# 示例 3: GPT-4 Turbo 长上下文配置
def create_gpt4_turbo_max_context():
    """
    GPT-4 Turbo 支持 128K 上下文长度
    平衡性能和成本
    """
    return ChatOpenAI(
        model="openai/gpt-4-turbo",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        max_tokens=4096,
        temperature=0.5,
        max_retries=3,
        request_timeout=120,
        model_kwargs={
            "max_context_length": 128000,  # 128K 上下文
            "top_p": 0.9,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "stream": True,
        }
    )

# 示例 4: 成本优化的长上下文配置
def create_cost_optimized_long_context():
    """
    使用较便宜的模型但仍保持较长上下文
    适合预算有限的场景
    """
    return ChatOpenAI(
        model="openai/gpt-3.5-turbo-16k",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        max_tokens=2048,
        temperature=0.7,
        max_retries=3,
        request_timeout=60,
        model_kwargs={
            "max_context_length": 16384,  # 16K 上下文
            "top_p": 0.9,
            "frequency_penalty": 0.1,
            "presence_penalty": 0.1,
            "stream": True,
        }
    )

# 配置选择指南
CONTEXT_LENGTH_GUIDE = {
    "qwen/qwen3-32b": 131072,          # 128K - 性价比高
    "anthropic/claude-3-5-sonnet": 200000,  # 200K - 最长上下文
    "openai/gpt-4-turbo": 128000,      # 128K - 平衡性能
    "openai/gpt-4o": 128000,           # 128K - 最新模型
    "openai/gpt-3.5-turbo-16k": 16384, # 16K - 成本优化
}

# 使用建议
USAGE_RECOMMENDATIONS = {
    "长文档分析": "anthropic/claude-3-5-sonnet",
    "代码库理解": "qwen/qwen3-32b",
    "复杂对话": "openai/gpt-4-turbo",
    "成本敏感": "openai/gpt-3.5-turbo-16k",
    "实时应用": "qwen/qwen3-32b",
}

def get_optimal_config(use_case: str):
    """
    根据使用场景返回最优配置
    """
    model_map = {
        "长文档分析": create_claude_max_context,
        "代码库理解": create_qwen_max_context,
        "复杂对话": create_gpt4_turbo_max_context,
        "成本敏感": create_cost_optimized_long_context,
        "实时应用": create_qwen_max_context,
    }
    
    config_func = model_map.get(use_case, create_qwen_max_context)
    return config_func()

# 上下文管理技巧
CONTEXT_MANAGEMENT_TIPS = """
1. 合理分配 token:
   - 输入上下文: 80-90% 的总 token
   - 输出预留: 10-20% 的总 token

2. 优化输入内容:
   - 移除不必要的空白和格式
   - 压缩重复信息
   - 使用摘要替代完整内容

3. 分段处理:
   - 对于超长内容，考虑分段处理
   - 使用滑动窗口技术
   - 保留关键上下文信息

4. 监控 token 使用:
   - 使用 tiktoken 库计算 token 数量
   - 实时监控上下文长度
   - 动态调整输入内容
"""

if __name__ == "__main__":
    # 示例使用
    llm = get_optimal_config("代码库理解")
    print(f"选择的模型配置: {llm.model}")
    print(f"最大上下文长度: {llm.model_kwargs.get('max_context_length', 'N/A')}")
