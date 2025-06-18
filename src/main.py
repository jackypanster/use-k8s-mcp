import asyncio
import os
from dotenv import load_dotenv
from mcp_use import MCPAgent, MCPClient
from .llm_config import create_llm, print_model_status


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

    # 打印当前LLM提供商状态
    print("=" * 60)
    print("🚀 K8s MCP Agent 启动 (环境配置模式)")
    print("=" * 60)
    print_model_status()
    print("=" * 60)

    # 验证并获取MCP配置
    try:
        print("🔧 正在验证环境配置...")
        config = get_mcp_config()
        server_name = os.getenv("MCP_SERVER_NAME")
        server_url = os.getenv("MCP_SERVER_URL")
        print(f"✅ 环境配置验证成功")
        print(f"   MCP服务器: {server_name}")
        print(f"   服务器地址: {server_url}")
    except ValueError as e:
        print(f"❌ 致命错误: 环境配置验证失败")
        print(f"   错误详情: {e}")
        print("")
        print("🔧 请检查 .env 文件中的MCP配置:")
        print("   - MCP_SERVER_URL")
        print("   - MCP_SERVER_TYPE")
        print("   - MCP_SERVER_NAME")
        print("")
        print("🚫 程序终止 - 配置不完整")
        raise SystemExit(1) from e

    # 创建Gemini 2.5 Flash LLM实例
    try:
        print("🔧 正在初始化 Gemini 2.5 Flash LLM...")
        llm = create_llm()  # 从环境变量读取配置
        print(f"✅ LLM初始化完成")
        print(f"   模型: {llm.model_name}")
        print(f"   温度: {llm.temperature}")
        print(f"   最大Token: {llm.max_tokens}")
        print(f"   服务地址: {llm.openai_api_base}")
    except ValueError as e:
        print(f"❌ 致命错误: LLM配置验证失败")
        print(f"   错误详情: {e}")
        print("")
        print("🔧 请检查 .env 文件中的LLM配置")
        print("🚫 程序终止 - LLM配置不完整")
        raise SystemExit(1) from e

    print("=" * 60)

    # 连接K8s MCP服务器 - 这是系统运行的必要条件
    print("🔗 连接K8s MCP服务器...")

    try:
        # Create MCPClient from environment-based config
        client = MCPClient.from_dict(config)
        print("✅ MCP服务器连接成功")
    except Exception as e:
        server_url = os.getenv("MCP_SERVER_URL")
        print(f"❌ 致命错误: K8s MCP服务器连接失败")
        print(f"   错误详情: {e}")
        print(f"   服务器地址: {server_url}")
        print("")
        print("💡 K8s MCP Agent 的核心价值在于通过MCP工具管理真实的K8s集群")
        print("   没有MCP工具调用能力的Agent对K8s运维毫无意义")
        print("")
        print("🔧 请确保:")
        print("   1. MCP服务器正常运行")
        print("   2. 网络连接正常")
        print("   3. .env 文件中的 MCP_SERVER_URL 配置正确")
        print("")
        print("🚫 程序终止 - 无法在没有真实集群数据的情况下提供K8s管理服务")
        raise SystemExit(1) from e

    try:
        # Create agent with the client
        print("🤖 创建K8s MCP Agent...")
        agent = MCPAgent(llm=llm, client=client, max_steps=10)
        print("✅ K8s MCP Agent 创建成功")
    except Exception as e:
        print(f"❌ 致命错误: 无法创建K8s MCP Agent")
        print(f"   错误详情: {e}")
        print("")
        print("💡 Agent创建失败意味着无法进行K8s集群管理")
        print("� 程序终止 - 系统核心功能不可用")
        raise SystemExit(1) from e

    # 执行K8s集群信息查询 - 验证系统功能
    print("🔍 执行K8s集群信息查询...")
    try:
        result = await agent.run(
            "get the k8s cluster info",
            max_steps=5,
        )
        print("✅ K8s集群查询成功!")
        print(f"📋 真实集群数据: {result}")

    except Exception as e:
        print(f"❌ 致命错误: K8s集群查询失败")
        print(f"   错误详情: {e}")
        print("")
        print("💡 无法获取真实的K8s集群数据")
        print("   这违反了系统的数据真实性铁律")
        print("🚫 程序终止 - 无法提供基于真实数据的K8s管理服务")
        raise SystemExit(1) from e

if __name__ == "__main__":
    # Run the appropriate example
    asyncio.run(main())
