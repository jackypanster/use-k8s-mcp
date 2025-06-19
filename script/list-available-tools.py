#!/usr/bin/env python3
"""
列出MCP服务器实际可用的工具
"""

import asyncio
import os
import sys
from pathlib import Path

# 设置Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# 导入组件
from mcp_use import MCPClient
from src.scanner.cluster_scanner import ClusterScanner
from src.cache import CacheManager
from src.mcp_tools import MCPToolLoader


async def list_available_tools():
    """列出MCP服务器实际可用的工具"""
    print("=" * 60)
    print("🛠️ 列出MCP服务器可用工具")
    print("=" * 60)
    
    try:
        # 创建组件
        config = {
            "mcpServers": {
                os.getenv("MCP_SERVER_NAME", "k8s"): {
                    "type": os.getenv("MCP_SERVER_TYPE", "sse"),
                    "url": os.getenv("MCP_SERVER_URL", "")
                }
            }
        }
        mcp_client = MCPClient.from_dict(config)
        cache_manager = CacheManager()
        tool_loader = MCPToolLoader(cache_manager)
        
        cluster_scanner = ClusterScanner(
            mcp_client=mcp_client,
            tool_loader=tool_loader,
            timeout=60,
            max_retries=2
        )
        
        print("✅ 组件创建成功")
        
        # 方法1：通过Agent询问可用工具
        print("\n🔍 方法1：询问Agent可用工具...")
        try:
            result = await cluster_scanner.agent.run(
                "请列出所有可用的K8s相关工具和命令", 
                max_steps=30
            )
            print("✅ Agent响应:")
            print(f"   {result}")
        except Exception as e:
            print(f"❌ Agent询问失败: {e}")
        
        # 方法2：通过工具加载器获取工具
        print("\n🔍 方法2：通过工具加载器获取...")
        try:
            tools = await tool_loader.load_tools()
            print(f"✅ 工具加载器找到 {len(tools)} 个工具:")
            for tool in tools:
                print(f"   - {tool.name}: {tool.description}")
        except Exception as e:
            print(f"❌ 工具加载器失败: {e}")
        
        # 方法3：测试常见的工具名称变体
        print("\n🔍 方法3：测试常见工具名称...")
        possible_tools = [
            'GET_CLUSTER_INFO',
            'LIST_NAMESPACES', 
            'LIST_NODES',
            'LIST_CORE_RESOURCES',
            'LIST_PODS',
            'LIST_SERVICES',
            'get_cluster_info',
            'list_namespaces',
            'list_nodes',
            'list_pods',
            'list_services',
            'k8s_cluster_info',
            'k8s_namespaces',
            'k8s_nodes',
            'k8s_pods',
            'k8s_services'
        ]
        
        working_tools = []
        
        for tool_name in possible_tools:
            try:
                result = await cluster_scanner.agent.run(
                    f"使用 {tool_name} 工具获取信息", 
                    max_steps=30
                )
                
                # 检查是否是"找不到工具"的错误
                if "无法找到" not in result and "找不到" not in result and "不存在" not in result:
                    working_tools.append((tool_name, result[:100] + "..."))
                    print(f"✅ {tool_name}: 工作正常")
                else:
                    print(f"❌ {tool_name}: 工具不存在")
                    
            except Exception as e:
                print(f"❌ {tool_name}: 调用失败 - {e}")
        
        print(f"\n🎯 找到 {len(working_tools)} 个可用工具:")
        for tool_name, response in working_tools:
            print(f"   ✅ {tool_name}")
            print(f"      响应: {response}")
        
        # 方法4：直接询问正确的工具名称
        print("\n🔍 方法4：询问正确的工具名称...")
        try:
            result = await cluster_scanner.agent.run(
                "我想获取K8s集群信息、命名空间列表、节点列表和Pod列表，请告诉我应该使用什么工具名称和参数", 
                max_steps=30
            )
            print("✅ Agent建议:")
            print(f"   {result}")
        except Exception as e:
            print(f"❌ 询问失败: {e}")
        
        print("\n" + "=" * 60)
        print("🎯 总结:")
        print("   1. 找到实际可用的工具名称")
        print("   2. 了解正确的参数格式")
        print("   3. 更新ClusterScanner中的工具映射")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 程序执行失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    print("🚀 启动工具列表查询程序")
    asyncio.run(list_available_tools())


if __name__ == '__main__':
    main()
