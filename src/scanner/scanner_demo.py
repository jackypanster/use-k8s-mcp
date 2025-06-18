"""
集群扫描器演示
展示如何使用集群扫描器进行K8s资源扫描
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from mcp_use import MCPClient

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

# 使用绝对导入
from src.scanner.cluster_scanner import ClusterScanner
from src.scanner.resource_parser import ResourceParser
from src.scanner.scan_coordinator import ScanCoordinator
from src.cache import CacheManager
from src.mcp_tools import MCPToolLoader
from src.llm_config import create_llm


async def demo_cluster_scanning():
    """演示集群扫描功能"""
    print("=" * 60)
    print("🔍 K8s集群扫描器演示")
    print("=" * 60)
    
    # 加载环境变量
    load_dotenv()
    
    try:
        # 1. 初始化组件
        print("🔧 初始化组件...")
        
        # 创建MCP客户端
        config = {
            "mcpServers": {
                os.getenv("MCP_SERVER_NAME", "k8s"): {
                    "type": os.getenv("MCP_SERVER_TYPE", "stdio"),
                    "url": os.getenv("MCP_SERVER_URL", "")
                }
            }
        }
        mcp_client = MCPClient.from_dict(config)
        print("✅ MCP客户端创建成功")
        
        # 创建缓存管理器
        cache_manager = CacheManager()
        print("✅ 缓存管理器创建成功")
        
        # 创建工具加载器
        tool_loader = MCPToolLoader(cache_manager)
        print("✅ 工具加载器创建成功")
        
        # 创建扫描组件
        cluster_scanner = ClusterScanner(
            mcp_client=mcp_client,
            tool_loader=tool_loader,
            timeout=60,
            max_retries=2
        )
        
        resource_parser = ResourceParser()
        
        scan_coordinator = ScanCoordinator(
            cluster_scanner=cluster_scanner,
            resource_parser=resource_parser,
            cache_manager=cache_manager,
            static_ttl=1800,  # 30分钟
            dynamic_ttl=300   # 5分钟
        )
        print("✅ 扫描组件创建成功")
        
        # 2. 预加载MCP工具
        print("\n🛠️ 预加载MCP工具...")
        try:
            tools = await tool_loader.load_tools()
            print(f"✅ 成功加载 {len(tools)} 个MCP工具")
            
            # 显示可用工具
            for tool in tools[:5]:  # 只显示前5个
                print(f"   - {tool.name}: {tool.description}")
            if len(tools) > 5:
                print(f"   ... 还有 {len(tools) - 5} 个工具")
                
        except Exception as e:
            print(f"⚠️ 工具预加载失败，使用模拟数据: {e}")
        
        # 3. 执行集群扫描演示
        print("\n🔍 执行集群扫描演示...")
        cluster_name = "demo-cluster"
        
        try:
            # 执行完整集群扫描
            scan_result = await scan_coordinator.scan_cluster_full(
                cluster_name=cluster_name,
                include_static=True,
                include_dynamic=True
            )
            
            print("✅ 集群扫描完成!")
            print(f"📊 扫描统计:")
            print(f"   - 集群名称: {scan_result['cluster_name']}")
            print(f"   - 扫描时长: {scan_result['scan_duration']:.2f}秒")
            
            # 显示静态资源统计
            static_stats = scan_result.get('static_resources', {})
            if static_stats.get('success'):
                static_data = static_stats.get('data', {})
                print(f"   - 静态资源: {sum(static_data.values())} 个")
                for resource_type, count in static_data.items():
                    print(f"     * {resource_type}: {count}")
            
            # 显示动态资源统计
            dynamic_stats = scan_result.get('dynamic_resources', {})
            if dynamic_stats.get('success'):
                dynamic_data = dynamic_stats.get('data', {})
                print(f"   - 动态资源: {sum(dynamic_data.values())} 个")
                for resource_type, count in dynamic_data.items():
                    print(f"     * {resource_type}: {count}")
            
            # 显示总体统计
            overall_stats = scan_result.get('statistics', {})
            print(f"   - 总资源数: {overall_stats.get('total_resources', 0)}")
            
        except Exception as e:
            print(f"❌ 集群扫描失败: {e}")
            print("💡 这可能是因为MCP服务器连接问题或工具不可用")
        
        # 4. 显示组件统计信息
        print("\n📈 组件统计信息:")
        
        # 扫描器统计
        scanner_stats = cluster_scanner.get_scan_stats()
        print(f"🔍 扫描器统计:")
        print(f"   - 扫描次数: {scanner_stats['scan_count']}")
        print(f"   - 错误次数: {scanner_stats['error_count']}")
        print(f"   - 成功率: {scanner_stats['success_rate']:.1f}%")
        print(f"   - 平均扫描时间: {scanner_stats['avg_scan_time']:.2f}秒")
        
        # 解析器统计
        parser_stats = resource_parser.get_parsing_stats()
        print(f"📝 解析器统计:")
        print(f"   - 解析次数: {parser_stats['parsed_count']}")
        print(f"   - 错误次数: {parser_stats['error_count']}")
        print(f"   - 成功率: {parser_stats['success_rate']:.1f}%")
        
        # 协调器统计
        coordinator_stats = scan_coordinator.get_coordinator_stats()
        print(f"🎯 协调器统计:")
        print(f"   - 扫描会话: {coordinator_stats['scan_sessions']}")
        print(f"   - 成功扫描: {coordinator_stats['successful_scans']}")
        print(f"   - 失败扫描: {coordinator_stats['failed_scans']}")
        print(f"   - 成功率: {coordinator_stats['success_rate']:.1f}%")
        
        # 5. 缓存数据查询演示
        print("\n💾 缓存数据查询演示:")
        try:
            # 查询缓存的集群信息
            clusters = cache_manager.list_records('clusters')
            print(f"📋 缓存的集群: {len(clusters)} 个")
            
            # 查询缓存的命名空间
            namespaces = cache_manager.list_records('namespaces')
            print(f"📋 缓存的命名空间: {len(namespaces)} 个")
            
            # 查询缓存的Pod
            pods = cache_manager.list_records('pods')
            print(f"📋 缓存的Pod: {len(pods)} 个")
            
            # 查询缓存元数据
            metadata_records = cache_manager.list_records('cache_metadata')
            print(f"📋 缓存元数据: {len(metadata_records)} 条")
            
        except Exception as e:
            print(f"⚠️ 缓存查询失败: {e}")
        
        print("\n" + "=" * 60)
        print("✅ 集群扫描器演示完成!")
        print("💡 扫描器已成功实现静态和动态资源的扫描、解析和缓存功能")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


def demo_resource_parsing():
    """演示资源解析功能"""
    print("\n" + "=" * 60)
    print("📝 资源解析器演示")
    print("=" * 60)
    
    parser = ResourceParser()
    
    # 演示集群信息解析
    print("🏢 集群信息解析:")
    cluster_data = {
        'name': 'production-cluster',
        'version': 'v1.23.15',
        'server': 'https://prod-k8s.example.com:6443',
        'nodeCount': 5
    }
    
    cluster_info = parser.parse_cluster_info(cluster_data, 'production-cluster')
    print(f"   ✅ 集群: {cluster_info.name}")
    print(f"   📊 版本: {cluster_info.version}")
    print(f"   🖥️  节点数: {cluster_info.node_count}")
    
    # 演示命名空间解析
    print("\n📁 命名空间解析:")
    namespace_data = [
        {
            'metadata': {'name': 'production', 'labels': {'env': 'prod'}},
            'status': {'phase': 'Active'}
        },
        {
            'metadata': {'name': 'staging', 'labels': {'env': 'staging'}},
            'status': {'phase': 'Active'}
        }
    ]
    
    namespaces = parser.parse_namespaces(namespace_data, 'production-cluster')
    for ns in namespaces:
        print(f"   ✅ 命名空间: {ns.name} (状态: {ns.status})")
    
    # 演示Pod解析
    print("\n🐳 Pod解析:")
    pod_data = [
        {
            'metadata': {
                'name': 'web-app-123',
                'namespace': 'production',
                'labels': {'app': 'web', 'version': 'v2.1'}
            },
            'status': {
                'phase': 'Running',
                'containerStatuses': [
                    {'name': 'web-container', 'ready': True, 'restartCount': 0}
                ]
            },
            'spec': {
                'nodeName': 'worker-node-1',
                'containers': [
                    {'name': 'web-container', 'image': 'nginx:1.21'}
                ]
            }
        }
    ]
    
    pods = parser.parse_pods(pod_data, 'production-cluster')
    for pod in pods:
        print(f"   ✅ Pod: {pod.name} (命名空间: {pod.namespace}, 状态: {pod.phase})")
        print(f"      🖥️  节点: {pod.node_name}")
        print(f"      📦 容器: {len(pod.containers)} 个")
    
    # 显示解析统计
    stats = parser.get_parsing_stats()
    print(f"\n📊 解析统计:")
    print(f"   - 解析总数: {stats['parsed_count']}")
    print(f"   - 成功率: {stats['success_rate']:.1f}%")
    
    print("✅ 资源解析演示完成!")


if __name__ == '__main__':
    print("🚀 启动集群扫描器演示程序")
    
    # 运行资源解析演示
    demo_resource_parsing()
    
    # 运行集群扫描演示
    asyncio.run(demo_cluster_scanning())
