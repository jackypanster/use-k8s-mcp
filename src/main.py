import asyncio
import os
from dotenv import load_dotenv
from mcp_use import MCPAgent, MCPClient

from src.llm_config import create_llm, print_model_status


async def main():
    """运行K8s MCP Agent，所有配置从环境变量读取"""
    # Load environment variables
    load_dotenv()

    # 简化启动输出
    print("✅ K8s MCP Agent 启动中")
    print_model_status()

    # 验证MCP配置
    server_name = os.getenv("MCP_SERVER_NAME")
    server_type = os.getenv("MCP_SERVER_TYPE")
    server_url = os.getenv("MCP_SERVER_URL")

    if not all([server_name, server_type, server_url]):
        missing = [var for var, val in [
            ("MCP_SERVER_NAME", server_name),
            ("MCP_SERVER_TYPE", server_type),
            ("MCP_SERVER_URL", server_url)
        ] if not val]
        print(f"❌ 缺少必需的MCP环境变量: {', '.join(missing)}")
        raise SystemExit(1)

    print(f"✅ 配置验证完成 - {server_name}")
    print(f"🔗 MCP服务器: {server_url} ({server_type})")

    # 创建Gemini 2.5 Flash LLM实例
    
    llm = create_llm()  # 从环境变量读取配置
    print(f"✅ LLM初始化完成 - {llm.model_name}")


    # 连接K8s MCP服务器 - 这是系统运行的必要条件
    
    # 直接构建MCP配置
    mcp_config = {
        "mcpServers": {
            server_name: {
                "type": server_type,
                "url": server_url
            }
        }
    }
        
    client = MCPClient.from_dict(mcp_config)
    print("✅ MCP服务器连接成功")


    
    # Create agent with the client
    agent = MCPAgent(llm=llm, client=client, max_steps=30)
    print("✅ K8s MCP Agent 创建成功")

    instruction = "调用k8s mcp工具，查询k8s集群状态"

    print(f"📤 发送指令到Agent (长度: {len(instruction)} chars)")

    result = await agent.run(
        instruction,
        max_steps=5,  # 减少步数，避免复杂操作
    )

    print(f"📥 Agent返回结果 (长度: {len(str(result))} chars)")
    print(f"📋 查询结果: {result}")



if __name__ == "__main__":
    # Run the appropriate example
    asyncio.run(main())
