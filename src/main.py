import asyncio
import os
from dotenv import load_dotenv
from mcp_use import MCPAgent, MCPClient
from .llm_config import create_llm, print_model_status
from .output_utils import success, fatal, StandardErrors, standard_fatal_error


def validate_mcp_config():
    """验证MCP服务器配置，遵循fail-fast原则"""
    required_vars = [
        "MCP_SERVER_URL",
        "MCP_SERVER_TYPE",
        "MCP_SERVER_NAME"
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        raise ValueError(
            f"缺少必需的MCP配置环境变量: {', '.join(missing_vars)}. "
            f"请检查 .env 文件配置。"
        )


def get_mcp_config():
    """从环境变量获取MCP服务器配置"""
    validate_mcp_config()

    server_name = os.getenv("MCP_SERVER_NAME")
    server_type = os.getenv("MCP_SERVER_TYPE")
    server_url = os.getenv("MCP_SERVER_URL")

    return {
        "mcpServers": {
            server_name: {
                "type": server_type,
                "url": server_url
            }
        }
    }


async def main():
    """运行K8s MCP Agent，所有配置从环境变量读取"""
    # Load environment variables
    load_dotenv()

    # 简化启动输出
    success("K8s MCP Agent 启动中")
    print_model_status()

    # 验证并获取MCP配置
    try:
        config = get_mcp_config()
        server_name = os.getenv("MCP_SERVER_NAME")
        success("配置验证完成", server_name)
    except ValueError as e:
        standard_fatal_error(StandardErrors.CONFIG_VALIDATION, str(e))
        raise SystemExit(1) from e

    # 创建Gemini 2.5 Flash LLM实例
    try:
        llm = create_llm()  # 从环境变量读取配置
        success("LLM初始化完成", llm.model_name)
    except ValueError as e:
        standard_fatal_error(StandardErrors.LLM_INITIALIZATION, str(e))
        raise SystemExit(1) from e

    # 连接K8s MCP服务器 - 这是系统运行的必要条件
    try:
        # Create MCPClient from environment-based config
        client = MCPClient.from_dict(config)
        success("MCP服务器连接成功")
    except Exception as e:
        standard_fatal_error(StandardErrors.MCP_CONNECTION, str(e))
        raise SystemExit(1) from e

    try:
        # Create agent with the client
        agent = MCPAgent(llm=llm, client=client, max_steps=30)
        success("K8s MCP Agent 创建成功")
    except Exception as e:
        fatal("Agent创建", str(e), "系统核心功能不可用")
        raise SystemExit(1) from e

    # 执行K8s集群信息查询 - 验证系统功能
    try:
        from .output_utils import request_log, response_log, step_log
        
        instruction = "get the k8s cluster info"
        request_log("MAIN_AGENT", "获取集群信息", f"指令: {instruction}, max_steps: 30")
        
        result = await agent.run(
            instruction,
            max_steps=30,
        )
        
        response_log("MAIN_AGENT", "获取集群信息", str(result))
        success("K8s集群查询完成")
        success("集群数据获取", f"{result}")

    except Exception as e:
        fatal("K8s集群查询", str(e), "无法获取真实K8s集群数据，违反数据真实性铁律")
        raise SystemExit(1) from e

if __name__ == "__main__":
    # Run the appropriate example
    asyncio.run(main())
