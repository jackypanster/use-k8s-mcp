#!/usr/bin/env python3
"""
K8s MCP 工具Schema提取脚本
基于 src/tool_discovery.py，提取所有55个K8s MCP工具的完整信息并保存为JSON文件

核心原则：
- 绝对不要编造、修改、删减或压缩任何返回数据
- 严格遵循工具返回的原始结果，保持数据完整性
- 单线程串行执行，fail-fast原则
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
print(f"🔧 项目根目录: {project_root}")
print(f"🔧 Python路径: {sys.path[0]}")

# 导入已验证的工具发现模块
from src.tool_discovery import get_tool_schema
from src.llm_config import create_llm
from dotenv import load_dotenv
from mcp_use import MCPAgent, MCPClient


async def extract_tool_list():
    """
    提取所有K8s MCP工具列表
    复用 src/tool_discovery.py 中已验证的配置
    """
    print("📋 开始获取工具列表...")

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
    agent = MCPAgent(llm=llm, client=client, max_steps=10)

    print(f"🔗 MCP服务器: {server_url}")

    # 获取工具列表 - 使用与 tool_discovery.py 相同的严格指令
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

    print(f"🛠️ 工具列表原始响应长度: {len(tools_result)} chars")

    # 解析工具列表 - 复用 tool_discovery.py 的解析逻辑
    tool_names = []
    lines = tools_result.split('\n')
    for line in lines:
        line = line.strip()
        if line and not line.startswith('Thought:') and not line.startswith('Final Answer:'):
            # 移除可能的序号和特殊字符
            clean_line = line.replace('*', '').replace('-', '').replace('•', '').strip()
            if clean_line and len(clean_line) > 2:  # 过滤掉太短的行
                tool_names.append(clean_line)

    print(f"📊 解析出 {len(tool_names)} 个工具名称")

    # 显示前5个工具作为验证
    for i, tool in enumerate(tool_names[:5]):
        print(f"   {i+1}. {tool}")
    if len(tool_names) > 5:
        print(f"   ... 还有 {len(tool_names) - 5} 个工具")

    return tool_names


def save_tool_list(tools, output_dir):
    """
    保存工具列表到JSON文件

    Args:
        tools: 工具名称列表
        output_dir: 输出目录路径
    """
    print("💾 开始保存工具列表...")

    # 确保输出目录存在
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 构建工具列表数据结构
    tool_list_data = {
        "total_count": len(tools),
        "extraction_timestamp": "2025-06-20",
        "data_integrity_principle": "绝对不编造、修改、删减或压缩任何返回数据",
        "tools": tools
    }

    # 保存到JSON文件
    output_file = output_dir / "tool_list.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(tool_list_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 工具列表已保存到: {output_file}")
    print(f"📊 包含 {len(tools)} 个工具名称")
    print(f"📁 文件大小: {output_file.stat().st_size} bytes")

    return output_file


def verify_tool_list_completeness(tools, output_file):
    """
    验证工具列表完整性

    Args:
        tools: 工具名称列表
        output_file: 保存的JSON文件路径

    Returns:
        bool: 验证是否通过
    """
    print("\n🔍 Task 2.3: 验证工具列表完整性...")

    verification_passed = True

    # 验收标准1: 工具数量 = 55
    print(f"📊 验证工具数量...")
    expected_count = 55
    actual_count = len(tools)
    if actual_count == expected_count:
        print(f"   ✅ 工具数量正确: {actual_count}/{expected_count}")
    else:
        print(f"   ❌ 工具数量不符: {actual_count}/{expected_count}")
        verification_passed = False

    # 验收标准2: 包含已知核心工具
    print(f"🔍 验证核心工具...")
    core_tools = ["LIST_CLUSTERS", "GET_CLUSTER_INFO", "LIST_NAMESPACES", "LIST_NODES"]
    found_core_tools = []
    missing_core_tools = []

    for core_tool in core_tools:
        if core_tool in tools:
            found_core_tools.append(core_tool)
            print(f"   ✅ {core_tool}")
        else:
            missing_core_tools.append(core_tool)
            print(f"   ❌ {core_tool} - 缺失")
            verification_passed = False

    print(f"📈 核心工具覆盖率: {len(found_core_tools)}/{len(core_tools)} ({len(found_core_tools)/len(core_tools)*100:.1f}%)")

    # 验收标准3: 工具名称无重复
    print(f"🔄 验证重复工具...")
    unique_tools = set(tools)
    duplicate_count = len(tools) - len(unique_tools)
    if duplicate_count == 0:
        print(f"   ✅ 工具列表无重复")
    else:
        print(f"   ❌ 发现重复工具: {duplicate_count} 个")
        verification_passed = False

        # 找出重复的工具
        seen = set()
        duplicates = set()
        for tool in tools:
            if tool in seen:
                duplicates.add(tool)
            else:
                seen.add(tool)
        print(f"   重复工具: {list(duplicates)}")

    # 验证JSON文件
    print(f"📁 验证JSON文件...")
    if output_file.exists():
        file_size = output_file.stat().st_size
        print(f"   ✅ 文件存在: {output_file}")
        print(f"   ✅ 文件大小: {file_size} bytes")

        # 验证JSON格式
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"   ✅ JSON格式正确")

            # 验证JSON内容
            if 'tools' in data and len(data['tools']) == len(tools):
                print(f"   ✅ JSON内容完整")
            else:
                print(f"   ❌ JSON内容不完整")
                verification_passed = False

        except json.JSONDecodeError as e:
            print(f"   ❌ JSON格式错误: {e}")
            verification_passed = False
    else:
        print(f"   ❌ 文件不存在: {output_file}")
        verification_passed = False

    # 总结验证结果
    print(f"\n📋 Task 2.3 验证结果:")
    if verification_passed:
        print(f"   ✅ 所有验收标准通过")
        print(f"   ✅ 工具列表完整性验证成功")
    else:
        print(f"   ❌ 部分验收标准未通过")
        print(f"   ❌ 工具列表完整性验证失败")

    return verification_passed


async def save_tool_schema(tool_name, schema_data, output_dir):
    """
    保存单个工具的schema到JSON文件

    Args:
        tool_name: 工具名称
        schema_data: schema原始数据
        output_dir: 输出目录路径
    """
    # TODO: 实现单个工具schema保存逻辑
    pass


async def extract_all_schemas(tools, output_dir):
    """
    逐个串行获取所有工具的schema
    单线程执行，失败立即停止

    Args:
        tools: 工具名称列表
        output_dir: 输出目录路径
    """
    # TODO: 实现批量schema提取逻辑
    pass


async def main():
    """主函数"""
    print("🚀 K8s MCP 工具Schema提取脚本")
    print("📋 准备提取55个工具的完整信息...")

    # 设置输出目录
    output_dir = Path(__file__).parent / "schemas"

    print(f"📁 输出目录: {output_dir}")
    print("⚠️  数据完整性原则: 绝对不编造、修改、删减或压缩任何返回数据")

    # 测试工具列表提取功能
    try:
        tools = await extract_tool_list()
        print(f"✅ 工具列表提取成功，共 {len(tools)} 个工具")

        # 验证是否包含已知的核心工具
        core_tools = ["LIST_CLUSTERS", "GET_CLUSTER_INFO", "LIST_NAMESPACES", "LIST_NODES"]
        found_core_tools = [tool for tool in core_tools if tool in tools]
        print(f"🔍 核心工具验证: 找到 {len(found_core_tools)}/{len(core_tools)} 个核心工具")
        for tool in found_core_tools:
            print(f"   ✅ {tool}")

        # 检查是否有重复工具
        unique_tools = set(tools)
        if len(unique_tools) == len(tools):
            print("✅ 工具列表无重复")
        else:
            print(f"⚠️ 发现重复工具: {len(tools) - len(unique_tools)} 个")

        # Task 2.2: 保存工具列表到JSON文件
        print("\n📋 Task 2.2: 保存工具列表...")
        saved_file = save_tool_list(tools, output_dir)
        print(f"✅ Task 2.2 完成: 工具列表已保存到 {saved_file}")

        # Task 2.3: 验证工具列表完整性
        verification_passed = verify_tool_list_completeness(tools, saved_file)
        if verification_passed:
            print(f"✅ Task 2.3 完成: 工具列表完整性验证通过")
        else:
            print(f"❌ Task 2.3 失败: 工具列表完整性验证未通过")
            raise Exception("工具列表完整性验证失败，停止执行")

        return tools
    except Exception as e:
        print(f"❌ 工具列表提取失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
