"""
K8s MCP 工具发现脚本
复用已验证的 MCP 连接配置，发现并展示所有可用的 K8s 工具
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from mcp_use import MCPAgent, MCPClient

# 添加项目根目录到 Python 路径（仅在直接运行时）
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

from src.llm_config import create_llm


async def discover_k8s_tools():
    """
    发现并打印所有 K8s MCP 工具的完整信息
    复用 src/main.py 中已验证的配置格式
    """
    # 加载环境变量
    load_dotenv()
    
    # 复用已验证的 MCP 配置（无 type 字段）
    server_name = os.getenv("MCP_SERVER_NAME")
    server_url = os.getenv("MCP_SERVER_URL")
    
    mcp_config = {
        "mcpServers": {
            server_name: {
                "url": server_url
            }
        }
    }
    
    # 创建已验证的组件
    client = MCPClient.from_dict(mcp_config)
    llm = create_llm()
    agent = MCPAgent(llm=llm, client=client, max_steps=80)
    
    print("🔍 K8s MCP 工具发现")
    print("=" * 60)
    print(f"📡 MCP 服务器: {server_url}")
    print(f"🏷️  服务器名称: {server_name}")
    print("=" * 60)
    
    # 发现工具列表
    print("\n📋 获取工具列表...")
    tools_result = await agent.run(
        """列出所有可用的工具名称，只返回工具名称列表，不要添加任何解释。
        严格要求：
1. 绝对不要编造、修改、删减或压缩任何返回数据
2. 严格遵循工具返回的原始结果，保持数据完整性
3. 只允许对数据进行结构化输出和美化展示
4. 保留所有字段、值和数据结构，不得省略任何信息
5. 如果工具调用失败，必须明确报告失败原因，不得提供任何模拟数据

你的职责仅限于：数据格式化和可读性优化，严禁任何形式的数据创造或修改。""",
        max_steps=5
    )
    print(f"🛠️  工具列表响应:\n{tools_result}")

    # 解析工具列表
    print("\n📝 解析工具列表...")
    tool_names = []

    # 尝试从返回结果中提取工具名称
    lines = tools_result.split('\n')
    for line in lines:
        line = line.strip()
        if line and not line.startswith('Thought:') and not line.startswith('Final Answer:'):
            # 移除可能的序号和特殊字符
            clean_line = line.replace('*', '').replace('-', '').replace('•', '').strip()
            if clean_line and len(clean_line) > 2:  # 过滤掉太短的行
                tool_names.append(clean_line)

    print(f"📊 解析出 {len(tool_names)} 个工具名称")
    for i, tool in enumerate(tool_names[:5]):  # 显示前5个
        print(f"   {i+1}. {tool}")
    if len(tool_names) > 5:
        print(f"   ... 还有 {len(tool_names) - 5} 个工具")

    # 获取前几个工具的详细 schema
    print("\n📖 获取工具详细 schema...")
    for i, tool_name in enumerate(tool_names[:3]):  # 只获取前3个工具的schema
        print(f"\n🔧 [{i+1}/3] 获取 {tool_name} 的 schema:")
        try:
            # 复用现有的 agent 而不是重新创建
            schema_result = await agent.run(
                f"获取工具 {tool_name} 的完整 schema 信息，包括输入参数、类型、是否必需等详细信息",
                max_steps=10
            )
            print(f"📋 {tool_name} Schema:")
            print(schema_result)
        except Exception as e:
            print(f"   ❌ 获取 {tool_name} schema 失败: {e}")

    print("\n" + "=" * 60)
    print("✅ 工具发现完成")
    print(f"💡 发现 {len(tool_names)} 个工具，可使用 get_tool_schema('工具名') 获取更多详情")


async def get_tool_schema(tool_name: str):
    """
    获取指定工具的 schema 信息
    
    Args:
        tool_name: 工具名称
    """
    load_dotenv()
    
    server_name = os.getenv("MCP_SERVER_NAME")
    server_url = os.getenv("MCP_SERVER_URL")
    
    mcp_config = {
        "mcpServers": {
            server_name: {
                "url": server_url
            }
        }
    }
    
    client = MCPClient.from_dict(mcp_config)
    llm = create_llm()
    agent = MCPAgent(llm=llm, client=client, max_steps=100)

    print(f"🔍 获取工具 {tool_name} 的 schema")
    print("-" * 40)

    result = await agent.run(
        f"获取工具 {tool_name} 的完整 schema 信息，包括输入参数、类型、是否必需等详细信息。要求：1. 绝对不编造、修改、删减或压缩任何返回数据；2. 不改变返回数据，用JSON格式结构化返回",
        max_steps=100
    )
    
    print(f"📋 {tool_name} Schema:")
    print(result)
    return result


def print_usage():
    """打印使用说明"""
    print("""
🚀 K8s MCP 工具发现脚本使用说明

独立运行：
  uv run python src/tool_discovery.py

导入使用：
  from src.tool_discovery import discover_k8s_tools, get_tool_schema
  
  # 发现所有工具
  await discover_k8s_tools()
  
  # 获取特定工具 schema
  await get_tool_schema("LIST_CLUSTERS")

环境要求：
  - 已配置 .env 文件中的 MCP 服务器信息
  - MCP_SERVER_NAME, MCP_SERVER_URL 环境变量
  - OPENROUTER_API_KEY, LLM_MODEL_NAME 等 LLM 配置
""")


async def get_all_tools_with_schemas():
    """获取所有工具及其 schema"""
    load_dotenv()

    server_name = os.getenv("MCP_SERVER_NAME")
    server_url = os.getenv("MCP_SERVER_URL")

    mcp_config = {
        "mcpServers": {
            server_name: {
                "url": server_url
            }
        }
    }

    client = MCPClient.from_dict(mcp_config)
    llm = create_llm()
    agent = MCPAgent(llm=llm, client=client, max_steps=5)

    print("🔍 获取所有 K8s MCP 工具及其 Schema")
    print("=" * 60)

    # 获取工具列表
    result = await agent.run(
        "列出所有可用的工具名称，只返回工具名称列表",
        max_steps=3
    )

    # 解析工具名称（从逗号分隔的列表中提取）
    tool_names = []
    if "Final Answer:" in result:
        tool_list_part = result.split("Final Answer:")[-1].strip()
        tool_names = [tool.strip() for tool in tool_list_part.split(",") if tool.strip()]

    print(f"� 发现 {len(tool_names)} 个工具")

    # 获取前5个工具的详细 schema
    for i, tool_name in enumerate(tool_names[:5]):
        print(f"\n🔧 [{i+1}/5] {tool_name}")
        print("-" * 40)

        schema_result = await agent.run(
            f"获取工具 {tool_name} 的完整 schema 信息，包括描述、输入参数、参数类型、是否必需等",
            max_steps=3
        )
        print(schema_result)

    if len(tool_names) > 5:
        print(f"\n💡 还有 {len(tool_names) - 5} 个工具未显示")
        print("可以使用 get_tool_schema('工具名') 单独查看")

    print("\n" + "=" * 60)
    print("✅ 完成")

    return tool_names


if __name__ == "__main__":
    print_usage()
    print("\n🔄 开始完整工具发现...")
    asyncio.run(discover_k8s_tools())
