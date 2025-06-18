#!/usr/bin/env python3
"""
MCP Agent 工作版本
使用保守模式配置，确保稳定运行
"""

import sys
import os
import asyncio
from dotenv import load_dotenv

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_use import MCPAgent, MCPClient
from src.llm_config import create_llm, print_provider_status, get_current_provider


async def main():
    """主函数 - 稳定的MCP Agent版本"""
    # Load environment variables
    load_dotenv()

    print("🚀 MCP Agent 启动（稳定版本）")
    print("=" * 60)
    print("📝 注意: 使用保守模式配置，确保稳定运行")
    print("=" * 60)
    
    # 显示当前配置状态
    print_provider_status()
    print("=" * 60)

    # 根据配置创建LLM实例
    print(f"🔧 正在初始化 {get_current_provider().upper()} LLM...")
    
    # 使用保守配置，禁用工具调用以避免参数验证问题
    llm = create_llm(
        model_type="production",
        temperature=0.0,
        max_tokens=4096,
        model_kwargs={
            "tool_choice": "none",  # 禁用工具调用
            "parallel_tool_calls": False,
        }
    )
    
    print(f"✅ LLM初始化完成")
    print(f"   模型: {llm.model_name}")
    print(f"   温度: {llm.temperature}")
    print(f"   最大Token: {llm.max_tokens}")
    print(f"   服务地址: {llm.openai_api_base}")
    print("=" * 60)

    # 尝试连接MCP服务器
    try:
        # 使用环境变量配置MCP服务器
        config = {
            "mcpServers": {
                "k8s": {
                    "type": "sse",
                    "url": os.getenv("MCP_SERVER_URL", "http://localhost:31455/sse")
                }
            }
        }

        # Create MCPClient from config file
        print("🔗 连接MCP服务器...")
        client = MCPClient.from_dict(config)

        # Create agent with the client
        print("🤖 创建MCP Agent...")
        agent = MCPAgent(llm=llm, client=client, max_steps=10)

        # 交互式查询循环
        print("✅ MCP Agent 准备就绪!")
        print("💡 您可以询问关于Kubernetes集群的任何问题")
        print("💡 输入 'quit' 或 'exit' 退出")
        print("=" * 60)
        
        while True:
            try:
                # 获取用户输入
                user_input = input("\n🔍 请输入您的问题: ").strip()
                
                if user_input.lower() in ['quit', 'exit', '退出', 'q']:
                    print("👋 再见!")
                    break
                
                if not user_input:
                    continue
                
                print(f"\n🤖 正在处理: {user_input}")
                print("-" * 40)
                
                # 运行查询
                result = await agent.run(
                    user_input,
                    max_steps=5,
                )
                
                print(f"\n📋 回答:")
                print(result)
                print("-" * 40)
                
            except KeyboardInterrupt:
                print("\n👋 用户中断，退出程序")
                break
            except Exception as e:
                print(f"\n❌ 处理查询时出错: {e}")
                print("💡 请尝试重新表述您的问题")
        
    except Exception as e:
        print(f"❌ MCP连接失败: {e}")
        print("💡 提示: 请检查MCP服务器是否正常运行")
        print("🔧 建议使用独立模式: uv run python standalone.py")
        
        # 运行简单的LLM测试
        print("\n🧪 运行简单LLM测试...")
        try:
            response = await llm.ainvoke("你好，请简单介绍一下你自己")
            print(f"🤖 LLM回复: {response.content[:200]}...")
            print("✅ LLM功能正常!")
        except Exception as llm_error:
            print(f"❌ LLM测试失败: {llm_error}")


if __name__ == "__main__":
    asyncio.run(main())
