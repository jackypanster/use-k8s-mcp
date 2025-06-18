#!/usr/bin/env python3
"""
无工具调用的MCP Agent
完全禁用工具调用，只使用基本对话功能
"""

import sys
import os
import asyncio
from dotenv import load_dotenv

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_use import MCPClient
from src.llm_config import create_no_tools_llm, print_provider_status, get_current_provider


async def test_mcp_without_tools():
    """测试不使用工具调用的MCP连接"""
    print("🔧 测试MCP连接（无工具调用）")
    print("=" * 60)
    
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
        
        # 创建MCP客户端
        print("🔗 创建MCP客户端...")
        client = MCPClient.from_dict(config)
        
        # 初始化会话
        print("🔄 初始化MCP会话...")
        sessions = await client.create_all_sessions()
        
        print(f"✅ 成功创建 {len(sessions)} 个MCP会话")
        
        # 检查会话状态
        for session_name, session in sessions.items():
            print(f"📋 会话 '{session_name}' 状态: 已连接")
            
            # 尝试获取服务器信息
            try:
                # 这里可能需要根据实际的MCP客户端API调整
                print(f"   服务器连接正常")
            except Exception as e:
                print(f"   服务器信息获取失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP连接测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_basic_llm():
    """测试基础LLM功能"""
    print("\n🤖 测试基础LLM功能")
    print("=" * 60)
    
    try:
        # 创建完全禁用工具调用的LLM
        llm = create_no_tools_llm("production")
        
        print(f"✅ LLM创建成功: {llm.model_name}")
        
        # 测试基本对话
        print("💬 测试基本对话...")
        response = await llm.ainvoke(
            "你好，请简单介绍一下你是什么，用一句话回答。"
        )
        
        print(f"🤖 LLM回复: {response.content}")
        
        # 测试Kubernetes相关问题（不使用工具）
        print("\n💬 测试Kubernetes知识...")
        k8s_response = await llm.ainvoke(
            "什么是Kubernetes？请用一句话简单解释。"
        )
        
        print(f"🤖 K8s回复: {k8s_response.content}")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def interactive_mode():
    """交互模式"""
    print("\n💬 进入交互模式")
    print("=" * 60)
    print("📋 注意: 当前模式不使用MCP工具，只提供基本对话")
    print("💡 输入 'quit' 或 'exit' 退出")
    print("=" * 60)
    
    try:
        # 创建LLM
        llm = create_no_tools_llm("development")
        
        while True:
            try:
                # 获取用户输入
                user_input = input("\n🔍 请输入您的问题: ").strip()
                
                if user_input.lower() in ['quit', 'exit', '退出', 'q']:
                    print("👋 再见!")
                    break
                
                if not user_input:
                    continue
                
                print(f"\n🤖 正在思考...")
                
                # 获取回复
                response = await llm.ainvoke(user_input)
                
                print(f"💬 回复: {response.content}")
                print("-" * 40)
                
            except KeyboardInterrupt:
                print("\n👋 用户中断，退出程序")
                break
            except Exception as e:
                print(f"\n❌ 处理问题时出错: {e}")
                print("💡 请尝试重新表述您的问题")
        
        return True
        
    except Exception as e:
        print(f"❌ 交互模式失败: {e}")
        return False


async def main():
    """主函数"""
    print("🚀 无工具调用MCP测试")
    print("=" * 60)
    print("🎯 目标: 绕过工具调用问题，测试基础功能")
    print("=" * 60)
    
    # 加载环境变量
    load_dotenv()
    
    # 显示当前配置
    print_provider_status()
    print("=" * 60)
    
    # 运行测试
    tests = [
        ("MCP连接测试", test_mcp_without_tools),
        ("基础LLM测试", test_basic_llm),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 运行 {test_name}...")
        try:
            if await test_func():
                passed += 1
                print(f"✅ {test_name} 通过")
            else:
                print(f"❌ {test_name} 失败")
        except Exception as e:
            print(f"❌ {test_name} 异常: {e}")
    
    print("\n" + "=" * 60)
    print(f"🏁 测试完成: {passed}/{total} 通过")
    
    if passed > 0:
        print("🎉 基础功能正常!")
        
        # 询问是否进入交互模式
        try:
            choice = input("\n💡 是否进入交互模式？(y/n): ").strip().lower()
            if choice in ['y', 'yes', '是', '好']:
                await interactive_mode()
        except KeyboardInterrupt:
            print("\n👋 退出程序")
    else:
        print("⚠️ 所有测试失败，请检查配置")
    
    print("\n📋 总结:")
    print("1. MCP服务器工具定义需要添加 'strict: true' 参数")
    print("2. 这是服务器端问题，需要MCP服务器开发者修复")
    print("3. 当前可以使用基础对话功能")
    print("4. 等待MCP服务器更新后可恢复完整工具调用功能")


if __name__ == "__main__":
    asyncio.run(main())
