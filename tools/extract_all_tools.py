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
    print(f"🚀 begin extract_tool_list()")
    try:
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

        print(f"🛠️ 工具列表原始响应:\n{tools_result}")
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

        print(f"📊 解析出: {tool_names}")
        print(f"📊 解析出 {len(tool_names)} 个工具名称")

        print(f"✅ end extract_tool_list() - success (tools_count={len(tool_names)})")
        return tool_names
    except Exception as e:
        print(f"❌ end extract_tool_list() - failed: {e}")
        raise


def save_tool_list(tools, output_dir):
    """
    保存工具列表到JSON文件

    Args:
        tools: 工具名称列表
        output_dir: 输出目录路径
    """
    print(f"🚀 begin save_tool_list(tools_count={len(tools)}, output_dir={output_dir})")
    try:
        # 确保输出目录存在
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 构建工具列表数据结构
        tool_list_data = {
            "total_count": len(tools),
            "tools": tools
        }

        # 保存到JSON文件
        output_file = output_dir / "tool_list.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(tool_list_data, f, ensure_ascii=False, indent=2)

        print(f"✅ 工具列表已保存到: {output_file}")
        print(f"📊 包含 {len(tools)} 个工具名称")
        print(f"📁 文件大小: {output_file.stat().st_size} bytes")

        print(f"✅ end save_tool_list(tools_count={len(tools)}, output_dir={output_dir}) - success")
        return output_file
    except Exception as e:
        print(f"❌ end save_tool_list(tools_count={len(tools)}, output_dir={output_dir}) - failed: {e}")
        raise


def load_completed_list(output_dir):
    """
    读取已完成清单文件

    Args:
        output_dir: 输出目录路径

    Returns:
        list: 已完成的工具名称列表
    """
    print(f"🚀 begin load_completed_list(output_dir={output_dir})")
    try:
        output_dir = Path(output_dir)
        completed_file = output_dir / "completed_schemas.json"

        print(f"📋 读取已完成清单: {completed_file}")

        # 如果文件不存在，返回空列表
        if not completed_file.exists():
            print(f"   ℹ️  清单文件不存在，初始化为空列表")
            print(f"✅ end load_completed_list(output_dir={output_dir}) - success (count=0)")
            return []

        with open(completed_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        completed_tools = data.get('completed_tools', [])
        print(f"   ✅ 已读取 {len(completed_tools)} 个已完成工具")

        # 显示前5个已完成的工具
        if completed_tools:
            for i, tool in enumerate(completed_tools[:5]):
                print(f"      {i+1}. {tool}")
            if len(completed_tools) > 5:
                print(f"      ... 还有 {len(completed_tools) - 5} 个")

        print(f"✅ end load_completed_list(output_dir={output_dir}) - success (count={len(completed_tools)})")
        return completed_tools

    except json.JSONDecodeError as e:
        print(f"   ❌ 清单文件格式错误: {e}")
        print(f"❌ end load_completed_list(output_dir={output_dir}) - failed: {e}")
        raise Exception(f"已完成清单文件损坏: {completed_file}")
    except Exception as e:
        print(f"   ❌ 读取清单文件失败: {e}")
        print(f"❌ end load_completed_list(output_dir={output_dir}) - failed: {e}")
        raise


def add_to_completed_list(tool_name, output_dir):
    """
    向已完成清单中添加新完成的工具

    Args:
        tool_name: 工具名称
        output_dir: 输出目录路径
    """
    print(f"🚀 begin add_to_completed_list(tool_name={tool_name}, output_dir={output_dir})")
    try:
        output_dir = Path(output_dir)
        completed_file = output_dir / "completed_schemas.json"

        print(f"📝 更新已完成清单: {tool_name}")

        # 读取现有清单
        completed_tools = load_completed_list(output_dir) if completed_file.exists() else []

        # 避免重复添加
        if tool_name in completed_tools:
            print(f"   ℹ️  工具已在清单中: {tool_name}")
            print(f"✅ end add_to_completed_list(tool_name={tool_name}, output_dir={output_dir}) - success (already_exists)")
            return

        # 添加新工具
        completed_tools.append(tool_name)

        # 构建清单数据结构
        completed_data = {
            "completed_tools": completed_tools,
            "total_completed": len(completed_tools)
        }

        # 保存到文件
        with open(completed_file, 'w', encoding='utf-8') as f:
            json.dump(completed_data, f, ensure_ascii=False, indent=2)

        print(f"   ✅ 清单已更新: {len(completed_tools)} 个工具")
        print(f"   📁 文件大小: {completed_file.stat().st_size} bytes")

        print(f"✅ end add_to_completed_list(tool_name={tool_name}, output_dir={output_dir}) - success (added)")

    except Exception as e:
        print(f"   ❌ 更新清单失败: {e}")
        print(f"❌ end add_to_completed_list(tool_name={tool_name}, output_dir={output_dir}) - failed: {e}")
        raise Exception(f"无法更新已完成清单: {e}")


async def save_tool_schema(tool_name, real_schema_data, output_dir):
    """
    保存单个工具的schema到JSON文件

    Args:
        tool_name: 工具名称 (从内存中的工具列表传递)
        schema_data: schema原始数据 (从 get_tool_schema() 获取)
        output_dir: 输出目录路径

    Returns:
        Path: 保存的文件路径
    """
    print(f"🚀 begin save_tool_schema(tool_name={tool_name}, output_dir={output_dir})")
    try:
        # 确保输出目录存在
        output_dir = Path(output_dir)
        tools_dir = output_dir / "tools"
        tools_dir.mkdir(parents=True, exist_ok=True)

        # 构建schema数据结构，保持原始数据完整性
        schema_file_data = {
            "tool_name": tool_name,
            "schema": real_schema_data  # 保持原始schema数据不变
        }

        # 生成文件名：工具名称.json
        output_file = tools_dir / f"{tool_name}.json"

        # 保存到JSON文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(schema_file_data, f, ensure_ascii=False, indent=2)

        # 验证文件保存成功
        if output_file.exists():
            file_size = output_file.stat().st_size
            print(f"   ✅ 已保存: {output_file.name} ({file_size} bytes)")
        else:
            print(f"   ❌ 保存失败: {output_file}")
            raise Exception(f"工具schema保存失败: {tool_name}")

        print(f"✅ end save_tool_schema(tool_name={tool_name}, output_dir={output_dir}) - success")
        return output_file
    except Exception as e:
        print(f"❌ end save_tool_schema(tool_name={tool_name}, output_dir={output_dir}) - failed: {e}")
        raise


async def extract_single_tool_schema(tool_name, output_dir):
    """
    获取单个工具的schema并保存
    集成真实的MCP工具调用，不使用mock数据

    Args:
        tool_name: 工具名称
        output_dir: 输出目录路径

    Returns:
        bool: 是否成功获取并保存
    """
    print(f"🚀 begin extract_single_tool_schema(tool_name={tool_name}, output_dir={output_dir})")
    try:
        # 1. 调用 get_tool_schema() 获取真实schema数据
        print(f"   📡 调用MCP工具获取schema...")
        schema_data = await get_tool_schema(tool_name)

        if not schema_data:
            print(f"   ❌ 获取schema失败: 返回数据为空")
            return False

        print(f"   ✅ schema数据获取成功:{str(schema_data)}")
        print(f"   📊 数据大小: {len(str(schema_data))} chars")

        # 2. 调用 save_tool_schema() 保存到JSON文件
        print(f"   💾 保存schema到文件...")
        saved_file = await save_tool_schema(tool_name, schema_data, output_dir)

        # 3. 成功后自动更新已完成清单
        print(f"   📝 更新已完成清单...")
        add_to_completed_list(tool_name, output_dir)

        print(f"   ✅ 工具schema处理完成: {tool_name}")
        print(f"✅ end extract_single_tool_schema(tool_name={tool_name}, output_dir={output_dir}) - success")
        return True

    except Exception as e:
        print(f"   ❌ 工具schema获取失败: {tool_name}")
        print(f"   💥 错误详情: {e}")
        print(f"❌ end extract_single_tool_schema(tool_name={tool_name}, output_dir={output_dir}) - failed: {e}")
        return False


async def extract_all_schemas(tools, output_dir):
    """
    逐个串行获取所有工具的schema
    单线程执行，失败立即停止

    Args:
        tools: 工具名称列表
        output_dir: 输出目录路径
    """
    print(f"🚀 begin extract_all_schemas(tools_count={len(tools)}, output_dir={output_dir})")
    try:
        # 1. 读取已完成清单，跳过已完成的工具
        print(f"📋 检查已完成的工具...")
        completed_tools = load_completed_list(output_dir)

        # 获取待处理的工具列表
        pending_tools = [tool for tool in tools if tool not in completed_tools]

        print(f"📊 进度状态:")
        print(f"   总工具数: {len(tools)}")
        print(f"   已完成: {len(completed_tools)}")
        print(f"   待处理: {len(pending_tools)}")
        print(f"   完成率: {len(completed_tools)/len(tools)*100:.1f}%")

        if not pending_tools:
            print(f"🎉 所有工具schema已获取完成！")
            print(f"✅ end extract_all_schemas(tools_count={len(tools)}, output_dir={output_dir}) - success (all_completed)")
            return

        # 2. 单线程串行处理待处理工具
        print(f"\n🔄 开始批量获取schema...")
        print(f"📝 处理顺序: {pending_tools[:5]}{'...' if len(pending_tools) > 5 else ''}")

        success_count = 0
        failed_tool = None

        for i, tool_name in enumerate(pending_tools, 1):
            print(f"\n🔧 [{i}/{len(pending_tools)}] 处理工具: {tool_name}")
            print(f"   进度: {(len(completed_tools) + i - 1)/len(tools)*100:.1f}% → {(len(completed_tools) + i)/len(tools)*100:.1f}%")

            # 调用单个工具schema获取函数
            success = await extract_single_tool_schema(tool_name, output_dir)

            if success:
                success_count += 1
                print(f"   ✅ 成功: {tool_name} ({success_count}/{len(pending_tools)})")
            else:
                # 3. 失败时立即停止（fail-fast）
                failed_tool = tool_name
                print(f"   ❌ 失败: {tool_name}")
                print(f"💥 批量获取中断，fail-fast原则")
                break

        # 最终统计
        final_completed = load_completed_list(output_dir)
        final_completion_rate = len(final_completed)/len(tools)*100

        print(f"\n📊 批量获取结果:")
        print(f"   本次处理: {success_count}/{len(pending_tools)} 成功")
        print(f"   总体进度: {len(final_completed)}/{len(tools)} ({final_completion_rate:.1f}%)")

        if failed_tool:
            print(f"❌ end extract_all_schemas(tools_count={len(tools)}, output_dir={output_dir}) - failed: {failed_tool}")
            raise Exception(f"工具schema获取失败: {failed_tool}")
        else:
            print(f"✅ end extract_all_schemas(tools_count={len(tools)}, output_dir={output_dir}) - success (processed={success_count})")

    except Exception as e:
        print(f"❌ end extract_all_schemas(tools_count={len(tools)}, output_dir={output_dir}) - failed: {e}")
        raise


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

        # 批量获取所有工具的schema
        print("\n📋 开始批量获取所有工具schema...")
        await extract_all_schemas(tools, output_dir)

        print(f"✅ 所有工具schema获取完成")

        return tools
    except Exception as e:
        print(f"❌ 工具列表提取失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
