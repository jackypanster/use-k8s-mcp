"""
K8s MCP Agent LLM配置模块
专用于 Gemini 2.5 Flash 模型的环境配置管理
遵循十二要素应用方法论，所有配置通过环境变量管理
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# 加载环境变量
load_dotenv()


class GeminiMaxConfig:
    """
    Gemini 2.5 Flash 环境配置
    从环境变量读取所有配置，遵循十二要素应用方法论
    """

    def __init__(self):
        """初始化Gemini配置管理器，从环境变量读取所有配置"""
        # 验证必要的环境变量
        self._validate_required_env_vars()

        # 从环境变量加载配置
        self._load_config_from_env()

    def _validate_required_env_vars(self):
        """验证必需的环境变量，遵循fail-fast原则"""
        required_vars = [
            "OPENROUTER_API_KEY",
            "OPENROUTER_BASE_URL",
            "LLM_MODEL_NAME"
        ]

        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            raise ValueError(
                f"缺少必需的环境变量: {', '.join(missing_vars)}. "
                f"请检查 .env 文件配置。"
            )

    def _load_config_from_env(self):
        """从环境变量加载所有配置"""
        # LLM 提供商配置
        self.PROVIDER_NAME = os.getenv("LLM_PROVIDER_NAME", "OpenRouter")
        self.MODEL_NAME = os.getenv("LLM_MODEL_NAME")
        self.BASE_URL = os.getenv("OPENROUTER_BASE_URL")

        # 模型能力配置
        self.MAX_INPUT_CONTEXT = int(os.getenv("LLM_MAX_INPUT_CONTEXT", "1048576"))
        self.MAX_OUTPUT_TOKENS = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "32768"))
        self.MAX_TIMEOUT = int(os.getenv("LLM_REQUEST_TIMEOUT", "600"))

        # 模型行为配置
        self.TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.0"))
        self.TOP_P = float(os.getenv("LLM_TOP_P", "0.05"))
        self.MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "5"))
        self.SEED = int(os.getenv("LLM_SEED", "42"))

        # 安全配置
        safety_sequences = os.getenv("LLM_SAFETY_STOP_SEQUENCES",
                                   "```bash,```sh,```shell,rm -rf,kubectl delete,docker rmi,sudo rm")
        self.SAFETY_STOP_SEQUENCES = [seq.strip() for seq in safety_sequences.split(",")]

    def create_llm(self, **kwargs) -> ChatOpenAI:
        """
        创建Gemini 2.5 Flash LLM实例
        所有配置从环境变量读取，支持运行时覆盖

        Args:
            **kwargs: 可选的覆盖参数

        Returns:
            配置的Gemini 2.5 Flash ChatOpenAI实例
        """
        # 创建原始LLM
        original_llm = ChatOpenAI(
            model=kwargs.get("model", self.MODEL_NAME),
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url=kwargs.get("base_url", self.BASE_URL),

            # 模型能力配置 (从环境变量)
            max_tokens=kwargs.get("max_tokens", self.MAX_OUTPUT_TOKENS),
            temperature=kwargs.get("temperature", self.TEMPERATURE),
            top_p=kwargs.get("top_p", self.TOP_P),

            # 稳定性配置
            frequency_penalty=kwargs.get("frequency_penalty", 0.0),
            presence_penalty=kwargs.get("presence_penalty", 0.0),
            streaming=kwargs.get("streaming", False),
            seed=kwargs.get("seed", self.SEED),  # 明确指定seed参数，修复UserWarning

            # 可靠性配置 (从环境变量)
            max_retries=kwargs.get("max_retries", self.MAX_RETRIES),
            request_timeout=kwargs.get("request_timeout", self.MAX_TIMEOUT),

            # 安全配置 (从环境变量)
            stop=kwargs.get("stop", self.SAFETY_STOP_SEQUENCES),
        )
        
        # 包装为追踪版本
        return TrackedChatOpenAI(original_llm)
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息 (从环境变量配置)"""
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        masked_key = api_key[:10] + "..." if api_key else "未设置"

        return {
            "provider": self.PROVIDER_NAME,
            "model": self.MODEL_NAME,
            "api_key": masked_key,
            "base_url": self.BASE_URL,
            "input_context": f"{self.MAX_INPUT_CONTEXT:,} tokens",
            "output_tokens": f"{self.MAX_OUTPUT_TOKENS:,} tokens",
            "timeout": f"{self.MAX_TIMEOUT}s",
            "temperature": self.TEMPERATURE,
            "top_p": self.TOP_P,
            "max_retries": self.MAX_RETRIES,
            "features": ["工具调用", "大上下文", "推理模式", "数学/编程", "K8s运维"],
            "configuration": "环境变量配置 - 遵循十二要素应用方法论"
        }


# 全局配置实例 - 从环境变量初始化
gemini_config = GeminiMaxConfig()


def create_llm(**kwargs) -> ChatOpenAI:
    """
    🎯 主要入口点：创建Gemini 2.5 Flash LLM实例

    从环境变量读取所有配置，遵循十二要素应用方法论。
    支持不同部署环境的灵活配置。

    配置来源：
    - 模型名称：LLM_MODEL_NAME
    - 输入上下文：LLM_MAX_INPUT_CONTEXT
    - 输出能力：LLM_MAX_OUTPUT_TOKENS
    - 超时时间：LLM_REQUEST_TIMEOUT
    - 温度设置：LLM_TEMPERATURE

    Args:
        **kwargs: 可选的覆盖参数

    Returns:
        配置的Gemini 2.5 Flash ChatOpenAI实例

    Raises:
        ValueError: 当必需的环境变量未设置时

    Examples:
        >>> llm = create_llm()  # 从环境变量读取配置
        >>> llm = create_llm(max_tokens=16384)  # 覆盖输出限制
    """
    return gemini_config.create_llm(**kwargs)


def get_model_info() -> Dict[str, Any]:
    """
    获取当前模型配置信息

    Returns:
        包含模型详细信息的字典，所有值来自环境变量配置
    """
    return gemini_config.get_model_info()


def print_model_status():
    """打印当前模型状态"""
    info = get_model_info()
    print(f"🤖 当前LLM模型: {info['model']}")
    print(f"🔗 服务地址: {info['base_url']}")
    print(f"🔑 API密钥: {info['api_key']}")
    print(f"📏 输入上下文: {info['input_context']}")
    print(f"📤 输出能力: {info['output_tokens']}")
    print(f"⏱️  超时设置: {info['timeout']}")
    print(f"🛠️  功能特性: {', '.join(info['features'])}")
    print(f"⚙️  配置模式: {info['configuration']}")


# 在文件末尾添加LLM调用包装器
class TrackedChatOpenAI:
    """带追踪功能的ChatOpenAI包装器"""
    
    def __init__(self, llm):
        self.llm = llm
        
    def __getattr__(self, name):
        """代理所有属性到原始LLM"""
        return getattr(self.llm, name)
        
    async def ainvoke(self, input, **kwargs):
        """异步调用时增加日志追踪"""
        from .output_utils import chain_start, chain_end, llm_request, llm_response, data_flow
        
        # 提取prompt文本
        if hasattr(input, 'content'):
            prompt_text = input.content
        elif isinstance(input, str):
            prompt_text = input
        elif hasattr(input, 'messages') and input.messages:
            prompt_text = str(input.messages[-1].content) if input.messages else "未知消息格式"
        else:
            prompt_text = str(input)
            
        llm_call_id = chain_start("LLM", "生成响应", 
                                f"模型: {self.llm.model_name}, prompt长度: {len(prompt_text)} chars")
        
        # 记录LLM请求
        llm_request(self.llm.model_name, prompt_text, getattr(self.llm, 'max_tokens', None))
        
        # 数据流：Agent → LLM
        data_flow("AGENT", "LLM", "Prompt文本", len(prompt_text))
        
        try:
            # 调用原始LLM
            result = await self.llm.ainvoke(input, **kwargs)
            
            # 提取响应文本
            response_text = result.content if hasattr(result, 'content') else str(result)
            
            # 记录LLM响应
            llm_response(self.llm.model_name, response_text, 
                        getattr(result, 'usage', {}).get('total_tokens') if hasattr(result, 'usage') else None)
            
            # 数据流：LLM → Agent
            data_flow("LLM", "AGENT", "响应文本", len(response_text))
            
            chain_end(llm_call_id, f"成功生成响应，长度: {len(response_text)} chars")
            
            return result
            
        except Exception as e:
            chain_end(llm_call_id, "", f"LLM调用失败: {str(e)}")
            raise
    
    def invoke(self, input, **kwargs):
        """同步调用时增加日志追踪"""
        from .output_utils import chain_start, chain_end, llm_request, llm_response, data_flow
        
        # 提取prompt文本
        if hasattr(input, 'content'):
            prompt_text = input.content
        elif isinstance(input, str):
            prompt_text = input
        elif hasattr(input, 'messages') and input.messages:
            prompt_text = str(input.messages[-1].content) if input.messages else "未知消息格式"
        else:
            prompt_text = str(input)
            
        llm_call_id = chain_start("LLM", "生成响应", 
                                f"模型: {self.llm.model_name}, prompt长度: {len(prompt_text)} chars")
        
        # 记录LLM请求
        llm_request(self.llm.model_name, prompt_text, getattr(self.llm, 'max_tokens', None))
        
        # 数据流：Agent → LLM
        data_flow("AGENT", "LLM", "Prompt文本", len(prompt_text))
        
        try:
            # 调用原始LLM
            result = self.llm.invoke(input, **kwargs)
            
            # 提取响应文本
            response_text = result.content if hasattr(result, 'content') else str(result)
            
            # 记录LLM响应
            llm_response(self.llm.model_name, response_text,
                        getattr(result, 'usage', {}).get('total_tokens') if hasattr(result, 'usage') else None)
            
            # 数据流：LLM → Agent
            data_flow("LLM", "AGENT", "响应文本", len(response_text))
            
            chain_end(llm_call_id, f"成功生成响应，长度: {len(response_text)} chars")
            
            return result
            
        except Exception as e:
            chain_end(llm_call_id, "", f"LLM调用失败: {str(e)}")
            raise


